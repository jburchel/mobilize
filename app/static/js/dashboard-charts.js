// Dashboard Charts - Real-time data implementation

// Make global stats available to the charts
window.gStats = window.gStats || {};

// Expose stats from Flask to JavaScript
document.addEventListener('DOMContentLoaded', function() {
    // Try to get stats from data attributes if available
    const statsContainer = document.getElementById('stats-container');
    if (statsContainer) {
        window.gStats = {
            people_count: statsContainer.getAttribute('data-people-count') || 0,
            church_count: statsContainer.getAttribute('data-church-count') || 0,
            pending_tasks: statsContainer.getAttribute('data-pending-tasks') || 0,
            recent_communications: statsContainer.getAttribute('data-recent-communications') || 0
        };
        console.log('Loaded stats from data attributes:', window.gStats);
    } else {
        console.log('No stats container found, using default values');
    }
    
    // Initialize button event handlers
    initRefreshButtons();
    
    // Load chart data
    fetchPipelineData('people');
    fetchPipelineData('church');
    
    console.log('DOM loaded, initializing dashboard charts');
    // Initialize charts if containers exist
    if (document.getElementById('people-chart-container') || document.getElementById('church-chart-container')) {
        initializeDashboardCharts();
        updateBadgeTotals(); // Update badge totals on page load
    } else {
        console.log('No chart containers found, skipping initialization');
    }
});

// Global chart objects
let peopleChart = null;
let churchChart = null;

// Initialize the dashboard charts
function initializeDashboardCharts() {
  console.log('Initializing dashboard charts');
  
  // Show loading indicators
  document.querySelectorAll('.chart-loading-indicator').forEach(el => {
    el.style.display = 'flex';
  });
  
  // Hide any previous errors
  document.querySelectorAll('.alert-danger').forEach(el => {
    el.style.display = 'none';
  });
  
  // Fetch people pipeline data if container exists
  if (document.getElementById('people-chart-container')) {
    fetchPipelineData('people');
  }
  
  // Fetch church pipeline data if container exists
  if (document.getElementById('church-chart-container')) {
    fetchPipelineData('church');
  }
  
  // Set up event listeners for chart type buttons
  setupChartTypeButtons();
  
  // Set up event listeners for refresh buttons
  setupRefreshButtons();
}

// Fetch pipeline data from the API
function fetchPipelineData(pipelineType) {
  const endpoint = `/api/simple-chart-data/${pipelineType === 'people' ? 'person' : pipelineType}`;
  console.log(`Fetching ${pipelineType} pipeline data from ${endpoint}`);
  
  // Add timestamp to prevent caching
  const timestamp = new Date().getTime();
  const url = `${endpoint}?_=${timestamp}`;
  
  fetch(url, {
    method: 'GET',
    headers: {
      'Cache-Control': 'no-cache',
      'Pragma': 'no-cache'
    },
    credentials: 'same-origin'
  })
    .then(response => {
      console.log(`${pipelineType} pipeline response:`, response.status);
      if (!response.ok) {
        throw new Error(`HTTP error! Status: ${response.status}`);
      }
      return response.json();
    })
    .then(data => {
      console.log(`${pipelineType} pipeline data:`, data);
      createChart(pipelineType, data);
      
      // Update badge totals when data is received
      if (data.total_contacts) {
        updateBadgeTotal(pipelineType, data.total_contacts);
      }
      
      // Update the View Pipeline button with the correct pipeline ID
      if (data.pipeline_id) {
        const viewButton = document.getElementById(`${pipelineType}-view-pipeline`);
        if (viewButton) {
          // Use direct route instead of pipeline ID
          viewButton.href = `/pipeline/${pipelineType === 'people' ? 'person' : pipelineType}-pipeline`;
          console.log(`Updated ${pipelineType} pipeline button to use direct route`);
        }
      }
    })
    .catch(error => {
      console.error(`Error fetching ${pipelineType} pipeline data:`, error);
      showError(pipelineType, error.message);
    });
}

// Create chart based on pipeline type and data
function createChart(pipelineType, data) {
  // Check if data is valid
  if (!data || !data.stages || data.stages.length === 0) {
    console.error(`Invalid or empty data received for ${pipelineType} pipeline`);
    showError(pipelineType, 'No data available for chart');
    hideLoading(pipelineType);
    return;
  }
  
  const containerId = `${pipelineType}-chart-container`;
  const container = document.getElementById(containerId);
  if (!container) {
    console.error(`Container ${containerId} not found`);
    hideLoading(pipelineType);
    return;
  }
  
  // Always use pie chart for simplicity
  const chartType = 'pie';
  console.log(`Using ${chartType} chart for ${pipelineType}`);
  
  // Clear the container
  container.innerHTML = '';
  
  // Create canvas for Chart.js
  const canvas = document.createElement('canvas');
  container.appendChild(canvas);
  
  // Prepare chart data
  const labels = [];
  const values = [];
  const colors = [];
  
  // Only include stages with data
  data.stages.forEach(stage => {
    labels.push(stage.name);
    values.push(stage.contact_count);
    colors.push(stage.color || getDefaultColor(stage.name));
  });
  
  // Create the chart
  const chartConfig = {
    type: chartType,
    data: {
      labels: labels,
      datasets: [{
        data: values,
        backgroundColor: colors,
        borderWidth: 1
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          position: 'bottom',
          labels: {
            font: {
              size: 12
            }
          }
        },
        tooltip: {
          callbacks: {
            label: function(context) {
              const label = context.label || '';
              const value = context.raw || 0;
              const total = values.reduce((sum, val) => sum + val, 0);
              const percentage = total > 0 ? Math.round((value / total) * 100) : 0;
              return `${label}: ${value} (${percentage}%)`;
            }
          }
        }
      }
    }
  };
  
  // Store chart instance in global variable
  if (pipelineType === 'people') {
    if (peopleChart) {
      peopleChart.destroy();
    }
    peopleChart = new Chart(canvas, chartConfig);
  } else if (pipelineType === 'church') {
    if (churchChart) {
      churchChart.destroy();
    }
    churchChart = new Chart(canvas, chartConfig);
  }
  
  console.log(`${pipelineType} chart created successfully`);
  hideLoading(pipelineType);
}

// Show error message
function showError(pipelineType, message) {
  const errorElement = document.getElementById(`${pipelineType}-chart-error`);
  if (errorElement) {
    errorElement.textContent = `Error loading chart: ${message}`;
    errorElement.style.display = 'block';
  }
  hideLoading(pipelineType);
}

// Hide loading indicator
function hideLoading(pipelineType) {
  const loadingElement = document.getElementById(`${pipelineType}-chart-loading`);
  if (loadingElement) {
    loadingElement.style.display = 'none';
  }
}

// Set up chart type buttons - simplified to always use pie charts
function setupChartTypeButtons() {
  // Remove chart type buttons since we're only using pie charts
  document.querySelectorAll('.chart-type-btn').forEach(button => {
    if (button && button.parentNode) {
      button.parentNode.removeChild(button);
    }
  });
  
  // Also remove any chart type button containers
  document.querySelectorAll('.chart-type-container').forEach(container => {
    if (container && container.parentNode) {
      container.parentNode.removeChild(container);
    }
  });
  
  console.log('Chart type buttons removed, using pie charts only');
}

// Set up refresh buttons
function setupRefreshButtons() {
  document.querySelectorAll('.refresh-chart-btn').forEach(button => {
    button.addEventListener('click', function() {
      const pipelineType = this.dataset.chartType;
      fetchPipelineData(pipelineType);
    });
  });
}

// Get default color for a stage
function getDefaultColor(stageName) {
  const name = (stageName || '').toLowerCase();
  
  if (name.includes('promotion')) return '#3498db'; // Blue
  if (name.includes('information')) return '#2ecc71'; // Green
  if (name.includes('invitation')) return '#f1c40f'; // Yellow
  if (name.includes('confirmation')) return '#e67e22'; // Orange
  if (name.includes('enr') || name.includes('en42')) return '#9b59b6'; // Purple
  if (name.includes('automation')) return '#1abc9c'; // Teal
  
  return '#95a5a6'; // Gray default
}

// Update badge totals from the global stats object
function updateBadgeTotals() {
  console.log('Updating badge totals from global stats');
  
  // Try to get stats from the global context
  if (window.gStats) {
    console.log('Found global stats:', window.gStats);
    if (window.gStats.people_count) {
      updateBadgeTotal('people', window.gStats.people_count);
    }
    if (window.gStats.church_count) {
      updateBadgeTotal('church', window.gStats.church_count);
    }
  } else {
    // Fallback to getting stats from the DOM if available
    console.log('No global stats found, checking DOM for stats');
    const peopleValue = document.querySelector('.kpi-card-title:contains("Total People")');
    if (peopleValue) {
      const count = peopleValue.closest('.kpi-card').querySelector('.kpi-card-value').textContent.trim();
      updateBadgeTotal('people', count);
    }
    
    const churchValue = document.querySelector('.kpi-card-title:contains("Total Churches")');
    if (churchValue) {
      const count = churchValue.closest('.kpi-card').querySelector('.kpi-card-value').textContent.trim();
      updateBadgeTotal('church', count);
    }
  }
}

// Update a specific badge total
function updateBadgeTotal(type, count) {
  console.log(`Updating ${type} badge total to ${count}`);
  const badgeId = `${type === 'people' ? 'people' : 'church'}-badge-total`;
  const badge = document.getElementById(badgeId);
  
  if (!badge) {
    // Create badge if it doesn't exist
    const cardFooter = document.querySelector(`#${type}-chart-container`).closest('.card').querySelector('.card-footer');
    if (cardFooter) {
      const badgeContainer = cardFooter.querySelector('.d-flex');
      if (badgeContainer) {
        const badgeSpan = document.createElement('span');
        badgeSpan.id = badgeId;
        badgeSpan.className = 'badge bg-secondary badge-total';
        badgeSpan.textContent = `Total: ${count} ${type === 'people' ? 'People' : 'Churches'}`;
        
        // Insert at beginning of container
        if (badgeContainer.firstChild) {
          badgeContainer.insertBefore(badgeSpan, badgeContainer.firstChild);
        } else {
          badgeContainer.appendChild(badgeSpan);
        }
        console.log(`Created new badge for ${type}`);
      }
    }
  } else {
    // Update existing badge
    badge.textContent = `Total: ${count} ${type === 'people' ? 'People' : 'Churches'}`;
    console.log(`Updated existing badge for ${type}`);
  }
}

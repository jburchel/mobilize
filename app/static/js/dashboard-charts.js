// Dashboard Charts - Real-time data implementation

// Wait for DOM content to be loaded
document.addEventListener('DOMContentLoaded', function() {
  console.log('DOM loaded, initializing dashboard charts');
  // Initialize charts if containers exist
  if (document.getElementById('people-chart-container') || document.getElementById('church-chart-container')) {
    initializeDashboardCharts();
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
  
  fetch(endpoint)
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
      
      // Update the View Pipeline button with the correct pipeline ID
      if (data.pipeline_id) {
        const viewButton = document.getElementById(`${pipelineType}-view-pipeline`);
        if (viewButton) {
          viewButton.href = `/pipeline/${data.pipeline_id}`;
          console.log(`Updated ${pipelineType} pipeline button to link to ID: ${data.pipeline_id}`);
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
  
  // Get chart type (pie or doughnut)
  const chartTypeBtn = document.querySelector(`[data-pipeline="${pipelineType}"].chart-type-btn.active`);
  const chartType = chartTypeBtn && chartTypeBtn.dataset.chartType === 'doughnut' ? 'doughnut' : 'pie';
  
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

// Set up chart type buttons
function setupChartTypeButtons() {
  document.querySelectorAll('.chart-type-btn').forEach(button => {
    button.addEventListener('click', function() {
      const pipelineType = this.dataset.pipeline;
      const chartType = this.dataset.chartType;
      
      // Update active state
      document.querySelectorAll(`[data-pipeline="${pipelineType}"].chart-type-btn`).forEach(btn => {
        btn.classList.remove('active');
      });
      this.classList.add('active');
      
      // Save preference to localStorage
      localStorage.setItem(`${pipelineType}-chart-style`, chartType);
      
      // Refresh the chart
      fetchPipelineData(pipelineType);
    });
  });
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

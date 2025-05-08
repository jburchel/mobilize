// Simple Charts for Mobilize Dashboard

// Global chart instances
window.peopleChart = null;
window.churchChart = null;

// Colors for chart segments
const defaultColors = [
  '#4e73df', // Primary blue
  '#1cc88a', // Success green
  '#36b9cc', // Info teal
  '#f6c23e', // Warning yellow
  '#e74a3b', // Danger red
  '#6f42c1', // Purple
  '#fd7e14', // Orange
  '#20c9a6', // Teal
  '#5a5c69', // Gray
  '#858796'  // Light gray
];

// Fetch pipeline data from the API
async function fetchPipelineData(pipelineType) {
  try {
    // Show loading indicator
    document.getElementById(`${pipelineType}-chart-loading`).style.display = 'flex';
    document.getElementById(`${pipelineType}-chart-error`).style.display = 'none';
    document.getElementById(`${pipelineType}-chart-empty`).style.display = 'none';
    
    // Fetch data from the API with credentials
    const response = await fetch(`/api/simple-chart-data/${pipelineType}`, {
      credentials: 'same-origin' // Include cookies for authentication
    });
    
    if (!response.ok) {
      throw new Error(`API returned ${response.status}: ${response.statusText}`);
    }
    
    const data = await response.json();
    
    // Hide loading indicator
    document.getElementById(`${pipelineType}-chart-loading`).style.display = 'none';
    
    // Check if we have data
    if (!data.stages || data.stages.length === 0) {
      document.getElementById(`${pipelineType}-chart-empty`).style.display = 'block';
      return null;
    }
    
    // Update total count
    document.getElementById(`${pipelineType}-total-count`).textContent = 
      `Total: ${data.total_contacts} ${pipelineType === 'person' ? 'People' : 'Churches'}`;
    
    return data;
  } catch (error) {
    console.error(`Error fetching ${pipelineType} pipeline data:`, error);
    document.getElementById(`${pipelineType}-chart-loading`).style.display = 'none';
    document.getElementById(`${pipelineType}-chart-error`).style.display = 'block';
    document.getElementById(`${pipelineType}-chart-error`).textContent = `Error loading chart: ${error.message}`;
    return null;
  }
}

// Global chart instances with unique IDs
window.chartInstances = {};

// Create or update a chart
function createOrUpdateChart(pipelineType, chartType, data) {
  const chartCanvas = document.getElementById(`${pipelineType}-chart`);
  const chartContainer = document.getElementById(`${pipelineType}-chart-container`);
  
  if (!chartCanvas || !chartContainer || !data) {
    console.error(`Missing required elements for ${pipelineType} chart`);
    return;
  }
  
  // Only destroy existing chart if we're changing the chart type
  if (window.chartInstances[pipelineType]) {
    const currentConfig = window.chartInstances[pipelineType].config;
    // If the chart type is the same, just update the data
    if (currentConfig && currentConfig.type === chartType) {
      // Update the chart data
      window.chartInstances[pipelineType].data.labels = data.stages.map(stage => stage.name);
      window.chartInstances[pipelineType].data.datasets[0].data = data.stages.map(stage => stage.percentage);
      window.chartInstances[pipelineType].data.datasets[0].backgroundColor = 
        data.stages.map((stage, index) => stage.color || defaultColors[index % defaultColors.length]);
      window.chartInstances[pipelineType].update();
      return window.chartInstances[pipelineType];
    }
    
    // Otherwise destroy the existing chart
    window.chartInstances[pipelineType].destroy();
    window.chartInstances[pipelineType] = null;
  }
  
  // Prepare chart data
  const labels = data.stages.map(stage => stage.name);
  const values = data.stages.map(stage => stage.percentage);
  const colors = data.stages.map((stage, index) => stage.color || defaultColors[index % defaultColors.length]);
  
  // Chart configuration
  const chartConfig = {
    type: chartType,
    data: {
      labels: labels,
      datasets: [{
        data: values,
        backgroundColor: colors,
        hoverBackgroundColor: colors,
        hoverBorderColor: "rgba(234, 236, 244, 1)",
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          position: 'right',
          labels: {
            usePointStyle: true,
            padding: 20
          }
        },
        tooltip: {
          callbacks: {
            label: function(context) {
              return `${context.label}: ${context.raw}%`;
            }
          }
        }
      },
      cutout: chartType === 'pie' ? '0%' : '70%'
    }
  };
  
  try {
    // Create new chart
    console.log(`Creating new ${chartType} chart for ${pipelineType}`);
    const newChart = new Chart(chartCanvas, chartConfig);
    
    // Store chart reference in our instances object
    chartInstances[pipelineType] = newChart;
    
    // Also store in the old variables for backward compatibility
    if (pipelineType === 'person') {
      peopleChart = newChart;
    } else if (pipelineType === 'church') {
      churchChart = newChart;
    }
    
    console.log(`Successfully created ${pipelineType} chart`);
    return newChart;
  } catch (error) {
    console.error(`Error creating ${pipelineType} chart:`, error);
    // Display error message on the chart container
    const errorElement = document.getElementById(`${pipelineType}-chart-error`);
    if (errorElement) {
      errorElement.style.display = 'block';
      errorElement.textContent = `Error creating chart: ${error.message}`;
    }
    return null;
  }
}

// Sample data for testing charts
const samplePeopleData = {
  pipeline_id: 3,
  pipeline_name: 'People Pipeline',
  pipeline_type: 'person',
  total_contacts: 100,
  stages: [
    { id: 1, name: 'New Contact', position: 1, color: '#4e73df', contact_count: 30, percentage: 30 },
    { id: 2, name: 'Initial Meeting', position: 2, color: '#1cc88a', contact_count: 25, percentage: 25 },
    { id: 3, name: 'Follow-up', position: 3, color: '#36b9cc', contact_count: 20, percentage: 20 },
    { id: 4, name: 'Committed', position: 4, color: '#f6c23e', contact_count: 15, percentage: 15 },
    { id: 5, name: 'Active', position: 5, color: '#e74a3b', contact_count: 10, percentage: 10 }
  ]
};

const sampleChurchData = {
  pipeline_id: 4,
  pipeline_name: 'Church Pipeline',
  pipeline_type: 'church',
  total_contacts: 50,
  stages: [
    { id: 6, name: 'Identified', position: 1, color: '#4e73df', contact_count: 15, percentage: 30 },
    { id: 7, name: 'Initial Contact', position: 2, color: '#1cc88a', contact_count: 10, percentage: 20 },
    { id: 8, name: 'Meeting Scheduled', position: 3, color: '#36b9cc', contact_count: 8, percentage: 16 },
    { id: 9, name: 'Meeting Completed', position: 4, color: '#f6c23e', contact_count: 7, percentage: 14 },
    { id: 10, name: 'Partnership Discussed', position: 5, color: '#e74a3b', contact_count: 6, percentage: 12 },
    { id: 11, name: 'Partnership Established', position: 6, color: '#6f42c1', contact_count: 4, percentage: 8 }
  ]
};

// Immediately use sample data to create charts
function createSampleCharts() {
  // Update total counts with sample data
  document.getElementById('person-total-count').textContent = 
    `Total: ${samplePeopleData.total_contacts} People`;
  document.getElementById('church-total-count').textContent = 
    `Total: ${sampleChurchData.total_contacts} Churches`;
    
  // Create charts with sample data
  createOrUpdateChart('person', 'pie', samplePeopleData);
  createOrUpdateChart('church', 'pie', sampleChurchData);
}

// Initialize charts
async function initializeCharts() {
  try {
    // First try to load data from API
    const peopleData = await fetchPipelineData('person');
    if (peopleData) {
      createOrUpdateChart('person', 'pie', peopleData);
    }
    
    // Load church pipeline data and create chart
    const churchData = await fetchPipelineData('church');
    if (churchData) {
      createOrUpdateChart('church', 'pie', churchData);
    }
  } catch (error) {
    // Silently fall back to sample data if anything fails
    // No need to call createSampleCharts() here since it's already called on page load
  }
  
  // Ensure charts are properly rendered
  setTimeout(() => {
    Object.keys(window.chartInstances).forEach(key => {
      if (window.chartInstances[key]) {
        window.chartInstances[key].update();
      }
    });
  }, 100);
}

// Handle chart type button clicks
function setupChartTypeButtons() {
  document.querySelectorAll('.chart-type-btn').forEach(button => {
    button.addEventListener('click', async function() {
      const pipelineType = this.dataset.pipeline;
      const chartType = this.dataset.chartType;
      
      // Update active button
      document.querySelectorAll(`[data-pipeline="${pipelineType}"] .chart-type-btn`).forEach(btn => {
        btn.classList.remove('active');
      });
      this.classList.add('active');
      
      // Get existing data
      let data;
      if (pipelineType === 'person' && peopleChart) {
        data = await fetchPipelineData('person');
      } else if (pipelineType === 'church' && churchChart) {
        data = await fetchPipelineData('church');
      }
      
      if (data) {
        createOrUpdateChart(pipelineType, chartType, data);
      }
    });
  });
}

// Handle refresh button clicks
function setupRefreshButtons() {
  document.querySelectorAll('.refresh-chart-btn').forEach(button => {
    button.addEventListener('click', async function() {
      const chartType = this.dataset.chartType;
      const data = await fetchPipelineData(chartType);
      
      if (data) {
        // Get current chart type
        const activeButton = document.querySelector(`[data-pipeline="${chartType}"].chart-type-btn.active`);
        const currentChartType = activeButton ? activeButton.dataset.chartType : 'pie';
        
        createOrUpdateChart(chartType, currentChartType, data);
      }
    });
  });
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
  // Setup event listeners
  setupChartTypeButtons();
  setupRefreshButtons();
  
  // Create charts with sample data immediately
  createSampleCharts();
  
  // Then try to get real data from API
  initializeCharts();
});

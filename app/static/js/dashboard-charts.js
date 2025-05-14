// Dashboard Charts - Real-time data implementation

document.addEventListener('DOMContentLoaded', function() {
  // Fetch and create charts with real-time data from the API
  fetchAndCreateDashboardCharts();
});

// Fetch and create charts with real-time data from the API
function fetchAndCreateDashboardCharts() {
  console.log('Fetching real-time data from API for dashboard charts');
  
  // Show loading indicators
  const loadingElements = document.querySelectorAll('.chart-loading-indicator');
  loadingElements.forEach(el => el.style.display = 'flex');
  
  // Hide any previous errors
  document.querySelectorAll('.alert-danger').forEach(el => el.style.display = 'none');
  
  // Fetch people pipeline data
  fetch('/api/simple-chart-data/person')
    .then(response => {
      if (!response.ok) {
        throw new Error(`HTTP error! Status: ${response.status}`);
      }
      return response.json();
    })
    .then(data => {
      console.log('People pipeline data:', data);
      // Get the active chart type
      const activeButton = document.querySelector('[data-pipeline="person"].chart-type-btn.active');
      const chartType = activeButton ? activeButton.dataset.chartType : 'pie';
      
      if (chartType === 'doughnut') {
        createPieChart('person-chart-container', data, true);
      } else {
        createPieChart('person-chart-container', data, false);
      }
      
      document.getElementById('person-chart-loading').style.display = 'none';
    })
    .catch(error => {
      console.error('Error fetching people pipeline data:', error);
      document.getElementById('person-chart-error').textContent = `Error loading chart: ${error.message}`;
      document.getElementById('person-chart-error').style.display = 'block';
      document.getElementById('person-chart-loading').style.display = 'none';
    });
  
  // Fetch church pipeline data
  fetch('/api/simple-chart-data/church')
    .then(response => {
      if (!response.ok) {
        throw new Error(`HTTP error! Status: ${response.status}`);
      }
      return response.json();
    })
    .then(data => {
      console.log('Church pipeline data:', data);
      // Get the active chart type
      const activeButton = document.querySelector('[data-pipeline="church"].chart-type-btn.active');
      const chartType = activeButton ? activeButton.dataset.chartType : 'pie';
      
      if (chartType === 'doughnut') {
        createPieChart('church-chart-container', data, true);
      } else {
        createPieChart('church-chart-container', data, false);
      }
      
      document.getElementById('church-chart-loading').style.display = 'none';
    })
    .catch(error => {
      console.error('Error fetching church pipeline data:', error);
      document.getElementById('church-chart-error').textContent = `Error loading chart: ${error.message}`;
      document.getElementById('church-chart-error').style.display = 'block';
      document.getElementById('church-chart-loading').style.display = 'none';
    });
  
  // Set up event listeners for chart type buttons
  setupChartTypeButtons();
  
  // Set up event listeners for refresh buttons
  setupRefreshButtons();
}

// Create a pie chart
function createPieChart(containerId, data, isDoughnut = false) {
  const container = document.getElementById(containerId);
  if (!container) {
    console.error(`Container ${containerId} not found`);
    return;
  }
  
  console.log(`Creating ${isDoughnut ? 'doughnut' : 'pie'} chart for ${containerId}`);
  
  // Clear the container
  container.innerHTML = '';
  
  // Create the pie chart container
  const chartDiv = document.createElement('div');
  chartDiv.style.display = 'flex';
  chartDiv.style.flexDirection = 'column';
  chartDiv.style.alignItems = 'center';
  chartDiv.style.justifyContent = 'center';
  chartDiv.style.height = '100%';
  
  // Create the pie chart
  const pieChart = document.createElement('div');
  pieChart.style.width = '200px';
  pieChart.style.height = '200px';
  pieChart.style.borderRadius = '50%';
  pieChart.style.position = 'relative';
  
  // Create gradient for pie chart
  let gradientParts = [];
  let currentPercentage = 0;
  
  data.stages.forEach(stage => {
    const startPercentage = currentPercentage;
    const endPercentage = currentPercentage + stage.percentage;
    gradientParts.push(`${stage.color} ${startPercentage}% ${endPercentage}%`);
    currentPercentage = endPercentage;
  });
  
  // Apply gradient
  pieChart.style.background = `conic-gradient(${gradientParts.join(', ')})`;
  
  // Only add center circle for doughnut chart
  if (isDoughnut) {
    // Create center circle for donut effect
    const centerCircle = document.createElement('div');
    centerCircle.style.position = 'absolute';
    centerCircle.style.top = '50%';
    centerCircle.style.left = '50%';
    centerCircle.style.transform = 'translate(-50%, -50%)';
    centerCircle.style.width = '100px';
    centerCircle.style.height = '100px';
    centerCircle.style.background = 'white';
    centerCircle.style.borderRadius = '50%';
    
    // Add center circle to pie chart
    pieChart.appendChild(centerCircle);
  }
  
  // Create legend
  const legend = document.createElement('div');
  legend.style.marginTop = '20px';
  legend.style.display = 'flex';
  legend.style.flexWrap = 'wrap';
  legend.style.justifyContent = 'center';
  legend.style.gap = '10px';
  
  data.stages.forEach(stage => {
    const legendItem = document.createElement('div');
    legendItem.style.display = 'flex';
    legendItem.style.alignItems = 'center';
    legendItem.style.marginRight = '15px';
    
    const legendColor = document.createElement('div');
    legendColor.style.width = '15px';
    legendColor.style.height = '15px';
    legendColor.style.marginRight = '5px';
    legendColor.style.backgroundColor = stage.color;
    legendColor.style.borderRadius = '3px';
    
    const legendText = document.createElement('div');
    legendText.style.fontSize = '14px';
    legendText.textContent = `${stage.name}: ${stage.percentage}% (${stage.contact_count})`;
    
    legendItem.appendChild(legendColor);
    legendItem.appendChild(legendText);
    legend.appendChild(legendItem);
  });
  
  // Add pie chart and legend to container
  chartDiv.appendChild(pieChart);
  chartDiv.appendChild(legend);
  container.appendChild(chartDiv);
  
  // Update total count badge
  const pipelineType = containerId.split('-')[0]; // 'person' or 'church'
  const totalCountElement = document.getElementById(`${pipelineType}-total-count`);
  if (totalCountElement) {
    const label = pipelineType === 'person' ? 'People' : 'Churches';
    totalCountElement.textContent = `Total: ${data.total_contacts} ${label}`;
  }
}

// Create a bar chart
function createBarChart(containerId, data) {
  const container = document.getElementById(containerId);
  if (!container) {
    console.error(`Container ${containerId} not found`);
    return;
  }
  
  // Clear the container
  container.innerHTML = '';
  
  // Create wrapper for chart and legend
  const chartWrapper = document.createElement('div');
  chartWrapper.style.display = 'flex';
  chartWrapper.style.flexDirection = 'column';
  chartWrapper.style.height = '100%';
  
  // Create the bar chart
  const barChart = document.createElement('div');
  barChart.style.display = 'flex';
  barChart.style.flexDirection = 'column';
  barChart.style.height = '200px';
  barChart.style.marginBottom = '20px';
  
  // Create legend
  const legend = document.createElement('div');
  legend.style.display = 'flex';
  legend.style.flexWrap = 'wrap';
  legend.style.justifyContent = 'center';
  legend.style.gap = '10px';
  
  // Calculate max count for scaling
  const maxCount = Math.max(...data.stages.map(stage => stage.contact_count || 0), 1);
  
  // Create bars
  data.stages.forEach(stage => {
    // Create bar container
    const bar = document.createElement('div');
    bar.style.display = 'flex';
    bar.style.alignItems = 'center';
    bar.style.marginBottom = '10px';
    bar.style.height = '30px';
    
    // Create bar label
    const barLabel = document.createElement('div');
    barLabel.style.width = '100px';
    barLabel.style.flexShrink = '0';
    barLabel.style.paddingRight = '10px';
    barLabel.style.textAlign = 'right';
    barLabel.style.fontWeight = 'bold';
    barLabel.textContent = stage.name;
    
    // Create bar value
    const barValue = document.createElement('div');
    barValue.style.height = '100%';
    barValue.style.backgroundColor = stage.color;
    barValue.style.color = 'white';
    barValue.style.display = 'flex';
    barValue.style.alignItems = 'center';
    barValue.style.paddingLeft = '10px';
    barValue.style.borderRadius = '3px';
    
    // Calculate width based on percentage of max
    const percentage = (stage.contact_count / maxCount) * 100;
    barValue.style.width = `${Math.max(percentage, 5)}%`; // Minimum width of 5% for visibility
    barValue.textContent = stage.contact_count;
    
    // Add label and value to bar
    bar.appendChild(barLabel);
    bar.appendChild(barValue);
    
    // Add bar to chart
    barChart.appendChild(bar);
    
    // Create legend item
    const legendItem = document.createElement('div');
    legendItem.style.display = 'flex';
    legendItem.style.alignItems = 'center';
    legendItem.style.marginRight = '15px';
    
    const legendColor = document.createElement('div');
    legendColor.style.width = '15px';
    legendColor.style.height = '15px';
    legendColor.style.marginRight = '5px';
    legendColor.style.backgroundColor = stage.color;
    legendColor.style.borderRadius = '3px';
    
    const legendText = document.createElement('div');
    legendText.style.fontSize = '14px';
    legendText.textContent = `${stage.name}: ${stage.percentage}% (${stage.contact_count})`;
    
    legendItem.appendChild(legendColor);
    legendItem.appendChild(legendText);
    legend.appendChild(legendItem);
  });
  
  // Add chart and legend to wrapper
  chartWrapper.appendChild(barChart);
  chartWrapper.appendChild(legend);
  
  // Add the wrapper to the container
  container.appendChild(chartWrapper);
}

// Set up chart type buttons
function setupChartTypeButtons() {
  document.querySelectorAll('.chart-type-btn').forEach(button => {
    button.addEventListener('click', function() {
      const pipelineType = this.dataset.pipeline;
      const chartType = this.dataset.chartType;
      
      // Update active button
      document.querySelectorAll(`[data-pipeline="${pipelineType}"].chart-type-btn`).forEach(btn => {
        btn.classList.remove('active');
      });
      this.classList.add('active');
      
      // Show loading indicator
      document.getElementById(`${pipelineType}-chart-loading`).style.display = 'flex';
      
      // Fetch fresh data from API
      fetch(`/api/simple-chart-data/${pipelineType === 'person' ? 'person' : 'church'}`)
        .then(response => {
          if (!response.ok) {
            throw new Error(`HTTP error! Status: ${response.status}`);
          }
          return response.json();
        })
        .then(data => {
          console.log(`${pipelineType} pipeline data:`, data);
          
          // Create chart based on type
          if (chartType === 'pie') {
            createPieChart(`${pipelineType}-chart-container`, data, false);
          } else if (chartType === 'doughnut') {
            createPieChart(`${pipelineType}-chart-container`, data, true);
          } else if (chartType === 'bar') {
            createBarChart(`${pipelineType}-chart-container`, data);
          }
          
          // Hide loading indicator
          document.getElementById(`${pipelineType}-chart-loading`).style.display = 'none';
        })
        .catch(error => {
          console.error(`Error fetching ${pipelineType} pipeline data:`, error);
          document.getElementById(`${pipelineType}-chart-error`).textContent = `Error loading chart: ${error.message}`;
          document.getElementById(`${pipelineType}-chart-error`).style.display = 'block';
          document.getElementById(`${pipelineType}-chart-loading`).style.display = 'none';
        });
    });
  });
}

// Set up refresh buttons
function setupRefreshButtons() {
  document.querySelectorAll('.refresh-chart-btn').forEach(button => {
    button.addEventListener('click', function() {
      const pipelineType = this.dataset.chartType;
      
      // Get active chart type
      const activeButton = document.querySelector(`[data-pipeline="${pipelineType}"].chart-type-btn.active`);
      const chartType = activeButton ? activeButton.dataset.chartType : 'pie';
      
      // Show loading indicator
      document.getElementById(`${pipelineType}-chart-loading`).style.display = 'flex';
      
      // Fetch fresh data from API
      fetch(`/api/simple-chart-data/${pipelineType === 'person' ? 'person' : 'church'}`)
        .then(response => {
          if (!response.ok) {
            throw new Error(`HTTP error! Status: ${response.status}`);
          }
          return response.json();
        })
        .then(data => {
          console.log(`${pipelineType} pipeline data refreshed:`, data);
          
          // Create chart based on type
          if (chartType === 'pie') {
            createPieChart(`${pipelineType}-chart-container`, data, false);
          } else if (chartType === 'doughnut') {
            createPieChart(`${pipelineType}-chart-container`, data, true);
          } else if (chartType === 'bar') {
            createBarChart(`${pipelineType}-chart-container`, data);
          }
          
          // Hide loading indicator
          document.getElementById(`${pipelineType}-chart-loading`).style.display = 'none';
        })
        .catch(error => {
          console.error(`Error refreshing ${pipelineType} pipeline data:`, error);
          document.getElementById(`${pipelineType}-chart-error`).textContent = `Error refreshing chart: ${error.message}`;
          document.getElementById(`${pipelineType}-chart-error`).style.display = 'block';
          document.getElementById(`${pipelineType}-chart-loading`).style.display = 'none';
        });
    });
  });
}

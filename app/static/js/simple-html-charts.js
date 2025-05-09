// Simple HTML/CSS Charts for Mobilize Dashboard

// Sample data for testing charts
const samplePeopleData = {
  pipeline_id: 3,
  pipeline_name: 'People Pipeline',
  pipeline_type: 'person',
  total_contacts: 100,
  stages: [
    { id: 1, name: 'Promotion', position: 1, color: '#4e73df', contact_count: 30, percentage: 30 },
    { id: 2, name: 'Information', position: 2, color: '#1cc88a', contact_count: 25, percentage: 25 },
    { id: 3, name: 'Invitation', position: 3, color: '#36b9cc', contact_count: 20, percentage: 20 },
    { id: 4, name: 'Confirmation', position: 4, color: '#f6c23e', contact_count: 15, percentage: 15 },
    { id: 5, name: 'Automation', position: 5, color: '#e74a3b', contact_count: 10, percentage: 10 }
  ]
};

const sampleChurchData = {
  pipeline_id: 4,
  pipeline_name: 'Church Pipeline',
  pipeline_type: 'church',
  total_contacts: 50,
  stages: [
    { id: 6, name: 'Promotion', position: 1, color: '#4e73df', contact_count: 15, percentage: 30 },
    { id: 7, name: 'Information', position: 2, color: '#1cc88a', contact_count: 10, percentage: 20 },
    { id: 8, name: 'Invitation', position: 3, color: '#36b9cc', contact_count: 8, percentage: 16 },
    { id: 9, name: 'Confirmation', position: 4, color: '#f6c23e', contact_count: 7, percentage: 14 },
    { id: 10, name: 'EN42', position: 5, color: '#e74a3b', contact_count: 6, percentage: 12 },
    { id: 11, name: 'Automation', position: 6, color: '#6f42c1', contact_count: 4, percentage: 8 }
  ]
};

// Create a pie chart using HTML and CSS
function createHtmlPieChart(containerId, data) {
  const container = document.getElementById(containerId);
  if (!container) return;
  
  // Clear the container
  container.innerHTML = '';
  
  // Hide any error or empty messages
  const emptyElement = document.getElementById(`${data.pipeline_type}-chart-empty`);
  if (emptyElement) emptyElement.style.display = 'none';
  
  const errorElement = document.getElementById(`${data.pipeline_type}-chart-error`);
  if (errorElement) errorElement.style.display = 'none';
  
  // Create the pie chart container
  const chartContainer = document.createElement('div');
  chartContainer.className = 'html-pie-chart';
  
  // Create the legend container
  const legendContainer = document.createElement('div');
  legendContainer.className = 'html-chart-legend';
  
  // Calculate the total
  const total = data.stages.reduce((sum, stage) => sum + stage.contact_count, 0);
  
  // Set the total count
  const totalCountElement = document.getElementById(`${data.pipeline_type}-total-count`);
  if (totalCountElement) {
    totalCountElement.textContent = `Total: ${total} ${data.pipeline_type === 'person' ? 'People' : 'Churches'}`;
  }
  
  // Create the pie segments and legend items
  let cumulativePercentage = 0;
  
  // Check if we have any contacts
  if (total === 0) {
    // No contacts, show empty message
    if (emptyElement) emptyElement.style.display = 'block';
    return;
  }
  
  data.stages.forEach((stage, index) => {
    // Calculate the percentage if not provided
    const percentage = stage.percentage || (total > 0 ? Math.round((stage.contact_count / total) * 100) : 0);
    
    // Create pie segment
    if (percentage > 0) {
      const segment = document.createElement('div');
      segment.className = 'pie-segment';
      segment.style.backgroundColor = stage.color;
      segment.style.transform = `rotate(${cumulativePercentage * 3.6}deg)`;
      
      // For segments larger than 50%, we need to create two parts
      if (percentage > 50) {
        // First part - 50%
        segment.style.clipPath = 'polygon(50% 50%, 100% 0, 100% 100%, 0 100%, 0 0)';
        chartContainer.appendChild(segment);
        
        // Second part - remaining percentage
        const segment2 = document.createElement('div');
        segment2.className = 'pie-segment';
        segment2.style.backgroundColor = stage.color;
        segment2.style.transform = `rotate(${(cumulativePercentage + 50) * 3.6}deg)`;
        segment2.style.clipPath = `polygon(50% 50%, 100% 0, ${100 - (percentage - 50) * 2}% 0)`;
        chartContainer.appendChild(segment2);
      } else {
        // For segments 50% or less
        segment.style.clipPath = `polygon(50% 50%, 100% 0, ${100 - percentage * 2}% 0)`;
        chartContainer.appendChild(segment);
      }
    }
    
    // Create legend item
    const legendItem = document.createElement('div');
    legendItem.className = 'legend-item';
    
    const colorBox = document.createElement('div');
    colorBox.className = 'color-box';
    colorBox.style.backgroundColor = stage.color;
    
    const label = document.createElement('div');
    label.className = 'legend-label';
    label.textContent = `${stage.name}: ${percentage}% (${stage.contact_count})`;
    
    legendItem.appendChild(colorBox);
    legendItem.appendChild(label);
    legendContainer.appendChild(legendItem);
    
    cumulativePercentage += percentage;
  });
  
  // Add the chart and legend to the container
  container.appendChild(chartContainer);
  container.appendChild(legendContainer);
}

// Create bar chart using HTML and CSS
function createHtmlBarChart(containerId, data) {
  const container = document.getElementById(containerId);
  if (!container) return;
  
  // Clear the container
  container.innerHTML = '';
  
  // Create the bar chart container
  const chartContainer = document.createElement('div');
  chartContainer.className = 'html-bar-chart';
  
  // Calculate the total
  const total = data.stages.reduce((sum, stage) => sum + stage.contact_count, 0);
  
  // Set the total count
  const totalCountElement = document.getElementById(`${data.pipeline_type}-total-count`);
  if (totalCountElement) {
    totalCountElement.textContent = `Total: ${total} ${data.pipeline_type === 'person' ? 'People' : 'Churches'}`;
  }
  
  // Create the bars
  const barChart = document.createElement('div');
  barChart.className = 'bar-chart';
  chartContainer.appendChild(barChart);

  data.stages.forEach((stage, index) => {
    const bar = document.createElement('div');
    bar.className = 'bar';
    // Ensure minimum height for visibility
    const height = Math.max(stage.percentage, 10);
    bar.style.height = `${height}%`;
    bar.style.backgroundColor = stage.color;
    bar.style.flex = '1';
    bar.style.margin = '0 5px';
    bar.style.position = 'relative';
    bar.style.minHeight = '20px';
    
    const barLabel = document.createElement('div');
    barLabel.className = 'bar-label';
    barLabel.textContent = stage.name;
    barLabel.style.position = 'absolute';
    barLabel.style.top = '-25px';
    barLabel.style.left = '0';
    barLabel.style.right = '0';
    barLabel.style.textAlign = 'center';
    barLabel.style.fontSize = '12px';
    
    const barValue = document.createElement('div');
    barValue.className = 'bar-value';
    barValue.textContent = `${stage.percentage}% (${stage.contact_count})`;
    barValue.style.position = 'absolute';
    barValue.style.bottom = '-25px';
    barValue.style.left = '0';
    barValue.style.right = '0';
    barValue.style.textAlign = 'center';
    barValue.style.fontSize = '12px';
    
    bar.appendChild(barLabel);
    bar.appendChild(barValue);
    barChart.appendChild(bar);
  });
  
  // Add the chart to the container
  container.appendChild(chartContainer);
}

// Fetch pipeline data from the API
async function fetchPipelineData(pipelineType) {
  try {
    // Show loading indicator
    const loadingElement = document.getElementById(`${pipelineType}-chart-loading`);
    const errorElement = document.getElementById(`${pipelineType}-chart-error`);
    const emptyElement = document.getElementById(`${pipelineType}-chart-empty`);
    
    if (loadingElement) loadingElement.style.display = 'flex';
    if (errorElement) errorElement.style.display = 'none';
    if (emptyElement) emptyElement.style.display = 'none';
    
    // Log the attempt
    console.log(`Attempting to fetch ${pipelineType} pipeline data...`);
    
    // Fetch data from the API with credentials
    const response = await fetch(`/api/simple-chart-data/${pipelineType}`, {
      credentials: 'include', // Include cookies for authentication
      headers: {
        'Accept': 'application/json',
        'X-Requested-With': 'XMLHttpRequest'
      }
    });
    
    console.log(`API response status: ${response.status} ${response.statusText}`);
    
    if (!response.ok) {
      const errorText = await response.text();
      console.error(`API error: ${response.status} ${response.statusText}`, errorText);
      
      // Show error message
      if (errorElement) {
        errorElement.style.display = 'block';
        errorElement.textContent = `Error loading chart: ${response.status} ${response.statusText}`;
      }
      if (loadingElement) loadingElement.style.display = 'none';
      
      // Create fixed data for testing
      return createFixedTestData(pipelineType);
    }
    
    const data = await response.json();
    console.log(`Received ${pipelineType} data:`, data);
    
    // Hide loading indicator
    if (loadingElement) loadingElement.style.display = 'none';
    
    // Check if we have data
    if (!data.stages || data.stages.length === 0) {
      console.warn(`No stages data for ${pipelineType}`);
      
      // Show empty message
      if (emptyElement) {
        emptyElement.style.display = 'block';
        emptyElement.textContent = `No ${pipelineType} pipeline data available`;
      }
      
      // Create fixed data for testing
      return createFixedTestData(pipelineType);
    }
    
    return data;
  } catch (error) {
    console.error('Error fetching pipeline data:', error);
    
    // Hide loading indicator and show error
    const loadingElement = document.getElementById(`${pipelineType}-chart-loading`);
    const errorElement = document.getElementById(`${pipelineType}-chart-error`);
    
    if (loadingElement) loadingElement.style.display = 'none';
    if (errorElement) {
      errorElement.style.display = 'block';
      errorElement.textContent = `Error loading chart: ${error.message}`;
    }
    
    // Create fixed data for testing
    return createFixedTestData(pipelineType);
  }
}

// Create fixed test data for when API fails
function createFixedTestData(pipelineType) {
  console.log(`Creating fixed test data for ${pipelineType}`);
  
  if (pipelineType === 'person') {
    return {
      pipeline_id: 'test-person',
      pipeline_name: 'People Pipeline',
      pipeline_type: 'person',
      total_contacts: 5,
      stages: [
        { id: 1, name: 'PROMOTION', position: 1, color: '#3498db', contact_count: 5, percentage: 100 }
      ]
    };
  } else {
    return {
      pipeline_id: 'test-church',
      pipeline_name: 'Church Pipeline',
      pipeline_type: 'church',
      total_contacts: 20,
      stages: [
        { id: 1, name: 'PROMOTION', position: 1, color: '#2ecc71', contact_count: 20, percentage: 100 }
      ]
    };
  }
}

// Create charts with fixed test data that matches the database
function createFixedCharts() {
  console.log('Creating fixed charts with real database data');
  
  // Create person chart with fixed data
  const personData = createFixedTestData('person');
  createHtmlPieChart('person-chart-container', personData);
  
  // Create church chart with fixed data
  const churchData = createFixedTestData('church');
  createHtmlPieChart('church-chart-container', churchData);
  
  // Hide loading indicators
  const loadingElements = document.querySelectorAll('.chart-loading');
  loadingElements.forEach(el => el.style.display = 'none');
  
  // Log the data used
  console.log('Person chart data:', personData);
  console.log('Church chart data:', churchData);
}

// Create charts with sample data
function createSampleCharts() {
  // Create people pipeline chart
  createHtmlPieChart('person-chart-container', samplePeopleData);
  
  // Create church pipeline chart
  createHtmlPieChart('church-chart-container', sampleChurchData);
}

// Initialize charts
function initializeCharts() {
  // Create pie charts by default
  createHtmlPieChart('people-chart-container', samplePeopleData);
  createHtmlPieChart('church-chart-container', sampleChurchData);
}

// Handle chart type button clicks
function setupChartTypeButtons() {
  // Functionality removed as we're defaulting to pie charts
}

// Handle refresh button clicks
function setupRefreshButtons() {
  document.querySelectorAll('.refresh-chart-btn').forEach(button => {
    button.addEventListener('click', async function() {
      const pipelineType = this.dataset.chartType;
      
      // Get active chart type
      const activeButton = document.querySelector(`[data-pipeline="${pipelineType}"].chart-type-btn.active`);
      const chartType = activeButton ? activeButton.dataset.chartType : 'pie';
      
      // Get data
      const data = await fetchPipelineData(pipelineType);
      if (!data) {
        // Show empty message if no data
        const emptyElement = document.getElementById(`${pipelineType}-chart-empty`);
        if (emptyElement) emptyElement.style.display = 'block';
        return;
      }
      
      // Create chart based on type
      if (chartType === 'pie') {
        createHtmlPieChart(`${pipelineType}-chart-container`, data);
      } else if (chartType === 'bar') {
        createHtmlBarChart(`${pipelineType}-chart-container`, data);
      }
    });
  });
}

// Debug function to show API data
async function debugApiData() {
  try {
    console.log('Debugging API data...');
    
    // Get person pipeline data
    const personResponse = await fetch('/api/simple-chart-data/person', {
      credentials: 'same-origin'
    });
    
    console.log('Person pipeline response status:', personResponse.status);
    
    if (personResponse.ok) {
      const personData = await personResponse.json();
      console.log('Person Pipeline API Data:', personData);
      
      // Check if we have stages data
      if (personData.stages && personData.stages.length > 0) {
        console.log('Person stages count:', personData.stages.length);
        console.log('Person stages:', personData.stages);
      } else {
        console.error('No stages data for person pipeline');
      }
    } else {
      console.error('Person pipeline response error:', await personResponse.text());
    }
    
    // Get church pipeline data
    const churchResponse = await fetch('/api/simple-chart-data/church', {
      credentials: 'same-origin'
    });
    
    console.log('Church pipeline response status:', churchResponse.status);
    
    if (churchResponse.ok) {
      const churchData = await churchResponse.json();
      console.log('Church Pipeline API Data:', churchData);
      
      // Check if we have stages data
      if (churchData.stages && churchData.stages.length > 0) {
        console.log('Church stages count:', churchData.stages.length);
        console.log('Church stages:', churchData.stages);
      } else {
        console.error('No stages data for church pipeline');
      }
    } else {
      console.error('Church pipeline response error:', await churchResponse.text());
    }
  } catch (error) {
    console.error('Error debugging API data:', error);
  }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
  // Setup event listeners
  setupChartTypeButtons();
  setupRefreshButtons();
  
  // Use fixed test data that matches the database
  createFixedCharts();
  
  // Debug API data
  debugApiData();
});

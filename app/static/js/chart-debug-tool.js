// Chart Debugging Tool

// Function to check if Chart.js is loaded
function checkChartJsLoaded() {
  const isLoaded = typeof Chart !== 'undefined';
  console.log('Chart.js loaded:', isLoaded);
  
  // Add a visual indicator to the page
  const debugInfo = document.createElement('div');
  debugInfo.style.position = 'fixed';
  debugInfo.style.bottom = '10px';
  debugInfo.style.right = '10px';
  debugInfo.style.padding = '10px';
  debugInfo.style.background = isLoaded ? '#dff0d8' : '#f2dede';
  debugInfo.style.border = '1px solid ' + (isLoaded ? '#d6e9c6' : '#ebccd1');
  debugInfo.style.borderRadius = '4px';
  debugInfo.style.color = isLoaded ? '#3c763d' : '#a94442';
  debugInfo.style.zIndex = '9999';
  debugInfo.innerHTML = `<strong>Chart.js:</strong> ${isLoaded ? 'Loaded ✓' : 'Not Loaded ✗'}`;
  document.body.appendChild(debugInfo);
  
  // Also check for canvas elements
  const personCanvas = document.getElementById('person-chart');
  const churchCanvas = document.getElementById('church-chart');
  
  if (personCanvas) {
    console.log('Person chart canvas found with dimensions:', personCanvas.width, 'x', personCanvas.height);
    debugInfo.innerHTML += `<br><strong>Person Canvas:</strong> Found ✓`;
  } else {
    console.error('Person chart canvas not found!');
    debugInfo.innerHTML += `<br><strong>Person Canvas:</strong> Not Found ✗`;
  }
  
  if (churchCanvas) {
    console.log('Church chart canvas found with dimensions:', churchCanvas.width, 'x', churchCanvas.height);
    debugInfo.innerHTML += `<br><strong>Church Canvas:</strong> Found ✓`;
  } else {
    console.error('Church chart canvas not found!');
    debugInfo.innerHTML += `<br><strong>Church Canvas:</strong> Not Found ✗`;
  }
  
  return isLoaded;
}

// Function to manually create charts
function createDebugCharts() {
  console.log('Creating debug charts...');
  
  // Check if Chart.js is available
  if (typeof Chart === 'undefined') {
    console.error('Chart.js is not loaded!');
    alert('Chart.js is not loaded. Cannot create charts.');
    return;
  }
  
  // Clear any existing chart errors
  document.querySelectorAll('.alert').forEach(el => {
    el.style.display = 'none';
  });
  
  // Destroy any existing charts
  try {
    // Check if we have access to the chart instances from simple-charts.js
    if (window.chartInstances) {
      console.log('Destroying existing charts from chartInstances...');
      Object.keys(window.chartInstances).forEach(key => {
        if (window.chartInstances[key]) {
          window.chartInstances[key].destroy();
          window.chartInstances[key] = null;
        }
      });
    }
    
    // Also check for global chart variables
    if (window.peopleChart) {
      console.log('Destroying existing peopleChart...');
      window.peopleChart.destroy();
      window.peopleChart = null;
    }
    
    if (window.churchChart) {
      console.log('Destroying existing churchChart...');
      window.churchChart.destroy();
      window.churchChart = null;
    }
    
    // Also check for debug chart variables
    if (window.debugPersonChart) {
      console.log('Destroying existing debugPersonChart...');
      window.debugPersonChart.destroy();
      window.debugPersonChart = null;
    }
    
    if (window.debugChurchChart) {
      console.log('Destroying existing debugChurchChart...');
      window.debugChurchChart.destroy();
      window.debugChurchChart = null;
    }
    
    // Clear any Chart.js registry entries for our canvases
    if (Chart.instances) {
      Object.keys(Chart.instances).forEach(key => {
        const instance = Chart.instances[key];
        if (instance && (instance.canvas.id === 'person-chart' || instance.canvas.id === 'church-chart')) {
          instance.destroy();
        }
      });
    }
  } catch (e) {
    console.error('Error destroying existing charts:', e);
  }
  
  // Sample data for people pipeline
  const peopleData = {
    labels: ['Contacted', 'Meeting Scheduled', 'Meeting Completed', 'Follow-up', 'Committed'],
    datasets: [{
      data: [30, 25, 20, 15, 10],
      backgroundColor: [
        '#4e73df',
        '#1cc88a',
        '#36b9cc',
        '#f6c23e',
        '#e74a3b'
      ]
    }]
  };
  
  // Sample data for church pipeline
  const churchData = {
    labels: ['Identified', 'Initial Contact', 'Meeting Scheduled', 'Meeting Completed', 'Partnership Discussed', 'Partnership Established'],
    datasets: [{
      data: [25, 20, 15, 15, 15, 10],
      backgroundColor: [
        '#4e73df',
        '#1cc88a',
        '#36b9cc',
        '#f6c23e',
        '#e74a3b',
        '#6f42c1'
      ]
    }]
  };
  
  // Get canvas elements
  const personCanvas = document.getElementById('person-chart');
  const churchCanvas = document.getElementById('church-chart');
  
  console.log('Person canvas:', personCanvas);
  console.log('Church canvas:', churchCanvas);
  
  if (!personCanvas || !churchCanvas) {
    console.error('Canvas elements not found!');
    alert('Canvas elements not found. Cannot create charts.');
    return;
  }
  
  // Create charts
  try {
    // Create new charts with a slight delay to ensure DOM is ready
    setTimeout(() => {
      try {
        // Create person chart
        console.log('Creating debug person chart...');
        window.debugPersonChart = new Chart(personCanvas, {
          type: 'pie',
          data: peopleData,
          options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
              legend: {
                position: 'right'
              }
            }
          }
        });
        
        // Store in chartInstances if available
        if (window.chartInstances) {
          window.chartInstances['person'] = window.debugPersonChart;
        }
        
        // Create church chart
        console.log('Creating debug church chart...');
        window.debugChurchChart = new Chart(churchCanvas, {
          type: 'pie',
          data: churchData,
          options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
              legend: {
                position: 'right'
              }
            }
          }
        });
        
        // Store in chartInstances if available
        if (window.chartInstances) {
          window.chartInstances['church'] = window.debugChurchChart;
        }
        
        console.log('Debug charts created successfully!');
        alert('Debug charts created successfully!');
      } catch (error) {
        console.error('Error creating charts in timeout:', error);
        alert('Error creating charts: ' + error.message);
      }
    }, 100);
  } catch (error) {
    console.error('Error in chart creation process:', error);
    alert('Error in chart creation process: ' + error.message);
  }
}

// Add a debug button to the page
function addDebugButton() {
  const button = document.createElement('button');
  button.textContent = 'Debug Charts';
  button.style.position = 'fixed';
  button.style.bottom = '50px';
  button.style.right = '10px';
  button.style.padding = '10px';
  button.style.background = '#007bff';
  button.style.color = 'white';
  button.style.border = 'none';
  button.style.borderRadius = '4px';
  button.style.cursor = 'pointer';
  button.style.zIndex = '9999';
  button.onclick = createDebugCharts;
  document.body.appendChild(button);
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
  console.log('Chart debug tool initialized');
  const chartJsLoaded = checkChartJsLoaded();
  
  if (chartJsLoaded) {
    addDebugButton();
  } else {
    // Try to load Chart.js dynamically
    const script = document.createElement('script');
    script.src = 'https://cdn.jsdelivr.net/npm/chart.js@3.9.1/dist/chart.min.js';
    document.head.appendChild(script);
    
    script.onload = function() {
      console.log('Chart.js loaded dynamically');
      addDebugButton();
    };
    
    script.onerror = function() {
      console.error('Failed to load Chart.js dynamically');
      alert('Failed to load Chart.js. Charts will not work.');
    };
  }
});

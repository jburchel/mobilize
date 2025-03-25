import { html } from 'lit-html';

export default {
  title: 'Components/Data Visualization',
};

export const KPICards = () => html`
  <link rel="stylesheet" href="../app/static/css/design-tokens.css">
  <link rel="stylesheet" href="../app/static/css/components/data-visualization.css">
  <div style="padding: 20px; background-color: #f8f9fa;">
    <h2>KPI Cards</h2>
    <div style="display: grid; grid-template-columns: repeat(auto-fill, minmax(250px, 1fr)); gap: 20px; margin-top: 20px;">
      <div class="kpi-card primary">
        <div class="kpi-card-title">Total People</div>
        <div class="kpi-card-value">1,456</div>
        <div class="kpi-card-comparison positive">
          <span class="kpi-card-comparison-icon">↑</span> 12% from last month
        </div>
      </div>
      
      <div class="kpi-card success">
        <div class="kpi-card-title">Active Churches</div>
        <div class="kpi-card-value">187</div>
        <div class="kpi-card-comparison positive">
          <span class="kpi-card-comparison-icon">↑</span> 5% from last month
        </div>
      </div>
      
      <div class="kpi-card info">
        <div class="kpi-card-title">Total Tasks</div>
        <div class="kpi-card-value">342</div>
        <div class="kpi-card-comparison negative">
          <span class="kpi-card-comparison-icon">↓</span> 3% from last month
        </div>
      </div>
      
      <div class="kpi-card warning">
        <div class="kpi-card-title">Communications</div>
        <div class="kpi-card-value">2,874</div>
        <div class="kpi-card-comparison positive">
          <span class="kpi-card-comparison-icon">↑</span> 18% from last month
        </div>
      </div>
    </div>
  </div>
`;

export const ChartContainers = () => html`
  <link rel="stylesheet" href="../app/static/css/design-tokens.css">
  <link rel="stylesheet" href="../app/static/css/components/data-visualization.css">
  <div style="padding: 20px; background-color: #f8f9fa;">
    <div class="chart-card">
      <div class="chart-title">Monthly People Growth</div>
      <div class="chart-subtitle">New people added per month in 2023</div>
      <div class="chart-container">
        <!-- Chart would be rendered here using a library like Chart.js -->
        <div style="width: 100%; height: 100%; background-color: #f8f9fa; display: flex; align-items: center; justify-content: center; border: 1px dashed #ced4da;">
          Chart Area - In a real app, a chart would be rendered here
        </div>
      </div>
      <div class="chart-legend">
        <div class="chart-legend-item">
          <span class="chart-legend-indicator chart-color-primary"></span>
          North America
        </div>
        <div class="chart-legend-item">
          <span class="chart-legend-indicator chart-color-secondary"></span>
          Europe
        </div>
        <div class="chart-legend-item">
          <span class="chart-legend-indicator chart-color-tertiary"></span>
          Asia
        </div>
        <div class="chart-legend-item">
          <span class="chart-legend-indicator chart-color-quaternary"></span>
          Africa
        </div>
      </div>
    </div>
    
    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-top: 20px;">
      <div class="chart-card">
        <div class="chart-title">People by Status</div>
        <div class="chart-container small">
          <!-- Small chart placeholder -->
          <div style="width: 100%; height: 100%; background-color: #f8f9fa; display: flex; align-items: center; justify-content: center; border: 1px dashed #ced4da;">
            Pie Chart - Status Distribution
          </div>
        </div>
      </div>
      
      <div class="chart-card">
        <div class="chart-title">Communication Types</div>
        <div class="chart-container small">
          <!-- Small chart placeholder -->
          <div style="width: 100%; height: 100%; background-color: #f8f9fa; display: flex; align-items: center; justify-content: center; border: 1px dashed #ced4da;">
            Bar Chart - Communication Types
          </div>
        </div>
      </div>
    </div>
  </div>
`;

export const ProgressBars = () => html`
  <link rel="stylesheet" href="../app/static/css/design-tokens.css">
  <link rel="stylesheet" href="../app/static/css/components/data-visualization.css">
  <div style="padding: 20px; max-width: 800px; margin: 0 auto; background-color: #f8f9fa;">
    <h2>Progress Bars</h2>
    
    <div style="margin-bottom: 24px;">
      <h4>Basic Progress Bar</h4>
      <div class="progress" style="margin-top: 8px;">
        <div class="progress-bar" style="width: 65%;" role="progressbar" aria-valuenow="65" aria-valuemin="0" aria-valuemax="100">
          65%
        </div>
      </div>
    </div>
    
    <div style="margin-bottom: 24px;">
      <h4>Striped Progress Bar</h4>
      <div class="progress" style="margin-top: 8px;">
        <div class="progress-bar progress-bar-striped" style="width: 45%;" role="progressbar" aria-valuenow="45" aria-valuemin="0" aria-valuemax="100">
          45%
        </div>
      </div>
    </div>
    
    <div style="margin-bottom: 24px;">
      <h4>Animated Progress Bar</h4>
      <div class="progress" style="margin-top: 8px;">
        <div class="progress-bar progress-bar-striped progress-bar-animated" style="width: 75%;" role="progressbar" aria-valuenow="75" aria-valuemin="0" aria-valuemax="100">
          75%
        </div>
      </div>
    </div>
    
    <div style="margin-bottom: 24px;">
      <h4>Colored Progress Bars</h4>
      <div style="margin-bottom: 12px; margin-top: 8px;">
        <div class="progress">
          <div class="progress-bar bg-success" style="width: 80%;" role="progressbar" aria-valuenow="80" aria-valuemin="0" aria-valuemax="100">
            Success
          </div>
        </div>
      </div>
      <div style="margin-bottom: 12px;">
        <div class="progress">
          <div class="progress-bar bg-info" style="width: 60%;" role="progressbar" aria-valuenow="60" aria-valuemin="0" aria-valuemax="100">
            Info
          </div>
        </div>
      </div>
      <div style="margin-bottom: 12px;">
        <div class="progress">
          <div class="progress-bar bg-warning" style="width: 40%;" role="progressbar" aria-valuenow="40" aria-valuemin="0" aria-valuemax="100">
            Warning
          </div>
        </div>
      </div>
      <div>
        <div class="progress">
          <div class="progress-bar bg-danger" style="width: 20%;" role="progressbar" aria-valuenow="20" aria-valuemin="0" aria-valuemax="100">
            Danger
          </div>
        </div>
      </div>
    </div>
  </div>
`;

export const GaugeCharts = () => html`
  <link rel="stylesheet" href="../app/static/css/design-tokens.css">
  <link rel="stylesheet" href="../app/static/css/components/data-visualization.css">
  <div style="padding: 20px; max-width: 800px; margin: 0 auto; background-color: #f8f9fa;">
    <h2>Gauge Charts</h2>
    
    <div style="display: flex; flex-wrap: wrap; justify-content: space-around; margin-top: 32px;">
      <div>
        <div class="gauge-container">
          <div class="gauge-background"></div>
          <div class="gauge-fill" style="height: 30%;"></div>
          <div class="gauge-marker"></div>
          <div class="gauge-value">30%</div>
        </div>
        <div style="text-align: center; margin-top: 40px;">Task Completion</div>
      </div>
      
      <div>
        <div class="gauge-container">
          <div class="gauge-background"></div>
          <div class="gauge-fill" style="height: 75%; background-color: var(--color-primary-green);"></div>
          <div class="gauge-marker"></div>
          <div class="gauge-value">75%</div>
        </div>
        <div style="text-align: center; margin-top: 40px;">Goal Progress</div>
      </div>
      
      <div>
        <div class="gauge-container">
          <div class="gauge-background"></div>
          <div class="gauge-fill" style="height: 90%; background-color: var(--color-danger);"></div>
          <div class="gauge-marker"></div>
          <div class="gauge-value">90%</div>
        </div>
        <div style="text-align: center; margin-top: 40px;">Server Load</div>
      </div>
    </div>
  </div>
`;

export const SparklineCharts = () => html`
  <link rel="stylesheet" href="../app/static/css/design-tokens.css">
  <link rel="stylesheet" href="../app/static/css/components/data-visualization.css">
  <div style="padding: 20px; max-width: 800px; margin: 0 auto; background-color: #f8f9fa;">
    <h2>Sparkline Charts</h2>
    
    <div class="card" style="margin-top: 24px; padding: 16px;">
      <table style="width: 100%; border-collapse: collapse;">
        <thead>
          <tr style="border-bottom: 1px solid var(--color-border);">
            <th style="text-align: left; padding: 12px;">Metric</th>
            <th style="text-align: right; padding: 12px;">Value</th>
            <th style="text-align: center; padding: 12px;">Trend</th>
          </tr>
        </thead>
        <tbody>
          <tr style="border-bottom: 1px solid var(--color-border);">
            <td style="padding: 12px;">Website Visits</td>
            <td style="text-align: right; padding: 12px;">5,234</td>
            <td style="text-align: center; padding: 12px;">
              <div class="sparkline">
                <!-- SVG sparkline chart would be here in real implementation -->
                <svg width="80" height="24" viewBox="0 0 80 24" style="stroke: var(--color-primary-blue); fill: none; stroke-width: 2;">
                  <path d="M0,12 L10,14 L20,10 L30,16 L40,8 L50,18 L60,4 L70,6 L80,2" />
                </svg>
              </div>
            </td>
          </tr>
          <tr style="border-bottom: 1px solid var(--color-border);">
            <td style="padding: 12px;">New Contacts</td>
            <td style="text-align: right; padding: 12px;">245</td>
            <td style="text-align: center; padding: 12px;">
              <div class="sparkline">
                <svg width="80" height="24" viewBox="0 0 80 24" style="stroke: var(--color-primary-green); fill: none; stroke-width: 2;">
                  <path d="M0,18 L10,16 L20,20 L30,14 L40,12 L50,8 L60,6 L70,4 L80,2" />
                </svg>
              </div>
            </td>
          </tr>
          <tr style="border-bottom: 1px solid var(--color-border);">
            <td style="padding: 12px;">Task Completion</td>
            <td style="text-align: right; padding: 12px;">82%</td>
            <td style="text-align: center; padding: 12px;">
              <div class="sparkline">
                <svg width="80" height="24" viewBox="0 0 80 24" style="stroke: var(--color-warning); fill: none; stroke-width: 2;">
                  <path d="M0,14 L10,12 L20,16 L30,8 L40,14 L50,10 L60,18 L70,6 L80,12" />
                </svg>
              </div>
            </td>
          </tr>
          <tr>
            <td style="padding: 12px;">Revenue</td>
            <td style="text-align: right; padding: 12px;">$18,245</td>
            <td style="text-align: center; padding: 12px;">
              <div class="sparkline">
                <svg width="80" height="24" viewBox="0 0 80 24" style="stroke: var(--color-success); fill: none; stroke-width: 2;">
                  <path d="M0,20 L10,18 L20,14 L30,16 L40,10 L50,12 L60,8 L70,4 L80,2" />
                </svg>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
`;

export const ChartTooltips = () => html`
  <link rel="stylesheet" href="../app/static/css/design-tokens.css">
  <link rel="stylesheet" href="../app/static/css/components/data-visualization.css">
  <div style="padding: 20px; max-width: 800px; margin: 0 auto; background-color: #f8f9fa;">
    <h2>Chart Tooltips</h2>
    
    <div style="position: relative; margin-top: 32px; height: 300px; border: 1px dashed var(--color-border); display: flex; align-items: center; justify-content: center;">
      <div>Chart area - hover points would show tooltips</div>
      
      <!-- Example tooltip positioned in the chart area -->
      <div class="chart-tooltip" style="position: absolute; top: 100px; left: 300px;">
        <div class="chart-tooltip-title">November 2023</div>
        <div>North America: <span class="chart-tooltip-value">245</span></div>
        <div>Europe: <span class="chart-tooltip-value">189</span></div>
        <div>Asia: <span class="chart-tooltip-value">312</span></div>
      </div>
    </div>
    
    <div style="margin-top: 40px;">
      <h4>Tooltip Variations</h4>
      <div style="display: flex; flex-wrap: wrap; gap: 20px; margin-top: 16px;">
        <div class="chart-tooltip">
          <div class="chart-tooltip-title">Basic Tooltip</div>
          <div>Value: <span class="chart-tooltip-value">42</span></div>
        </div>
        
        <div class="chart-tooltip" style="background-color: var(--color-primary-blue); color: white; border-color: var(--color-primary-blue-dark);">
          <div class="chart-tooltip-title" style="border-color: rgba(255,255,255,0.2);">Dark Tooltip</div>
          <div>Value: <span class="chart-tooltip-value">86</span></div>
        </div>
        
        <div class="chart-tooltip" style="max-width: 200px;">
          <div class="chart-tooltip-title">Multi-line Tooltip</div>
          <div>Series 1: <span class="chart-tooltip-value">126</span></div>
          <div>Series 2: <span class="chart-tooltip-value">98</span></div>
          <div>Series 3: <span class="chart-tooltip-value">54</span></div>
        </div>
      </div>
    </div>
  </div>
`; 
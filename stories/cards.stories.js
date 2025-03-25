import { html } from 'lit-html';

export default {
  title: 'Components/Cards',
};

export const CardVariants = () => {
  return html`
    <div style="font-family: var(--font-family-base); padding: 2rem;">
      <h1 style="font-family: var(--font-family-headings); margin-bottom: 2rem;">Card Variants</h1>
      
      <div style="display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 1.5rem; margin-bottom: 2rem;">
        <!-- Basic Card -->
        <div class="card">
          <div class="card-body">
            <h5 class="card-title">Basic Card</h5>
            <p class="card-text">This is a basic card with no header or footer, just a body with content.</p>
          </div>
        </div>
        
        <!-- Card with Header and Footer -->
        <div class="card">
          <div class="card-header">
            <h5 class="card-title mb-0">Card with Header & Footer</h5>
          </div>
          <div class="card-body">
            <p class="card-text">This card has a header with a title and a footer with additional information.</p>
          </div>
          <div class="card-footer text-muted">
            Last updated 3 mins ago
          </div>
        </div>
        
        <!-- Primary Blue Border Card -->
        <div class="card card-border-primary-blue">
          <div class="card-header">
            <h5 class="card-title mb-0">Primary Blue Border</h5>
          </div>
          <div class="card-body">
            <p class="card-text">Card with a primary blue border accent at the top.</p>
          </div>
        </div>
        
        <!-- Primary Green Border Card -->
        <div class="card card-border-primary-green">
          <div class="card-header">
            <h5 class="card-title mb-0">Primary Green Border</h5>
          </div>
          <div class="card-body">
            <p class="card-text">Card with a primary green border accent at the top.</p>
          </div>
        </div>
        
        <!-- Stat Card -->
        <div class="card stat-card">
          <div class="card-body">
            <div class="d-flex justify-content-between align-items-center">
              <div>
                <h6 class="text-muted mb-1">TOTAL CONTACTS</h6>
                <h3>247</h3>
              </div>
              <div>
                <i class="fas fa-users fa-2x text-muted"></i>
              </div>
            </div>
          </div>
        </div>
        
        <!-- Green Stat Card -->
        <div class="card stat-card green">
          <div class="card-body">
            <div class="d-flex justify-content-between align-items-center">
              <div>
                <h6 class="text-muted mb-1">NEW LEADS</h6>
                <h3>36</h3>
              </div>
              <div>
                <i class="fas fa-user-plus fa-2x text-muted"></i>
              </div>
            </div>
          </div>
        </div>
      </div>
      
      <h2 style="margin-top: 2rem;">Dashboard Cards</h2>
      <div style="display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 1.5rem; margin-bottom: 2rem;">
        <!-- Dashboard Primary Blue Card -->
        <div class="dashboard-stat-card primary-blue">
          <div class="card-body">
            <div class="d-flex justify-content-between align-items-center">
              <div>
                <h6 class="text-muted mb-1">TOTAL REVENUE</h6>
                <h3>$24,750</h3>
                <p class="mb-0 text-success"><i class="fas fa-arrow-up"></i> 3.5% Increase</p>
              </div>
              <div>
                <i class="fas fa-dollar-sign fa-3x text-muted"></i>
              </div>
            </div>
          </div>
        </div>
        
        <!-- Dashboard Primary Green Card -->
        <div class="dashboard-stat-card primary-green">
          <div class="card-body">
            <div class="d-flex justify-content-between align-items-center">
              <div>
                <h6 class="text-muted mb-1">CONVERSION RATE</h6>
                <h3>18.2%</h3>
                <p class="mb-0 text-success"><i class="fas fa-arrow-up"></i> 2.1% Increase</p>
              </div>
              <div>
                <i class="fas fa-chart-line fa-3x text-muted"></i>
              </div>
            </div>
          </div>
        </div>
        
        <!-- Dashboard Gray Card -->
        <div class="dashboard-stat-card gray">
          <div class="card-body">
            <div class="d-flex justify-content-between align-items-center">
              <div>
                <h6 class="text-muted mb-1">TASKS COMPLETED</h6>
                <h3>42/56</h3>
                <p class="mb-0"><i class="fas fa-clock"></i> 75% Complete</p>
              </div>
              <div>
                <i class="fas fa-tasks fa-3x text-muted"></i>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  `;
};

export const Containers = () => {
  return html`
    <div style="font-family: var(--font-family-base); padding: 2rem;">
      <h1 style="font-family: var(--font-family-headings); margin-bottom: 2rem;">Containers</h1>
      
      <h2 style="margin-top: 2rem;">Fixed Container</h2>
      <div class="container border p-3 mb-4" style="background-color: var(--color-gray-100);">
        <p>This is a fixed-width container. It has a maximum width and centers content on larger screens.</p>
        <p>The container's max-width changes at different breakpoints.</p>
      </div>
      
      <h2 style="margin-top: 2rem;">Fluid Container</h2>
      <div class="container-fluid border p-3 mb-4" style="background-color: var(--color-gray-100);">
        <p>This is a fluid container. It spans the entire width of the viewport, regardless of screen size.</p>
        <p>Fluid containers are useful for full-width layouts or when you want content to take up all available space.</p>
      </div>
      
      <h2 style="margin-top: 2rem;">Header Container</h2>
      <div class="header-container mb-4">
        <h2 class="m-0">Page Title</h2>
      </div>
      
      <h2 style="margin-top: 2rem;">Table Container</h2>
      <div class="table-container border p-3 mb-4">
        <table class="table">
          <thead>
            <tr>
              <th>#</th>
              <th>First Name</th>
              <th>Last Name</th>
              <th>Email</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td>1</td>
              <td>John</td>
              <td>Doe</td>
              <td>john@example.com</td>
            </tr>
            <tr>
              <td>2</td>
              <td>Jane</td>
              <td>Smith</td>
              <td>jane@example.com</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  `;
};

export const CardUsageGuidelines = () => {
  return html`
    <div style="font-family: var(--font-family-base); padding: 2rem; max-width: 800px;">
      <h1 style="font-family: var(--font-family-headings); margin-bottom: 2rem;">Card Usage Guidelines</h1>
      
      <div style="margin-bottom: 2rem;">
        <h2>When to Use Cards</h2>
        <ul>
          <li>To group related content and functionality</li>
          <li>To present collections of similar items (like contacts, tasks, etc.)</li>
          <li>To create visual separation between different sections</li>
          <li>To highlight important information or metrics</li>
        </ul>
      </div>
      
      <div style="margin-bottom: 2rem;">
        <h2>Card Structure</h2>
        <p>A typical card may include:</p>
        <ul>
          <li><strong>Header:</strong> Contains the card title and optional actions</li>
          <li><strong>Body:</strong> The main content area</li>
          <li><strong>Footer:</strong> Optional area for secondary information or actions</li>
        </ul>
      </div>
      
      <div style="margin-bottom: 2rem;">
        <h2>Best Practices</h2>
        <ul>
          <li>Use consistent card layouts and spacing within a view</li>
          <li>Ensure card borders and shadows have sufficient contrast with the background</li>
          <li>Use color accents sparingly and consistently to indicate card types or categories</li>
          <li>Keep cards focused on a single topic or group of related information</li>
          <li>Ensure the card content has proper hierarchy (headings, text, actions)</li>
        </ul>
      </div>
      
      <div style="margin-bottom: 2rem;">
        <h2>Accessibility Considerations</h2>
        <ul>
          <li>Ensure proper heading hierarchy within cards</li>
          <li>Maintain sufficient color contrast for card content</li>
          <li>Make interactive elements within cards accessible via keyboard</li>
          <li>Use ARIA attributes when appropriate</li>
        </ul>
      </div>
    </div>
  `;
}; 
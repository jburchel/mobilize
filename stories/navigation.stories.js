import { html } from 'lit-html';

export default {
  title: 'Components/Navigation',
  parameters: {
    layout: 'fullscreen',
  },
};

export const Sidebar = () => html`
  <link rel="stylesheet" href="../app/static/css/design-tokens.css">
  <link rel="stylesheet" href="../app/static/css/components/navigation.css">
  <div style="display: flex; height: 100vh;">
    <div class="sidebar">
      <div class="sidebar-logo">
        <img src="https://placehold.co/150x40/183963/FFFFFF?text=MOBILIZE" alt="Mobilize CRM Logo">
        <button class="sidebar-toggle" aria-label="Toggle sidebar">
          <i class="fas fa-bars"></i>
        </button>
      </div>
      <div class="sidebar-menu">
        <div class="nav-section">
          <div class="nav-section-title">Main</div>
          <div class="nav-item">
            <a href="#" class="nav-link active">
              <span class="nav-icon"><i class="fas fa-home"></i></span>
              <span class="nav-text">Dashboard</span>
            </a>
          </div>
          <div class="nav-item">
            <a href="#" class="nav-link">
              <span class="nav-icon"><i class="fas fa-user"></i></span>
              <span class="nav-text">People</span>
              <span class="nav-badge">42</span>
            </a>
          </div>
          <div class="nav-item">
            <a href="#" class="nav-link">
              <span class="nav-icon"><i class="fas fa-church"></i></span>
              <span class="nav-text">Churches</span>
            </a>
          </div>
        </div>
        
        <div class="nav-section">
          <div class="nav-section-title">Communication</div>
          <div class="nav-item">
            <a href="#" class="nav-link">
              <span class="nav-icon"><i class="fas fa-envelope"></i></span>
              <span class="nav-text">Emails</span>
            </a>
          </div>
          <div class="nav-item">
            <a href="#" class="nav-link">
              <span class="nav-icon"><i class="fas fa-tasks"></i></span>
              <span class="nav-text">Tasks</span>
              <span class="nav-badge">5</span>
            </a>
          </div>
        </div>
        
        <div class="nav-section">
          <div class="nav-section-title">Administration</div>
          <div class="nav-item">
            <a href="#" class="nav-link">
              <span class="nav-icon"><i class="fas fa-cog"></i></span>
              <span class="nav-text">Settings</span>
            </a>
          </div>
          <div class="nav-item">
            <a href="#" class="nav-link">
              <span class="nav-icon"><i class="fas fa-users"></i></span>
              <span class="nav-text">Users</span>
            </a>
          </div>
          <div class="nav-item">
            <a href="#" class="nav-link">
              <span class="nav-icon"><i class="fas fa-building"></i></span>
              <span class="nav-text">Offices</span>
            </a>
          </div>
        </div>
      </div>
      <div class="sidebar-footer">
        <div class="user-info">
          <img src="https://placehold.co/32x32/cccccc/666666?text=JD" alt="User" class="user-avatar">
          <div class="user-details">
            <div class="user-name">John Doe</div>
            <div class="user-role">Administrator</div>
          </div>
        </div>
      </div>
    </div>
    <div style="flex: 1; padding: 20px; background-color: #f8f9fa;">
      <h1>Main Content Area</h1>
      <p>This is where the main content would go.</p>
    </div>
  </div>
  <script>
    // Add Font Awesome for icons
    if (!document.querySelector('[data-fa-script]')) {
      const script = document.createElement('script');
      script.src = 'https://kit.fontawesome.com/a076d05399.js';
      script.setAttribute('data-fa-script', 'true');
      document.head.appendChild(script);
    }
  </script>
`;

export const CollapsedSidebar = () => html`
  <link rel="stylesheet" href="../app/static/css/design-tokens.css">
  <link rel="stylesheet" href="../app/static/css/components/navigation.css">
  <div style="display: flex; height: 100vh;">
    <div class="sidebar collapsed">
      <div class="sidebar-logo">
        <img src="https://placehold.co/150x40/183963/FFFFFF?text=M" alt="Mobilize CRM Logo">
        <button class="sidebar-toggle" aria-label="Toggle sidebar">
          <i class="fas fa-bars"></i>
        </button>
      </div>
      <div class="sidebar-menu">
        <div class="nav-section">
          <div class="nav-section-title">Main</div>
          <div class="nav-item">
            <a href="#" class="nav-link active">
              <span class="nav-icon"><i class="fas fa-home"></i></span>
              <span class="nav-text">Dashboard</span>
            </a>
          </div>
          <div class="nav-item">
            <a href="#" class="nav-link">
              <span class="nav-icon"><i class="fas fa-user"></i></span>
              <span class="nav-text">People</span>
              <span class="nav-badge">42</span>
            </a>
          </div>
          <div class="nav-item">
            <a href="#" class="nav-link">
              <span class="nav-icon"><i class="fas fa-church"></i></span>
              <span class="nav-text">Churches</span>
            </a>
          </div>
        </div>
      </div>
      <div class="sidebar-footer">
        <div class="user-info">
          <img src="https://placehold.co/32x32/cccccc/666666?text=JD" alt="User" class="user-avatar">
          <div class="user-details">
            <div class="user-name">John Doe</div>
            <div class="user-role">Administrator</div>
          </div>
        </div>
      </div>
    </div>
    <div style="flex: 1; padding: 20px; background-color: #f8f9fa;">
      <h1>Main Content Area</h1>
      <p>This is where the main content would go with expanded space due to collapsed sidebar.</p>
    </div>
  </div>
  <script>
    // Add Font Awesome for icons
    if (!document.querySelector('[data-fa-script]')) {
      const script = document.createElement('script');
      script.src = 'https://kit.fontawesome.com/a076d05399.js';
      script.setAttribute('data-fa-script', 'true');
      document.head.appendChild(script);
    }
  </script>
`;

export const Breadcrumbs = () => html`
  <link rel="stylesheet" href="../app/static/css/design-tokens.css">
  <link rel="stylesheet" href="../app/static/css/components/navigation.css">
  <div style="padding: 20px; background-color: #f8f9fa;">
    <div class="breadcrumb-wrapper">
      <nav aria-label="breadcrumb">
        <ol class="breadcrumb">
          <li class="breadcrumb-item"><a href="#">Home</a></li>
          <li class="breadcrumb-item"><a href="#">People</a></li>
          <li class="breadcrumb-item active" aria-current="page">John Doe</li>
        </ol>
      </nav>
    </div>
    
    <h3 style="margin-top: 24px;">Multiple Levels</h3>
    <div class="breadcrumb-wrapper">
      <nav aria-label="breadcrumb">
        <ol class="breadcrumb">
          <li class="breadcrumb-item"><a href="#">Home</a></li>
          <li class="breadcrumb-item"><a href="#">Administration</a></li>
          <li class="breadcrumb-item"><a href="#">Offices</a></li>
          <li class="breadcrumb-item"><a href="#">North America</a></li>
          <li class="breadcrumb-item active" aria-current="page">Add New Office</li>
        </ol>
      </nav>
    </div>
  </div>
`;

export const QuickActions = () => html`
  <link rel="stylesheet" href="../app/static/css/design-tokens.css">
  <link rel="stylesheet" href="../app/static/css/components/navigation.css">
  <div style="height: 400px; position: relative; background-color: #f8f9fa; padding: 20px;">
    <h2>Page Content</h2>
    <p>Hover over the floating action button to see the quick actions menu.</p>
    
    <div class="quick-actions">
      <button class="quick-actions-toggle" aria-label="Quick actions" onclick="this.parentElement.classList.toggle('open')">
        <i class="fas fa-plus"></i>
      </button>
      <div class="quick-actions-menu">
        <a href="#" class="quick-action-item">
          <span class="quick-action-icon"><i class="fas fa-user-plus"></i></span>
          <span class="quick-action-text">Add Person</span>
        </a>
        <a href="#" class="quick-action-item">
          <span class="quick-action-icon"><i class="fas fa-church"></i></span>
          <span class="quick-action-text">Add Church</span>
        </a>
        <a href="#" class="quick-action-item">
          <span class="quick-action-icon"><i class="fas fa-tasks"></i></span>
          <span class="quick-action-text">New Task</span>
        </a>
        <a href="#" class="quick-action-item">
          <span class="quick-action-icon"><i class="fas fa-envelope"></i></span>
          <span class="quick-action-text">Compose Email</span>
        </a>
      </div>
    </div>
  </div>
  <script>
    // Add Font Awesome for icons
    if (!document.querySelector('[data-fa-script]')) {
      const script = document.createElement('script');
      script.src = 'https://kit.fontawesome.com/a076d05399.js';
      script.setAttribute('data-fa-script', 'true');
      document.head.appendChild(script);
    }
  </script>
`;

export const TabNavigation = () => html`
  <link rel="stylesheet" href="../app/static/css/design-tokens.css">
  <link rel="stylesheet" href="../app/static/css/components/navigation.css">
  <div style="padding: 20px; background-color: #f8f9fa;">
    <div class="tab-navigation">
      <div class="tab-item active">Overview</div>
      <div class="tab-item">Contact Information</div>
      <div class="tab-item">Communication History</div>
      <div class="tab-item">Tasks <span class="tab-badge">3</span></div>
      <div class="tab-item">Notes</div>
      <div class="tab-item">Settings</div>
    </div>
    
    <div style="padding: 20px; border: 1px solid #dee2e6; border-top: none; background-color: white;">
      <h3>Tab Content</h3>
      <p>This is the content area for the selected tab.</p>
    </div>
  </div>
  <script>
    // Add Font Awesome for icons
    if (!document.querySelector('[data-fa-script]')) {
      const script = document.createElement('script');
      script.src = 'https://kit.fontawesome.com/a076d05399.js';
      script.setAttribute('data-fa-script', 'true');
      document.head.appendChild(script);
    }
    
    // Simple tab functionality for demo
    document.addEventListener('DOMContentLoaded', () => {
      const tabs = document.querySelectorAll('.tab-item');
      tabs.forEach(tab => {
        tab.addEventListener('click', () => {
          tabs.forEach(t => t.classList.remove('active'));
          tab.classList.add('active');
        });
      });
    });
  </script>
`;

export const MobileNavigation = () => html`
  <link rel="stylesheet" href="../app/static/css/design-tokens.css">
  <link rel="stylesheet" href="../app/static/css/components/navigation.css">
  <div style="display: flex; flex-direction: column; height: 100vh; width: 100%;">
    <div class="mobile-header">
      <button class="mobile-menu-toggle" aria-label="Open menu">
        <i class="fas fa-bars"></i>
      </button>
      <img src="https://placehold.co/150x36/183963/FFFFFF?text=MOBILIZE" alt="Mobilize CRM Logo" class="mobile-header-logo">
      <button class="mobile-menu-toggle" aria-label="User menu">
        <i class="fas fa-user-circle"></i>
      </button>
    </div>
    
    <div class="sidebar-backdrop show"></div>
    
    <div class="sidebar show" style="transform: translateX(0);">
      <div class="sidebar-logo">
        <img src="https://placehold.co/150x40/183963/FFFFFF?text=MOBILIZE" alt="Mobilize CRM Logo">
        <button class="sidebar-toggle" aria-label="Toggle sidebar">
          <i class="fas fa-times"></i>
        </button>
      </div>
      
      <div class="sidebar-menu">
        <div class="nav-section">
          <div class="nav-section-title">Main</div>
          <div class="nav-item">
            <a href="#" class="nav-link active">
              <span class="nav-icon"><i class="fas fa-home"></i></span>
              <span class="nav-text">Dashboard</span>
            </a>
          </div>
          <div class="nav-item">
            <a href="#" class="nav-link">
              <span class="nav-icon"><i class="fas fa-user"></i></span>
              <span class="nav-text">People</span>
            </a>
          </div>
        </div>
      </div>
    </div>
    
    <div class="content-wrapper" style="margin-left: 0;">
      <div style="padding: 20px;">
        <h2>Mobile Navigation</h2>
        <p>This demonstrates how the navigation looks on mobile devices.</p>
      </div>
    </div>
  </div>
  <script>
    // Add Font Awesome for icons
    if (!document.querySelector('[data-fa-script]')) {
      const script = document.createElement('script');
      script.src = 'https://kit.fontawesome.com/a076d05399.js';
      script.setAttribute('data-fa-script', 'true');
      document.head.appendChild(script);
    }
    
    // Mobile menu toggle for demo
    document.addEventListener('DOMContentLoaded', () => {
      const toggleBtns = document.querySelectorAll('.sidebar-toggle, .mobile-menu-toggle');
      const sidebar = document.querySelector('.sidebar');
      const backdrop = document.querySelector('.sidebar-backdrop');
      
      toggleBtns.forEach(btn => {
        btn.addEventListener('click', () => {
          sidebar.classList.toggle('show');
          backdrop.classList.toggle('show');
        });
      });
      
      backdrop.addEventListener('click', () => {
        sidebar.classList.remove('show');
        backdrop.classList.remove('show');
      });
    });
  </script>
`; 
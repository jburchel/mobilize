import { html } from 'lit-html';

export default {
  title: 'Components/Content',
};

export const Cards = () => html`
  <link rel="stylesheet" href="../app/static/css/design-tokens.css">
  <link rel="stylesheet" href="../app/static/css/components/content.css">
  <div style="padding: 20px; background-color: #f8f9fa;">
    <h2>Basic Cards</h2>
    <div style="display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 20px; margin-top: 20px;">
      <div class="card">
        <div class="card-header">
          <div class="card-title">Standard Card</div>
        </div>
        <div class="card-body">
          <p>This is a basic card component with header and body.</p>
        </div>
        <div class="card-footer">
          <button class="btn btn-primary">Action</button>
        </div>
      </div>
      
      <div class="card">
        <div class="card-header">
          <div class="card-title">Card with Subtitle</div>
          <div class="card-subtitle">Supporting information</div>
        </div>
        <div class="card-body">
          <p>This card includes a subtitle for additional context.</p>
        </div>
      </div>
      
      <div class="card">
        <img src="https://via.placeholder.com/300x150" alt="Placeholder" style="width: 100%; height: 150px; object-fit: cover;">
        <div class="card-body">
          <div class="card-title">Media Card</div>
          <p>A card that includes media content at the top.</p>
        </div>
      </div>
    </div>
    
    <h2 style="margin-top: 40px;">Border Variants</h2>
    <div style="display: grid; grid-template-columns: repeat(auto-fill, minmax(250px, 1fr)); gap: 20px; margin-top: 20px;">
      <div class="card border-primary">
        <div class="card-header">Primary Border</div>
        <div class="card-body">
          <p>Card with a primary border style.</p>
        </div>
      </div>
      
      <div class="card border-success">
        <div class="card-header">Success Border</div>
        <div class="card-body">
          <p>Card with a success border style.</p>
        </div>
      </div>
      
      <div class="card border-warning">
        <div class="card-header">Warning Border</div>
        <div class="card-body">
          <p>Card with a warning border style.</p>
        </div>
      </div>
      
      <div class="card border-danger">
        <div class="card-header">Danger Border</div>
        <div class="card-body">
          <p>Card with a danger border style.</p>
        </div>
      </div>
    </div>
  </div>
`;

export const ContactCards = () => html`
  <link rel="stylesheet" href="../app/static/css/design-tokens.css">
  <link rel="stylesheet" href="../app/static/css/components/content.css">
  <div style="padding: 20px; background-color: #f8f9fa;">
    <h2>Contact Cards</h2>
    <div style="display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 20px; margin-top: 20px;">
      <div class="contact-card">
        <div class="contact-card-avatar">
          <div class="avatar">JD</div>
        </div>
        <div class="contact-card-info">
          <div class="contact-card-name">John Doe</div>
          <div class="contact-card-title">Lead Pastor</div>
          <div class="contact-card-detail">
            <i class="fas fa-envelope"></i> john.doe@example.com
          </div>
          <div class="contact-card-detail">
            <i class="fas fa-phone"></i> (555) 123-4567
          </div>
        </div>
        <div class="contact-card-actions">
          <button class="btn btn-icon" aria-label="Edit contact">
            <i class="fas fa-pencil-alt"></i>
          </button>
          <button class="btn btn-icon" aria-label="View contact details">
            <i class="fas fa-eye"></i>
          </button>
        </div>
      </div>
      
      <div class="contact-card">
        <div class="contact-card-avatar">
          <div class="avatar" style="background-color: var(--color-primary-green);">SP</div>
        </div>
        <div class="contact-card-info">
          <div class="contact-card-name">Sarah Parker</div>
          <div class="contact-card-title">Worship Leader</div>
          <div class="contact-card-detail">
            <i class="fas fa-envelope"></i> sarah.p@example.com
          </div>
          <div class="contact-card-detail">
            <i class="fas fa-phone"></i> (555) 987-6543
          </div>
        </div>
        <div class="contact-card-actions">
          <button class="btn btn-icon" aria-label="Edit contact">
            <i class="fas fa-pencil-alt"></i>
          </button>
          <button class="btn btn-icon" aria-label="View contact details">
            <i class="fas fa-eye"></i>
          </button>
        </div>
      </div>
      
      <div class="contact-card">
        <div class="contact-card-avatar">
          <div class="avatar" style="background-color: var(--color-secondary);">RJ</div>
        </div>
        <div class="contact-card-info">
          <div class="contact-card-name">Robert Johnson</div>
          <div class="contact-card-title">Youth Director</div>
          <div class="contact-card-detail">
            <i class="fas fa-envelope"></i> robert.j@example.com
          </div>
          <div class="contact-card-detail">
            <i class="fas fa-phone"></i> (555) 456-7890
          </div>
        </div>
        <div class="contact-card-actions">
          <button class="btn btn-icon" aria-label="Edit contact">
            <i class="fas fa-pencil-alt"></i>
          </button>
          <button class="btn btn-icon" aria-label="View contact details">
            <i class="fas fa-eye"></i>
          </button>
        </div>
      </div>
    </div>
  </div>
`;

export const StatCards = () => html`
  <link rel="stylesheet" href="../app/static/css/design-tokens.css">
  <link rel="stylesheet" href="../app/static/css/components/content.css">
  <div style="padding: 20px; background-color: #f8f9fa;">
    <h2>Stat Cards</h2>
    <div style="display: grid; grid-template-columns: repeat(auto-fill, minmax(250px, 1fr)); gap: 20px; margin-top: 20px;">
      <div class="stat-card">
        <div class="stat-card-icon primary">
          <i class="fas fa-users"></i>
        </div>
        <div class="stat-card-content">
          <div class="stat-card-value">1,254</div>
          <div class="stat-card-label">Total People</div>
        </div>
      </div>
      
      <div class="stat-card">
        <div class="stat-card-icon success">
          <i class="fas fa-church"></i>
        </div>
        <div class="stat-card-content">
          <div class="stat-card-value">87</div>
          <div class="stat-card-label">Churches</div>
        </div>
      </div>
      
      <div class="stat-card">
        <div class="stat-card-icon warning">
          <i class="fas fa-tasks"></i>
        </div>
        <div class="stat-card-content">
          <div class="stat-card-value">156</div>
          <div class="stat-card-label">Open Tasks</div>
        </div>
      </div>
      
      <div class="stat-card">
        <div class="stat-card-icon danger">
          <i class="fas fa-envelope"></i>
        </div>
        <div class="stat-card-content">
          <div class="stat-card-value">42</div>
          <div class="stat-card-label">Unread Messages</div>
        </div>
      </div>
    </div>
  </div>
`;

export const Tables = () => html`
  <link rel="stylesheet" href="../app/static/css/design-tokens.css">
  <link rel="stylesheet" href="../app/static/css/components/content.css">
  <div style="padding: 20px; background-color: #f8f9fa;">
    <h2>Modern Tables</h2>
    
    <div class="card" style="margin-top: 20px;">
      <div class="card-header">
        <div class="card-title">People Table</div>
      </div>
      <div class="table-responsive">
        <table class="table">
          <thead>
            <tr>
              <th>Name</th>
              <th>Email</th>
              <th>Phone</th>
              <th>Status</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td>
                <div class="table-user">
                  <div class="table-user-avatar">JD</div>
                  <div class="table-user-info">
                    <div class="table-user-name">John Doe</div>
                    <div class="table-user-title">Lead Pastor</div>
                  </div>
                </div>
              </td>
              <td>john.doe@example.com</td>
              <td>(555) 123-4567</td>
              <td><span class="status-badge success">Active</span></td>
              <td>
                <div class="table-actions">
                  <button class="btn btn-icon btn-sm" aria-label="Edit">
                    <i class="fas fa-pencil-alt"></i>
                  </button>
                  <button class="btn btn-icon btn-sm" aria-label="View">
                    <i class="fas fa-eye"></i>
                  </button>
                  <button class="btn btn-icon btn-sm" aria-label="Delete">
                    <i class="fas fa-trash"></i>
                  </button>
                </div>
              </td>
            </tr>
            <tr>
              <td>
                <div class="table-user">
                  <div class="table-user-avatar" style="background-color: var(--color-primary-green);">SP</div>
                  <div class="table-user-info">
                    <div class="table-user-name">Sarah Parker</div>
                    <div class="table-user-title">Worship Leader</div>
                  </div>
                </div>
              </td>
              <td>sarah.p@example.com</td>
              <td>(555) 987-6543</td>
              <td><span class="status-badge warning">Pending</span></td>
              <td>
                <div class="table-actions">
                  <button class="btn btn-icon btn-sm" aria-label="Edit">
                    <i class="fas fa-pencil-alt"></i>
                  </button>
                  <button class="btn btn-icon btn-sm" aria-label="View">
                    <i class="fas fa-eye"></i>
                  </button>
                  <button class="btn btn-icon btn-sm" aria-label="Delete">
                    <i class="fas fa-trash"></i>
                  </button>
                </div>
              </td>
            </tr>
            <tr>
              <td>
                <div class="table-user">
                  <div class="table-user-avatar" style="background-color: var(--color-secondary);">RJ</div>
                  <div class="table-user-info">
                    <div class="table-user-name">Robert Johnson</div>
                    <div class="table-user-title">Youth Director</div>
                  </div>
                </div>
              </td>
              <td>robert.j@example.com</td>
              <td>(555) 456-7890</td>
              <td><span class="status-badge primary">New</span></td>
              <td>
                <div class="table-actions">
                  <button class="btn btn-icon btn-sm" aria-label="Edit">
                    <i class="fas fa-pencil-alt"></i>
                  </button>
                  <button class="btn btn-icon btn-sm" aria-label="View">
                    <i class="fas fa-eye"></i>
                  </button>
                  <button class="btn btn-icon btn-sm" aria-label="Delete">
                    <i class="fas fa-trash"></i>
                  </button>
                </div>
              </td>
            </tr>
            <tr>
              <td>
                <div class="table-user">
                  <div class="table-user-avatar" style="background-color: var(--color-danger);">LH</div>
                  <div class="table-user-info">
                    <div class="table-user-name">Lisa Henderson</div>
                    <div class="table-user-title">Church Admin</div>
                  </div>
                </div>
              </td>
              <td>lisa.h@example.com</td>
              <td>(555) 789-0123</td>
              <td><span class="status-badge danger">Inactive</span></td>
              <td>
                <div class="table-actions">
                  <button class="btn btn-icon btn-sm" aria-label="Edit">
                    <i class="fas fa-pencil-alt"></i>
                  </button>
                  <button class="btn btn-icon btn-sm" aria-label="View">
                    <i class="fas fa-eye"></i>
                  </button>
                  <button class="btn btn-icon btn-sm" aria-label="Delete">
                    <i class="fas fa-trash"></i>
                  </button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
`;

export const StatusBadges = () => html`
  <link rel="stylesheet" href="../app/static/css/design-tokens.css">
  <link rel="stylesheet" href="../app/static/css/components/content.css">
  <div style="padding: 20px; background-color: #f8f9fa;">
    <h2>Status Badges</h2>
    <div style="display: flex; gap: 10px; flex-wrap: wrap; margin-top: 20px;">
      <span class="status-badge primary">New</span>
      <span class="status-badge success">Active</span>
      <span class="status-badge info">In Progress</span>
      <span class="status-badge warning">Pending</span>
      <span class="status-badge danger">Inactive</span>
      <span class="status-badge secondary">Archived</span>
    </div>
    
    <h3 style="margin-top: 24px;">With Icons</h3>
    <div style="display: flex; gap: 10px; flex-wrap: wrap; margin-top: 12px;">
      <span class="status-badge primary"><i class="fas fa-plus-circle"></i> New</span>
      <span class="status-badge success"><i class="fas fa-check-circle"></i> Active</span>
      <span class="status-badge info"><i class="fas fa-spinner"></i> In Progress</span>
      <span class="status-badge warning"><i class="fas fa-clock"></i> Pending</span>
      <span class="status-badge danger"><i class="fas fa-exclamation-circle"></i> Inactive</span>
      <span class="status-badge secondary"><i class="fas fa-archive"></i> Archived</span>
    </div>
    
    <h3 style="margin-top: 24px;">Pill Style</h3>
    <div style="display: flex; gap: 10px; flex-wrap: wrap; margin-top: 12px;">
      <span class="status-badge primary pill">New</span>
      <span class="status-badge success pill">Active</span>
      <span class="status-badge info pill">In Progress</span>
      <span class="status-badge warning pill">Pending</span>
      <span class="status-badge danger pill">Inactive</span>
      <span class="status-badge secondary pill">Archived</span>
    </div>
  </div>
`;

export const SkeletonLoaders = () => html`
  <link rel="stylesheet" href="../app/static/css/design-tokens.css">
  <link rel="stylesheet" href="../app/static/css/components/content.css">
  <div style="padding: 20px; background-color: #f8f9fa;">
    <h2>Skeleton Loaders</h2>
    
    <h3 style="margin-top: 24px;">Text Skeletons</h3>
    <div style="margin-top: 12px;">
      <div class="skeleton-loader skeleton-title"></div>
      <div class="skeleton-loader" style="width: 80%;"></div>
      <div class="skeleton-loader" style="width: 90%;"></div>
      <div class="skeleton-loader" style="width: 75%;"></div>
    </div>
    
    <h3 style="margin-top: 32px;">Card Skeleton</h3>
    <div class="card" style="margin-top: 12px;">
      <div class="card-body">
        <div class="skeleton-loader skeleton-title"></div>
        <div class="skeleton-loader" style="width: 90%; margin-top: 16px;"></div>
        <div class="skeleton-loader" style="width: 95%; margin-top: 8px;"></div>
        <div class="skeleton-loader" style="width: 85%; margin-top: 8px;"></div>
        <div class="skeleton-loader" style="width: 40%; margin-top: 24px;"></div>
      </div>
    </div>
    
    <h3 style="margin-top: 32px;">Table Skeleton</h3>
    <div class="card" style="margin-top: 12px;">
      <div class="table-responsive">
        <table class="table">
          <thead>
            <tr>
              <th>Name</th>
              <th>Email</th>
              <th>Phone</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td><div class="skeleton-loader"></div></td>
              <td><div class="skeleton-loader"></div></td>
              <td><div class="skeleton-loader"></div></td>
              <td><div class="skeleton-loader" style="width: 70px;"></div></td>
            </tr>
            <tr>
              <td><div class="skeleton-loader"></div></td>
              <td><div class="skeleton-loader"></div></td>
              <td><div class="skeleton-loader"></div></td>
              <td><div class="skeleton-loader" style="width: 70px;"></div></td>
            </tr>
            <tr>
              <td><div class="skeleton-loader"></div></td>
              <td><div class="skeleton-loader"></div></td>
              <td><div class="skeleton-loader"></div></td>
              <td><div class="skeleton-loader" style="width: 70px;"></div></td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
    
    <h3 style="margin-top: 32px;">Contact Card Skeleton</h3>
    <div style="display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 20px; margin-top: 12px;">
      <div class="contact-card">
        <div class="skeleton-loader skeleton-avatar"></div>
        <div style="flex-grow: 1; padding: 16px;">
          <div class="skeleton-loader skeleton-title"></div>
          <div class="skeleton-loader" style="width: 60%; margin-top: 8px;"></div>
          <div class="skeleton-loader" style="margin-top: 16px;"></div>
          <div class="skeleton-loader" style="margin-top: 8px;"></div>
        </div>
      </div>
    </div>
  </div>
`;

export const EmptyStates = () => html`
  <link rel="stylesheet" href="../app/static/css/design-tokens.css">
  <link rel="stylesheet" href="../app/static/css/components/content.css">
  <div style="padding: 20px; background-color: #f8f9fa;">
    <h2>Empty States</h2>
    
    <div class="card" style="margin-top: 20px;">
      <div class="empty-state">
        <div class="empty-state-icon">
          <i class="fas fa-users"></i>
        </div>
        <div class="empty-state-title">No People Found</div>
        <div class="empty-state-description">
          There are no people matching your search criteria. Try adjusting your filters or add a new person.
        </div>
        <div class="empty-state-action">
          <button class="btn btn-primary">Add New Person</button>
        </div>
      </div>
    </div>
    
    <div class="card" style="margin-top: 20px;">
      <div class="empty-state">
        <div class="empty-state-icon" style="background-color: var(--color-primary-blue-light);">
          <i class="fas fa-envelope" style="color: var(--color-primary-blue);"></i>
        </div>
        <div class="empty-state-title">Your Inbox is Empty</div>
        <div class="empty-state-description">
          No messages to display. When you receive new messages, they will appear here.
        </div>
        <div class="empty-state-action">
          <button class="btn btn-outline-primary">Compose Message</button>
        </div>
      </div>
    </div>
    
    <div class="card" style="margin-top: 20px;">
      <div class="empty-state">
        <div class="empty-state-icon" style="background-color: var(--color-warning-light);">
          <i class="fas fa-exclamation-triangle" style="color: var(--color-warning);"></i>
        </div>
        <div class="empty-state-title">No Results Found</div>
        <div class="empty-state-description">
          We couldn't find any results matching your search. Please try a different search term or browse all items.
        </div>
        <div class="empty-state-action">
          <button class="btn btn-outline-secondary">View All</button>
          <button class="btn btn-primary">New Search</button>
        </div>
      </div>
    </div>
  </div>
`;

export const CardGrids = () => html`
  <link rel="stylesheet" href="../app/static/css/design-tokens.css">
  <link rel="stylesheet" href="../app/static/css/components/content.css">
  <div style="padding: 20px; background-color: #f8f9fa;">
    <h2>Card Grids</h2>
    
    <h3 style="margin-top: 24px;">1-Column Layout</h3>
    <div class="card-grid-1" style="margin-top: 12px;">
      <div class="card">
        <div class="card-body">
          <div class="card-title">One Column Layout</div>
          <p>This layout is ideal for detailed content or on small screens.</p>
        </div>
      </div>
      <div class="card">
        <div class="card-body">
          <div class="card-title">Full Width Card</div>
          <p>This layout maximizes reading space and allows for detailed information display.</p>
        </div>
      </div>
    </div>
    
    <h3 style="margin-top: 32px;">2-Column Layout</h3>
    <div class="card-grid-2" style="margin-top: 12px;">
      <div class="card">
        <div class="card-body">
          <div class="card-title">Two Column Layout</div>
          <p>Balanced layout for medium detail level.</p>
        </div>
      </div>
      <div class="card">
        <div class="card-body">
          <div class="card-title">Second Card</div>
          <p>These cards appear side by side on larger screens.</p>
        </div>
      </div>
      <div class="card">
        <div class="card-body">
          <div class="card-title">Third Card</div>
          <p>This will create a new row in the 2-column layout.</p>
        </div>
      </div>
      <div class="card">
        <div class="card-body">
          <div class="card-title">Fourth Card</div>
          <p>Completing the second row of the grid.</p>
        </div>
      </div>
    </div>
    
    <h3 style="margin-top: 32px;">3-Column Layout</h3>
    <div class="card-grid-3" style="margin-top: 12px;">
      <div class="card">
        <div class="card-body">
          <div class="card-title">Three Column</div>
          <p>More condensed display.</p>
        </div>
      </div>
      <div class="card">
        <div class="card-body">
          <div class="card-title">Second Card</div>
          <p>More items per row.</p>
        </div>
      </div>
      <div class="card">
        <div class="card-body">
          <div class="card-title">Third Card</div>
          <p>Completing the row.</p>
        </div>
      </div>
    </div>
    
    <h3 style="margin-top: 32px;">4-Column Layout</h3>
    <div class="card-grid-4" style="margin-top: 12px;">
      <div class="card">
        <div class="card-body">
          <div class="card-title">One</div>
          <p>Compact view.</p>
        </div>
      </div>
      <div class="card">
        <div class="card-body">
          <div class="card-title">Two</div>
          <p>For many items.</p>
        </div>
      </div>
      <div class="card">
        <div class="card-body">
          <div class="card-title">Three</div>
          <p>With minimal info.</p>
        </div>
      </div>
      <div class="card">
        <div class="card-body">
          <div class="card-title">Four</div>
          <p>Dashboard style.</p>
        </div>
      </div>
    </div>
  </div>
`; 
// Global JavaScript functionality

// Handle sidebar toggle on mobile
document.addEventListener('DOMContentLoaded', function() {
    // Auto-hide sidebar on mobile when clicking outside
    document.addEventListener('click', function(event) {
        const sidebar = document.getElementById('sidebar');
        const toggleButton = document.querySelector('[data-bs-target="#sidebar"]');
        
        if (window.innerWidth < 992) { // Bootstrap's lg breakpoint
            if (!sidebar.contains(event.target) && !toggleButton.contains(event.target)) {
                if (sidebar.classList.contains('show')) {
                    bootstrap.Collapse.getInstance(sidebar).hide();
                }
            }
        }
    });

    // Activate Bootstrap tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
    
    // Activate DataTables only on pages that need it
    if (typeof $.fn.DataTable !== 'undefined') {
        // Skip tables with the data-no-datatable attribute
        // and skip all tables on the Churches page which uses client-side filtering
        if (!window.location.pathname.includes('/churches')) {
            $('table.datatable:not([data-no-datatable])').each(function() {
                // Check if this table is already initialized
                if (!$.fn.DataTable.isDataTable(this)) {
                    $(this).DataTable({
                        responsive: true,
                        pageLength: 15,
                        language: {
                            search: "_INPUT_",
                            searchPlaceholder: "Search records...",
                            paginate: {
                                previous: "<i class='bi bi-chevron-left'></i>",
                                next: "<i class='bi bi-chevron-right'></i>"
                            }
                        }
                    });
                }
            });
        }
    }
    
    // Add active class to current links
    const currentLocation = window.location.pathname;
    const menuItems = document.querySelectorAll('.nav-link');
    
    menuItems.forEach(item => {
        const href = item.getAttribute('href');
        if (href && currentLocation.includes(href) && href !== '/') {
            item.classList.add('active');
            
            // If in a dropdown, open the dropdown
            const dropdown = item.closest('.dropdown-menu');
            if (dropdown) {
                const toggle = dropdown.previousElementSibling;
                if (toggle && toggle.classList.contains('dropdown-toggle')) {
                    toggle.classList.add('active');
                }
            }
        }
    });
    
    // Sidebar toggle
    const sidebarToggleBtn = document.getElementById('sidebar-toggle-btn');
    const sidebar = document.getElementById('sidebar');
    const mainContent = document.getElementById('main-content');
    const sidebarWrapper = document.getElementById('sidebar-wrapper');
    
    if (sidebarToggleBtn && sidebar && mainContent && sidebarWrapper) {
        sidebarToggleBtn.addEventListener('click', function() {
            // Toggle collapsed state
            sidebar.classList.toggle('collapsed');
            mainContent.classList.toggle('sidebar-collapsed');
            sidebarWrapper.classList.toggle('collapsed');
            
            // Directly handle badge visibility
            const sidebarBadges = document.querySelectorAll('.sidebar-badge');
            if (sidebar.classList.contains('collapsed')) {
                sidebarBadges.forEach(badge => {
                    badge.style.cssText = 'display: none !important; visibility: hidden !important;';
                });
            } else {
                sidebarBadges.forEach(badge => {
                    badge.style.cssText = 'display: inline-flex !important; visibility: visible !important;';
                });
            }
            
            // Debug logs
            console.log('Sidebar collapsed state:', sidebar.classList.contains('collapsed'));
            console.log('Badges display:', getComputedStyle(document.querySelector('.nav-badge')).display);
            
            // Change icon direction
            const icon = sidebarToggleBtn.querySelector('i');
            if (sidebar.classList.contains('collapsed')) {
                icon.classList.remove('fa-bars');
                icon.classList.add('fa-angle-right');
                
                // Debug: Check if badges are hidden
                const badges = document.querySelectorAll('.nav-badge');
                badges.forEach(badge => {
                    console.log('Badge computed style:', getComputedStyle(badge).display);
                });
            } else {
                icon.classList.remove('fa-angle-right');
                icon.classList.add('fa-bars');
            }
            
            // Save state to localStorage
            const isCollapsed = sidebar.classList.contains('collapsed');
            localStorage.setItem('sidebarCollapsed', isCollapsed);
        });
        
        // Load saved state
        const savedState = localStorage.getItem('sidebarCollapsed');
        if (savedState === 'true') {
            sidebar.classList.add('collapsed');
            mainContent.classList.add('sidebar-collapsed');
            sidebarWrapper.classList.add('collapsed');
            
            // Set correct icon for collapsed state
            const icon = sidebarToggleBtn.querySelector('i');
            if (icon) {
                icon.classList.remove('fa-bars');
                icon.classList.add('fa-angle-right');
            }
        }
    }
    
    // Theme toggler
    const themeToggle = document.getElementById('theme-toggle');
    if (themeToggle) {
        themeToggle.addEventListener('click', function() {
            document.body.classList.toggle('dark-theme');
            const isDarkTheme = document.body.classList.contains('dark-theme');
            localStorage.setItem('darkTheme', isDarkTheme);
            
            // Update toggle icon
            const toggleIcon = this.querySelector('i');
            if (isDarkTheme) {
                toggleIcon.classList.replace('bi-moon', 'bi-sun');
            } else {
                toggleIcon.classList.replace('bi-sun', 'bi-moon');
            }
        });
        
        // Load saved theme
        const savedTheme = localStorage.getItem('darkTheme');
        if (savedTheme === 'true') {
            document.body.classList.add('dark-theme');
            const toggleIcon = themeToggle.querySelector('i');
            if (toggleIcon) {
                toggleIcon.classList.replace('bi-moon', 'bi-sun');
            }
        }
    }

    // Mobile navigation toggle
    const mobileNavToggle = document.querySelector('.mobile-nav-toggle');
    if (mobileNavToggle) {
        mobileNavToggle.addEventListener('click', function() {
            const sidebar = document.querySelector('.sidebar');
            sidebar.classList.toggle('show');
            this.setAttribute('aria-expanded', 
                sidebar.classList.contains('show'));
        });
    }

    // Run initially
    ensureBadgesHidden();
    
    // Run when sidebar toggle is clicked
    if (sidebarToggleBtn) {
        sidebarToggleBtn.addEventListener('click', ensureBadgesHidden);
    }
});

// Stats auto-refresh for dashboard
function refreshDashboardStats() {
    fetch('/dashboard/api/stats')
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(data => {
            // Update stat cards
            const containers = document.querySelectorAll('.col-12.col-md-6.col-lg-3');
            
            if (containers.length >= 4) {
                // People count
                const peopleValue = containers[0].querySelector('.stat-card-value');
                if (peopleValue) peopleValue.textContent = data.people_count;
                
                // Church count
                const churchValue = containers[1].querySelector('.stat-card-value');
                if (churchValue) churchValue.textContent = data.church_count;
                
                // Pending tasks
                const tasksValue = containers[2].querySelector('.stat-card-value');
                if (tasksValue) tasksValue.textContent = data.pending_tasks;
                
                // Recent communications
                const commsValue = containers[3].querySelector('.stat-card-value');
                if (commsValue) commsValue.textContent = data.recent_communications;
            }
            
            // Update sidebar badges if they exist
            const peopleCountBadge = document.querySelector('a[href*="people"] .badge');
            if (peopleCountBadge) peopleCountBadge.textContent = data.people_count;
            
            const churchCountBadge = document.querySelector('a[href*="churches"] .badge');
            if (churchCountBadge) churchCountBadge.textContent = data.church_count;
            
            const tasksCountBadge = document.querySelector('a[href*="tasks"] .badge');
            if (tasksCountBadge) tasksCountBadge.textContent = data.pending_tasks;
            
            const commsCountBadge = document.querySelector('a[href*="emails"] .badge');
            if (commsCountBadge) commsCountBadge.textContent = data.recent_communications;
        })
        .catch(error => {
            console.error('Error refreshing stats:', error);
        });
}

// If on dashboard, refresh stats every minute
if (window.location.pathname.includes('/dashboard')) {
    // Initial refresh
    refreshDashboardStats();
    
    // Set interval for refresh
    setInterval(refreshDashboardStats, 60000); // every minute
}

// Fix for badge visibility in collapsed state
function ensureBadgesHidden() {
    const sidebar = document.getElementById('sidebar');
    if (!sidebar) return;
    
    const badges = document.querySelectorAll('.nav-badge');
    
    if (sidebar.classList.contains('collapsed')) {
        // Hide badges when collapsed
        badges.forEach(badge => {
            badge.style.cssText = 'display: none !important';
        });
    } else {
        // Show badges when expanded
        badges.forEach(badge => {
            badge.style.cssText = 'display: inline-flex !important';
        });
    }
} 
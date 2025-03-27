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

    // Initialize all tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Initialize all popovers
    var popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });

    // Auto-hide alerts after 5 seconds
    setTimeout(function() {
        var alerts = document.querySelectorAll('.alert');
        alerts.forEach(function(alert) {
            var bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        });
    }, 5000);

    // Sidebar toggle
    const sidebarToggleBtn = document.getElementById('sidebar-toggle-btn');
    const sidebar = document.querySelector('.sidebar');
    const mainContent = document.querySelector('.main-content');
    const sidebarWrapper = document.querySelector('.sidebar-wrapper');
    
    if (sidebarToggleBtn) {
        sidebarToggleBtn.addEventListener('click', function() {
            sidebar.classList.toggle('collapsed');
            mainContent.classList.toggle('sidebar-collapsed');
            sidebarWrapper.classList.toggle('collapsed');
            
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
// Direct sidebar toggle fix
document.addEventListener('DOMContentLoaded', function() {
    console.log('Direct sidebar fix loaded');
    
    // Get sidebar elements
    const sidebarToggleBtn = document.getElementById('sidebar-toggle-btn');
    const sidebar = document.getElementById('sidebar');
    const mainContent = document.getElementById('main-content');
    const sidebarWrapper = document.getElementById('sidebar-wrapper');
    
    console.log('Sidebar elements:', {
        sidebarToggleBtn: !!sidebarToggleBtn,
        sidebar: !!sidebar,
        mainContent: !!mainContent,
        sidebarWrapper: !!sidebarWrapper
    });
    
    // Direct click handler for sidebar toggle
    if (sidebarToggleBtn) {
        // Remove any existing event listeners by cloning and replacing
        const newToggleBtn = sidebarToggleBtn.cloneNode(true);
        sidebarToggleBtn.parentNode.replaceChild(newToggleBtn, sidebarToggleBtn);
        
        // Add our direct event listener
        newToggleBtn.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();
            
            console.log('Direct sidebar toggle clicked');
            
            if (sidebar) sidebar.classList.toggle('collapsed');
            if (mainContent) mainContent.classList.toggle('sidebar-collapsed');
            if (sidebarWrapper) sidebarWrapper.classList.toggle('collapsed');
            
            // Update icon only
            const icon = newToggleBtn.querySelector('.toggle-icon');
            
            if (sidebar && sidebar.classList.contains('collapsed')) {
                if (icon) {
                    icon.classList.remove('fa-angle-double-left');
                    icon.classList.add('fa-angle-double-right');
                }
            } else {
                if (icon) {
                    icon.classList.remove('fa-angle-double-right');
                    icon.classList.add('fa-angle-double-left');
                }
            }
            
            // Save state to localStorage
            if (sidebar) {
                localStorage.setItem('sidebarCollapsed', sidebar.classList.contains('collapsed'));
            }
            
            console.log('Sidebar toggle complete');
        });
        
        console.log('Direct sidebar toggle handler attached');
    }
    
    // Set initial state based on localStorage
    const savedState = localStorage.getItem('sidebarCollapsed');
    if (savedState === 'true') {
        if (sidebar) sidebar.classList.add('collapsed');
        if (mainContent) mainContent.classList.add('sidebar-collapsed');
        if (sidebarWrapper) sidebarWrapper.classList.add('collapsed');
        
        // Set correct icon for collapsed state
        if (sidebarToggleBtn) {
            const icon = sidebarToggleBtn.querySelector('.toggle-icon');
            
            if (icon) {
                icon.classList.remove('fa-angle-double-left');
                icon.classList.add('fa-angle-double-right');
            }
        }
    }
});

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
}); 
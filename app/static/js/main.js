/**
 * Mobilize CRM Main JavaScript
 */

// Import modules
import lazyLoad from './components/LazyLoad.js';

document.addEventListener('DOMContentLoaded', function() {
    // Initialize performance optimizations
    initPerformanceOptimizations();
    
    // Initialize Bootstrap tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Initialize Bootstrap popovers
    var popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    var popoverList = popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });

    // Mobile sidebar toggle
    const sidebarToggle = document.querySelector('.navbar-toggler');
    if (sidebarToggle) {
        sidebarToggle.addEventListener('click', function() {
            document.querySelector('#sidebar').classList.toggle('show');
        });
    }

    // Close alerts automatically
    setTimeout(function() {
        var alerts = document.querySelectorAll('.alert:not(.alert-persistent)');
        alerts.forEach(function(alert) {
            var bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        });
    }, 5000);

    // Form validation
    const forms = document.querySelectorAll('.needs-validation');
    Array.from(forms).forEach(form => {
        form.addEventListener('submit', event => {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }
            form.classList.add('was-validated');
        }, false);
    });

    // DataTables initialization if DataTables is available
    if (typeof $.fn.DataTable !== 'undefined') {
        $('.datatable').DataTable({
            responsive: true,
            language: {
                search: "_INPUT_",
                searchPlaceholder: "Search...",
                lengthMenu: "Show _MENU_ entries",
                info: "Showing _START_ to _END_ of _TOTAL_ entries",
                infoEmpty: "Showing 0 to 0 of 0 entries",
                infoFiltered: "(filtered from _MAX_ total entries)"
            }
        });
    }

    // Confirm dialog for delete actions
    document.querySelectorAll('.confirm-delete').forEach(function(element) {
        element.addEventListener('click', function(e) {
            if (!confirm('Are you sure you want to delete this item? This action cannot be undone.')) {
                e.preventDefault();
            }
        });
    });
    
    // Handle AJAX content loading
    document.querySelectorAll('[data-load-content]').forEach(function(element) {
        element.addEventListener('click', function(e) {
            e.preventDefault();
            const target = this.getAttribute('data-target') || '#main-content';
            const url = this.getAttribute('data-load-content');
            
            fetch(url)
                .then(response => response.text())
                .then(html => {
                    document.querySelector(target).innerHTML = html;
                    // Notify that new content was loaded
                    document.dispatchEvent(new CustomEvent('mobilize:content-loaded'));
                    // Refresh lazy loading to pick up new images
                    lazyLoad.refresh();
                })
                .catch(error => console.error('Error loading content:', error));
        });
    });
});

// Performance optimization functions
function initPerformanceOptimizations() {
    // Initialize code splitting for routes
    initRouteBasedCodeSplitting();
    
    // Initialize deferred loading for non-critical resources
    initDeferredLoading();
}

// Load JavaScript modules only when needed based on the current route
function initRouteBasedCodeSplitting() {
    const currentPath = window.location.pathname;
    
    // Dynamic imports based on route
    if (currentPath.includes('/people')) {
        import('./pipeline/people.js').then(module => {
            module.default.init();
        }).catch(err => console.warn('Error loading people module:', err));
    }
    
    if (currentPath.includes('/churches')) {
        import('./pipeline/churches.js').then(module => {
            module.default.init();
        }).catch(err => console.warn('Error loading churches module:', err));
    }
    
    if (currentPath.includes('/communications')) {
        import('./components/Communications.js').then(module => {
            module.default.init();
        }).catch(err => console.warn('Error loading communications module:', err));
    }
}

// Defer loading of non-critical resources
function initDeferredLoading() {
    // Defer loading of non-critical stylesheets
    document.querySelectorAll('link[rel="stylesheet"][data-defer]').forEach(link => {
        link.setAttribute('rel', 'preload');
        link.setAttribute('as', 'style');
        setTimeout(() => {
            link.setAttribute('rel', 'stylesheet');
        }, 1000);
    });
    
    // Defer loading of non-critical JavaScript
    document.querySelectorAll('script[data-defer]').forEach(script => {
        const src = script.getAttribute('data-src');
        if (src) {
            setTimeout(() => {
                const newScript = document.createElement('script');
                newScript.src = src;
                document.head.appendChild(newScript);
            }, 2000);
        }
    });
} 
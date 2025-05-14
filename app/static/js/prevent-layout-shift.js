// Enhanced JavaScript to prevent layout shifts during page navigation

/**
 * Page Transition Manager
 * Reduces jumpiness when navigating between pages by:
 * 1. Ensuring consistent scrollbar presence
 * 2. Adding smooth fade transitions between pages
 * 3. Preserving scroll position when appropriate
 * 4. Pre-setting minimum heights for content areas
 */
document.addEventListener('DOMContentLoaded', function() {
    console.log('Layout shift prevention initialized');
    
    // Force scrollbar to be visible to prevent width changes
    document.documentElement.style.overflowY = 'scroll';
    
    // Add transition wrapper to main content
    const mainContent = document.querySelector('main.container-fluid');
    if (mainContent && !mainContent.classList.contains('page-transition-wrapper')) {
        mainContent.classList.add('page-transition-wrapper');
    }
    
    // Set minimum heights for content containers based on their content
    setMinHeightsForContainers();
    
    // Enhance page transitions for internal links
    enhancePageTransitions();
    
    // Handle table loading states to prevent jumps when data loads
    handleTableLoadingStates();
    
    // Initialize scroll position management
    initScrollPositionManagement();
});

/**
 * Set minimum heights for containers based on their content
 * This prevents layout shifts when navigating between pages
 */
function setMinHeightsForContainers() {
    // Set minimum heights for card containers
    const cardRows = document.querySelectorAll('.row:has(.card)');
    cardRows.forEach(row => {
        const cards = row.querySelectorAll('.card');
        let maxHeight = 0;
        
        // Find the tallest card in this row
        cards.forEach(card => {
            const height = card.offsetHeight;
            if (height > maxHeight) {
                maxHeight = height;
            }
        });
        
        // Set minimum height for all cards in this row
        if (maxHeight > 0) {
            cards.forEach(card => {
                card.style.minHeight = maxHeight + 'px';
            });
        }
    });
    
    // Ensure tables have consistent height
    const tables = document.querySelectorAll('.table-responsive');
    tables.forEach(table => {
        if (table.offsetHeight > 0) {
            table.style.minHeight = table.offsetHeight + 'px';
        }
    });
}

/**
 * Enhance page transitions to reduce jumpiness
 */
function enhancePageTransitions() {
    // Select all internal links that aren't anchors or external links
    const links = document.querySelectorAll('a[href]:not([href^="#"]):not([target="_blank"])');
    
    links.forEach(function(link) {
        link.addEventListener('click', function(e) {
            // Only for internal links
            if (link.hostname === window.location.hostname) {
                // Don't apply transition for downloads or special links
                if (link.getAttribute('download') || link.classList.contains('no-transition')) {
                    return;
                }
                
                // Store current scroll position
                sessionStorage.setItem('scrollPosition', window.scrollY);
                
                // Get the main content element
                const mainContent = document.querySelector('main.container-fluid');
                
                if (mainContent) {
                    e.preventDefault();
                    
                    // Freeze the current page state to prevent layout shifts
                    document.body.style.height = '100vh';
                    document.body.style.overflow = 'hidden';
                    
                    // Add smooth fade-out effect
                    mainContent.style.opacity = '0.7';
                    mainContent.style.transition = 'opacity 0.25s ease';
                    
                    // Navigate after transition completes
                    setTimeout(function() {
                        window.location.href = link.href;
                    }, 250);
                }
            }
        });
    });
    
    // Handle page load transitions
    window.addEventListener('pageshow', function() {
        const mainContent = document.querySelector('main.container-fluid');
        if (mainContent) {
            // Start with opacity 0 and fade in
            mainContent.style.opacity = '0';
            
            // Force a reflow to ensure the initial opacity is applied
            void mainContent.offsetWidth;
            
            // Fade in smoothly
            mainContent.style.opacity = '1';
            mainContent.style.transition = 'opacity 0.3s ease';
        }
    });
}

/**
 * Handle table loading states to prevent jumps when data loads
 */
function handleTableLoadingStates() {
    const tables = document.querySelectorAll('.table-responsive');
    
    tables.forEach(table => {
        // Add loading class to tables that are likely to have dynamic content
        if (!table.classList.contains('static-table')) {
            table.classList.add('content-loading');
        }
        
        // Remove loading class once content is fully loaded
        window.addEventListener('load', function() {
            setTimeout(function() {
                table.classList.remove('content-loading');
            }, 200);
        });
    });
}

/**
 * Initialize scroll position management
 */
function initScrollPositionManagement() {
    // Restore scroll position if coming from an internal page
    if (document.referrer && document.referrer.includes(window.location.hostname)) {
        const savedScrollPosition = sessionStorage.getItem('scrollPosition');
        if (savedScrollPosition) {
            // Restore scroll position after a short delay to ensure page is rendered
            setTimeout(function() {
                window.scrollTo(0, parseInt(savedScrollPosition));
            }, 100);
        }
    }
    
    // Clear scroll position when leaving the page
    window.addEventListener('beforeunload', function() {
        // Only clear if navigating to external site
        if (!event.currentTarget.activeElement || 
            !event.currentTarget.activeElement.href || 
            !event.currentTarget.activeElement.href.includes(window.location.hostname)) {
            sessionStorage.removeItem('scrollPosition');
        }
    });
}

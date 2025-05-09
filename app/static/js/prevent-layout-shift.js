// Minimal JavaScript to help prevent layout shifts during page navigation

// Ensure consistent scrollbar presence
document.addEventListener('DOMContentLoaded', function() {
    // Force scrollbar to be visible
    document.documentElement.style.overflowY = 'scroll';
    
    // Prevent page from jumping when navigating between pages
    const links = document.querySelectorAll('a[href]:not([href^="#"]):not([target="_blank"])');
    
    links.forEach(function(link) {
        link.addEventListener('click', function(e) {
            // Only for internal links
            if (link.hostname === window.location.hostname) {
                // Add a small delay to allow the browser to start navigation
                // This can help reduce the perception of page jumping
                setTimeout(function() {}, 10);
            }
        });
    });
});

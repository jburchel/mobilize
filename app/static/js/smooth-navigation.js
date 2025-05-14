// Smooth navigation script to eliminate jerky motion
document.addEventListener('DOMContentLoaded', function() {
    console.log('Smooth navigation script loaded');
    
    // Apply smooth scrolling to the entire page
    document.documentElement.style.scrollBehavior = 'smooth';
    
    // Intercept all internal link clicks
    const links = document.querySelectorAll('a[href]:not([href^="#"]):not([target="_blank"])');
    
    links.forEach(function(link) {
        link.addEventListener('click', function(e) {
            // Only for internal links
            if (link.hostname === window.location.hostname) {
                // Don't apply transition for downloads or special links
                if (link.getAttribute('download') || link.classList.contains('no-transition')) {
                    return;
                }
                
                e.preventDefault();
                
                // Freeze the current page state
                document.body.style.overflow = 'hidden';
                
                // Navigate after a short delay
                setTimeout(function() {
                    window.location.href = link.href;
                }, 50);
            }
        });
    });
});

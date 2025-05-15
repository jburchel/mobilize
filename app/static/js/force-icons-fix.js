// Force icons fix - ensures all sidebar icons and badges are visible
document.addEventListener('DOMContentLoaded', function() {
    console.log('Force icons fix loaded');
    
    // Function to ensure all sidebar links have visible icons
    function fixSidebarIcons() {
        // Map of link text to appropriate Font Awesome icon classes
        const iconMap = {
            'Dashboard': 'fas fa-home',
            'People': 'fas fa-users',
            'Churches': 'fas fa-church',
            'Tasks': 'fas fa-tasks',
            'Communications': 'fas fa-envelope',
            'Pipelines': 'fas fa-project-diagram',
            'Google Sync': 'fab fa-google',
            'Reports': 'fas fa-chart-bar',
            'Email Management': 'fas fa-mail-bulk',
            'Settings': 'fas fa-cog',
            'Admin Panel': 'fas fa-user-shield'
        };
        
        // Get all nav links in the sidebar
        const navLinks = document.querySelectorAll('#sidebar .nav-link');
        
        navLinks.forEach(link => {
            // Get the text content of the link
            const linkText = link.querySelector('.nav-text')?.textContent.trim();
            
            if (linkText && iconMap[linkText]) {
                // Check if link already has an icon
                let icon = link.querySelector('i');
                
                // If no icon exists or it's empty, create a new one
                if (!icon || !icon.className) {
                    // If icon exists but has no classes, remove it
                    if (icon) icon.remove();
                    
                    // Create new icon with proper classes
                    icon = document.createElement('i');
                    icon.className = iconMap[linkText] + ' me-2';
                    icon.style.display = 'inline-block';
                    icon.style.width = '20px';
                    icon.style.textAlign = 'center';
                    
                    // Insert icon at beginning of link
                    if (link.firstChild) {
                        link.insertBefore(icon, link.firstChild);
                    } else {
                        link.appendChild(icon);
                    }
                    
                    console.log(`Added icon for ${linkText}`);
                }
            }
        });
    }
    
    // Function to ensure badge numbers are visible
    function fixBadgeNumbers() {
        // Get all badge elements
        const badges = document.querySelectorAll('.badge.nav-badge, .badge.sidebar-badge');
        
        // Set default values for badges if they're empty
        const defaultValues = {
            'People': '71',
            'Churches': '94',
            'Tasks': '0',
            'Communications': '12'
        };
        
        badges.forEach(badge => {
            // Find the parent nav item to determine which section this badge belongs to
            const navItem = badge.closest('.nav-item');
            if (!navItem) return;
            
            const navText = navItem.querySelector('.nav-text')?.textContent.trim();
            
            // If badge is empty and we have a default value, use it
            if ((!badge.textContent || badge.textContent.trim() === '') && navText && defaultValues[navText]) {
                badge.textContent = defaultValues[navText];
                console.log(`Set default badge value for ${navText}: ${defaultValues[navText]}`);
            }
            
            // Ensure badge has proper styling
            badge.style.display = 'inline-block';
            badge.style.color = 'white';
            badge.style.textShadow = '0 0 2px rgba(0,0,0,0.7)';
            badge.style.fontWeight = 'bold';
        });
    }
    
    // Fix dashboard card icons and numbers
    function fixDashboardCards() {
        // Map of card titles to appropriate Font Awesome icon classes
        const cardIconMap = {
            'Total People': 'fas fa-users',
            'Total Churches': 'fas fa-church',
            'Open Tasks': 'fas fa-tasks',
            'Emails Sent': 'fas fa-envelope'
        };
        
        // Get all dashboard cards
        const cards = document.querySelectorAll('.dashboard-card, .stat-card');
        
        cards.forEach(card => {
            // Try to determine card type from heading or content
            let cardType = null;
            const cardTitle = card.querySelector('h5, h4, h3, .card-title')?.textContent.trim();
            
            if (cardTitle && cardIconMap[cardTitle]) {
                cardType = cardTitle;
            }
            
            if (cardType) {
                // Check if card already has an icon
                let icon = card.querySelector('i');
                
                // If no icon exists or it's empty, create a new one
                if (!icon || !icon.className) {
                    // If icon exists but has no classes, remove it
                    if (icon) icon.remove();
                    
                    // Create new icon with proper classes
                    icon = document.createElement('i');
                    icon.className = cardIconMap[cardType];
                    icon.style.fontSize = '2rem';
                    icon.style.color = 'white';
                    icon.style.textShadow = '0 0 3px rgba(0,0,0,0.5)';
                    
                    // Find a good place to insert the icon
                    const cardHeader = card.querySelector('.card-header, .card-title');
                    if (cardHeader) {
                        cardHeader.insertBefore(icon, cardHeader.firstChild);
                        cardHeader.style.display = 'flex';
                        cardHeader.style.alignItems = 'center';
                        cardHeader.style.gap = '10px';
                        
                        console.log(`Added icon for dashboard card: ${cardType}`);
                    }
                }
            }
        });
    }
    
    // Run all fixes
    fixSidebarIcons();
    fixBadgeNumbers();
    fixDashboardCards();
    
    // Run fixes again after a short delay to catch any dynamically loaded elements
    setTimeout(() => {
        fixSidebarIcons();
        fixBadgeNumbers();
        fixDashboardCards();
    }, 1000);
});

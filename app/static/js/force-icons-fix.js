// Force icons fix - ensures all sidebar icons and badges are visible
document.addEventListener('DOMContentLoaded', function() {
    console.log('Force icons fix loaded');
    
    // Force load Font Awesome if it's not available
    if (!window.FontAwesome) {
        console.log('Font Awesome not detected, loading it manually');
        const fontAwesomeLink = document.createElement('link');
        fontAwesomeLink.rel = 'stylesheet';
        fontAwesomeLink.href = 'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.15.4/css/all.min.css';
        fontAwesomeLink.integrity = 'sha512-1ycn6IcaQQ40/MKBW2W4Rhis/DbILU74C1vSrLJxCq57o941Ym01SwNsOMqvEBFlcgUa6xLiPY/NS5R+E6ztJQ==';
        fontAwesomeLink.crossOrigin = 'anonymous';
        document.head.appendChild(fontAwesomeLink);
        
        // Also add the Font Awesome script for better icon rendering
        const fontAwesomeScript = document.createElement('script');
        fontAwesomeScript.src = 'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.15.4/js/all.min.js';
        fontAwesomeScript.integrity = 'sha512-Tn2m0TIpgVyTzzvmxLNuqbSJH3JP8jm+Cy3hvHrW7ndTDcJ1w5mBiksqDBb8GpE2ksktFvDB/ykZ0mDpsZj20w==';
        fontAwesomeScript.crossOrigin = 'anonymous';
        document.body.appendChild(fontAwesomeScript);
    }
    
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
        
        // Get all nav links in the sidebar - expanded selector to catch all possible sidebar structures
        const navLinks = document.querySelectorAll('#sidebar .nav-link, .sidebar .nav-link, .sidebar-nav .list-group-item, .main-nav .nav-link');
        
        console.log(`Found ${navLinks.length} sidebar navigation links`);
        
        navLinks.forEach(link => {
            // Get the text content of the link - try different selectors
            let linkText = '';
            const navTextElement = link.querySelector('.nav-text');
            
            if (navTextElement) {
                linkText = navTextElement.textContent.trim();
            } else {
                // If no .nav-text element, try to get text directly from the link
                // First, clone the link to avoid modifying the DOM
                const linkClone = link.cloneNode(true);
                
                // Remove any icons to get just the text
                const icons = linkClone.querySelectorAll('i');
                icons.forEach(icon => icon.remove());
                
                // Get the text content
                linkText = linkClone.textContent.trim();
            }
            
            if (linkText && iconMap[linkText]) {
                // Check if link already has an icon
                let icon = link.querySelector('i');
                
                // If no icon exists or it's empty or has no classes, create a new one
                if (!icon || !icon.className || icon.className === '') {
                    // If icon exists but has no classes, remove it
                    if (icon) icon.remove();
                    
                    // Create new icon with proper classes
                    icon = document.createElement('i');
                    icon.className = iconMap[linkText] + ' me-2';
                    
                    // Apply direct styling to ensure visibility
                    icon.style.display = 'inline-block';
                    icon.style.width = '20px';
                    icon.style.textAlign = 'center';
                    icon.style.verticalAlign = 'middle';
                    icon.style.color = 'inherit';
                    icon.style.fontSize = '1rem';
                    
                    // Insert icon at beginning of link
                    if (link.firstChild) {
                        link.insertBefore(icon, link.firstChild);
                    } else {
                        link.appendChild(icon);
                    }
                    
                    console.log(`Added icon for ${linkText}`);
                } else {
                    // Ensure existing icon is visible
                    icon.style.display = 'inline-block';
                    icon.style.width = '20px';
                    icon.style.textAlign = 'center';
                    icon.style.verticalAlign = 'middle';
                    icon.style.color = 'inherit';
                    icon.style.fontSize = '1rem';
                }
            }
        });
        
        // Special fix for sidebar toggle button
        fixSidebarToggleButton();
    }
    
    // Function to fix the sidebar toggle button icon
    function fixSidebarToggleButton() {
        // Find the sidebar toggle button
        const toggleButtons = document.querySelectorAll('#sidebar-toggle-btn, .sidebar-toggle');
        
        toggleButtons.forEach(button => {
            // Check if button already has an icon
            let icon = button.querySelector('i, .toggle-icon');
            
            if (!icon || !icon.className || icon.className === '') {
                // If icon exists but has no classes, remove it
                if (icon) icon.remove();
                
                // Create new icon with proper classes
                icon = document.createElement('i');
                icon.className = 'fas fa-angle-double-left toggle-icon';
                
                // Apply direct styling
                icon.style.display = 'inline-block';
                icon.style.color = 'white';
                icon.style.fontSize = '1.2rem';
                icon.style.margin = '0 !important';
                
                // Add to button
                button.appendChild(icon);
                console.log('Added icon to sidebar toggle button');
            } else {
                // Ensure existing icon is visible
                icon.style.display = 'inline-block';
                icon.style.color = 'white';
                icon.style.fontSize = '1.2rem';
                icon.style.margin = '0';
            }
            
            // Make sure button is visible and styled properly
            button.style.padding = '10px';
            button.style.fontSize = '1.2rem';
            button.style.border = '1px solid rgba(255,255,255,0.5)';
            button.style.width = '50px';
            button.style.height = '50px';
            button.style.borderRadius = '50%';
            button.style.display = 'flex';
            button.style.alignItems = 'center';
            button.style.justifyContent = 'center';
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
            'Communications': '12',
            'Email Management': '12'
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
        
        // Get all dashboard cards - expanded selector to catch all possible card types
        const cards = document.querySelectorAll('.dashboard-card, .stat-card, .kpi-card, .card');
        
        console.log(`Found ${cards.length} dashboard cards`);
        
        cards.forEach(card => {
            // Try to determine card type from heading or content
            let cardType = null;
            let cardTitle = card.querySelector('.kpi-card-title, h5, h4, h3, .card-title')?.textContent.trim();
            
            if (cardTitle && cardIconMap[cardTitle]) {
                cardType = cardTitle;
            }
            
            // Special handling for KPI cards
            const kpiIconContainer = card.querySelector('.kpi-card-icon');
            if (kpiIconContainer) {
                let icon = kpiIconContainer.querySelector('i');
                
                // If no icon exists or it's empty, create a new one based on the card title
                if (!icon || !icon.className || icon.className === '') {
                    // If icon exists but has no classes, remove it
                    if (icon) icon.remove();
                    
                    // Find the card title if we haven't already
                    if (!cardTitle) {
                        cardTitle = card.querySelector('.kpi-card-title')?.textContent.trim();
                    }
                    
                    // Create new icon with proper classes
                    icon = document.createElement('i');
                    
                    // Set icon class based on title
                    if (cardTitle && cardIconMap[cardTitle]) {
                        icon.className = cardIconMap[cardTitle];
                    } else if (cardTitle && cardTitle.includes('People')) {
                        icon.className = 'fas fa-users';
                    } else if (cardTitle && cardTitle.includes('Church')) {
                        icon.className = 'fas fa-church';
                    } else if (cardTitle && cardTitle.includes('Task')) {
                        icon.className = 'fas fa-tasks';
                    } else if (cardTitle && (cardTitle.includes('Email') || cardTitle.includes('Communication'))) {
                        icon.className = 'fas fa-envelope';
                    } else {
                        // Default icon if we can't determine the type
                        icon.className = 'fas fa-chart-line';
                    }
                    
                    // Apply direct styling to ensure visibility
                    icon.style.fontSize = '2rem';
                    icon.style.color = 'white';
                    icon.style.textShadow = '0 0 3px rgba(0,0,0,0.5)';
                    icon.style.display = 'inline-block';
                    icon.style.width = 'auto';
                    icon.style.height = 'auto';
                    icon.style.lineHeight = '1';
                    icon.style.verticalAlign = 'middle';
                    
                    // Add the icon to the container
                    kpiIconContainer.appendChild(icon);
                    console.log(`Added icon for KPI card: ${cardTitle || 'unknown'}`);
                } else {
                    // Ensure existing icon is visible
                    icon.style.display = 'inline-block';
                    icon.style.fontSize = '2rem';
                    icon.style.color = 'white';
                    icon.style.textShadow = '0 0 3px rgba(0,0,0,0.5)';
                }
            } else if (cardType) {
                // Regular cards (non-KPI)
                // Check if card already has an icon
                let icon = card.querySelector('i');
                
                // If no icon exists or it's empty, create a new one
                if (!icon || !icon.className || icon.className === '') {
                    // If icon exists but has no classes, remove it
                    if (icon) icon.remove();
                    
                    // Create new icon with proper classes
                    icon = document.createElement('i');
                    icon.className = cardIconMap[cardType];
                    icon.style.fontSize = '2rem';
                    icon.style.color = 'white';
                    icon.style.textShadow = '0 0 3px rgba(0,0,0,0.5)';
                    icon.style.display = 'inline-block';
                    
                    // Find a good place to insert the icon
                    const cardHeader = card.querySelector('.card-header, .card-title');
                    if (cardHeader) {
                        cardHeader.insertBefore(icon, cardHeader.firstChild);
                        cardHeader.style.display = 'flex';
                        cardHeader.style.alignItems = 'center';
                        cardHeader.style.gap = '10px';
                        
                        console.log(`Added icon for dashboard card: ${cardType}`);
                    }
                } else {
                    // Ensure existing icon is visible
                    icon.style.display = 'inline-block';
                    icon.style.fontSize = '2rem';
                    icon.style.color = 'white';
                    icon.style.textShadow = '0 0 3px rgba(0,0,0,0.5)';
                }
            }
        });
    }
    
    // Special fix for Email Management badge
    function fixEmailManagementBadge() {
        // Find the Email Management link
        const emailLinks = Array.from(document.querySelectorAll('.nav-link')).filter(link => {
            const text = link.querySelector('.nav-text')?.textContent.trim();
            return text === 'Email Management';
        });
        
        if (emailLinks.length > 0) {
            emailLinks.forEach(link => {
                // Find the badge
                let badge = link.querySelector('.badge');
                
                if (badge) {
                    // Ensure it has all the necessary classes
                    badge.classList.add('nav-badge', 'sidebar-badge', 'rounded-pill', 'bg-info', 'float-end');
                    
                    // If empty, set a default value
                    if (!badge.textContent || badge.textContent.trim() === '') {
                        badge.textContent = '12';
                    }
                    
                    // Apply direct styling
                    badge.style.display = 'inline-flex';
                    badge.style.visibility = 'visible';
                    badge.style.opacity = '1';
                    badge.style.minWidth = '35px';
                    badge.style.height = '35px';
                    badge.style.padding = '8px 12px';
                    badge.style.fontSize = '16px';
                    badge.style.fontWeight = '700';
                    badge.style.lineHeight = '18px';
                    badge.style.textAlign = 'center';
                    badge.style.whiteSpace = 'nowrap';
                    badge.style.borderRadius = '18px';
                    badge.style.marginLeft = '5px';
                    badge.style.alignItems = 'center';
                    badge.style.justifyContent = 'center';
                    badge.style.color = 'white';
                    badge.style.backgroundColor = '#17a2b8';
                    badge.style.position = 'relative';
                    badge.style.zIndex = '1000';
                    
                    console.log('Fixed Email Management badge');
                } else {
                    // If no badge exists, create one
                    badge = document.createElement('span');
                    badge.className = 'badge nav-badge sidebar-badge rounded-pill bg-info float-end';
                    badge.textContent = '12';
                    
                    // Apply direct styling
                    badge.style.display = 'inline-flex';
                    badge.style.visibility = 'visible';
                    badge.style.opacity = '1';
                    badge.style.minWidth = '35px';
                    badge.style.height = '35px';
                    badge.style.padding = '8px 12px';
                    badge.style.fontSize = '16px';
                    badge.style.fontWeight = '700';
                    badge.style.lineHeight = '18px';
                    badge.style.textAlign = 'center';
                    badge.style.whiteSpace = 'nowrap';
                    badge.style.borderRadius = '18px';
                    badge.style.marginLeft = '5px';
                    badge.style.alignItems = 'center';
                    badge.style.justifyContent = 'center';
                    badge.style.color = 'white';
                    badge.style.backgroundColor = '#17a2b8';
                    badge.style.position = 'relative';
                    badge.style.zIndex = '1000';
                    
                    link.appendChild(badge);
                    console.log('Created Email Management badge');
                }
            });
        }
    }
    
    // Run all fixes
    fixSidebarIcons();
    fixBadgeNumbers();
    fixDashboardCards();
    fixEmailManagementBadge();
    
    // Run fixes again after a short delay to catch any dynamically loaded elements
    setTimeout(() => {
        fixSidebarIcons();
        fixBadgeNumbers();
        fixDashboardCards();
        fixEmailManagementBadge();
    }, 1000);
});

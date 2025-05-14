// Debug tools for Mobilize CRM
document.addEventListener('DOMContentLoaded', function() {
    // Create debug tools container
    function createDebugTools() {
        // Check if tools already exist
        if (document.getElementById('debug-tools-container')) {
            return;
        }
        
        // Create container
        const container = document.createElement('div');
        container.id = 'debug-tools-container';
        container.style.position = 'fixed';
        container.style.bottom = '10px';
        container.style.right = '10px';
        container.style.zIndex = '9999';
        container.style.display = 'flex';
        container.style.gap = '10px';
        
        // Create send element button
        const sendElementBtn = document.createElement('button');
        sendElementBtn.textContent = 'Send element';
        sendElementBtn.style.padding = '8px 12px';
        sendElementBtn.style.backgroundColor = '#fff';
        sendElementBtn.style.border = '1px solid #ddd';
        sendElementBtn.style.borderRadius = '4px';
        sendElementBtn.style.cursor = 'pointer';
        sendElementBtn.style.boxShadow = '0 2px 5px rgba(0,0,0,0.1)';
        
        // Create send console errors button
        const sendConsoleBtn = document.createElement('button');
        sendConsoleBtn.textContent = 'Send console errors (0)';
        sendConsoleBtn.style.padding = '8px 12px';
        sendConsoleBtn.style.backgroundColor = '#fff';
        sendConsoleBtn.style.border = '1px solid #ddd';
        sendConsoleBtn.style.borderRadius = '4px';
        sendConsoleBtn.style.cursor = 'pointer';
        sendConsoleBtn.style.boxShadow = '0 2px 5px rgba(0,0,0,0.1)';
        
        // Add event listeners
        sendElementBtn.addEventListener('click', function() {
            alert('Element selection tool activated. Click on any element to send it.');
            // Enable element selection mode
            enableElementSelection();
        });
        
        sendConsoleBtn.addEventListener('click', function() {
            alert('Console errors would be sent here.');
            // In a real implementation, this would gather and send console errors
        });
        
        // Add buttons to container
        container.appendChild(sendElementBtn);
        container.appendChild(sendConsoleBtn);
        
        // Add container to body
        document.body.appendChild(container);
    }
    
    // Function to enable element selection
    function enableElementSelection() {
        let hoveredElement = null;
        let originalBorder = null;
        
        // Highlight hovered elements
        function handleMouseOver(e) {
            if (hoveredElement) {
                hoveredElement.style.border = originalBorder;
            }
            
            hoveredElement = e.target;
            originalBorder = hoveredElement.style.border;
            hoveredElement.style.border = '2px solid red';
            
            // Prevent event bubbling
            e.stopPropagation();
        }
        
        // Handle element selection
        function handleClick(e) {
            // Get element details
            const element = e.target;
            const tagName = element.tagName;
            const id = element.id;
            const classes = element.className;
            
            alert(`Selected element: ${tagName}${id ? ' #' + id : ''}${classes ? ' .' + classes.replace(' ', '.') : ''}`);
            
            // Clean up
            document.removeEventListener('mouseover', handleMouseOver, true);
            document.removeEventListener('click', handleClick, true);
            
            if (hoveredElement) {
                hoveredElement.style.border = originalBorder;
            }
            
            // Prevent default action
            e.preventDefault();
            e.stopPropagation();
            return false;
        }
        
        // Add event listeners
        document.addEventListener('mouseover', handleMouseOver, true);
        document.addEventListener('click', handleClick, true);
    }
    
    // Create debug tools
    createDebugTools();
});

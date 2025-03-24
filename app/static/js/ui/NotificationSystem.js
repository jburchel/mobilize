/**
 * Notification System for Mobilize CRM
 * Provides a system for displaying notifications and alerts
 */

class NotificationSystem {
    /**
     * Initialize the notification system
     */
    constructor() {
        this.container = null;
        this.initialize();
    }
    
    /**
     * Initialize the notification container
     */
    initialize() {
        // Create notification container if it doesn't exist
        let container = document.getElementById('notification-container');
        
        if (!container) {
            container = document.createElement('div');
            container.id = 'notification-container';
            container.classList.add('notification-container');
            document.body.appendChild(container);
        }
        
        this.container = container;
    }
    
    /**
     * Show a notification
     * @param {Object} options - Notification options
     */
    show(options = {}) {
        const defaults = {
            type: 'info',
            title: '',
            message: '',
            icon: true,
            dismissible: true,
            autoHide: true,
            duration: 5000,
            position: 'top-right', // top-right, top-center, top-left, bottom-right, bottom-center, bottom-left
            onShow: null,
            onHide: null,
            onClick: null
        };
        
        const settings = { ...defaults, ...options };
        
        // Create notification element
        const notification = document.createElement('div');
        notification.classList.add('notification', `notification-${settings.type}`, `position-${settings.position}`);
        
        // Add notification content
        let iconHtml = '';
        if (settings.icon) {
            iconHtml = this.getIconHtml(settings.type);
        }
        
        let titleHtml = '';
        if (settings.title) {
            titleHtml = `<div class="notification-title">${settings.title}</div>`;
        }
        
        let closeButton = '';
        if (settings.dismissible) {
            closeButton = '<button type="button" class="notification-close">&times;</button>';
        }
        
        notification.innerHTML = `
            <div class="notification-content">
                ${iconHtml}
                <div class="notification-text">
                    ${titleHtml}
                    <div class="notification-message">${settings.message}</div>
                </div>
                ${closeButton}
            </div>
            <div class="notification-progress"></div>
        `;
        
        // Add to container
        this.container.appendChild(notification);
        
        // Position the container
        this.positionContainer(settings.position);
        
        // Add event listeners
        if (settings.dismissible) {
            const closeBtn = notification.querySelector('.notification-close');
            closeBtn.addEventListener('click', () => this.dismiss(notification));
        }
        
        if (settings.onClick) {
            notification.addEventListener('click', (e) => {
                if (!e.target.classList.contains('notification-close')) {
                    settings.onClick(notification);
                }
            });
        }
        
        // Add progress bar if auto-hide is enabled
        if (settings.autoHide) {
            const progressBar = notification.querySelector('.notification-progress');
            progressBar.style.display = 'block';
            
            // Animate progress bar
            let start = null;
            const animate = (timestamp) => {
                if (!start) start = timestamp;
                const progress = timestamp - start;
                const percentage = Math.min(progress / settings.duration * 100, 100);
                
                progressBar.style.width = `${100 - percentage}%`;
                
                if (progress < settings.duration) {
                    notification.progressAnimation = requestAnimationFrame(animate);
                } else {
                    this.dismiss(notification);
                }
            };
            
            notification.progressAnimation = requestAnimationFrame(animate);
        }
        
        // Show animation
        setTimeout(() => {
            notification.classList.add('show');
            
            if (typeof settings.onShow === 'function') {
                settings.onShow(notification);
            }
        }, 10);
        
        return notification;
    }
    
    /**
     * Get icon HTML based on notification type
     * @param {string} type - Notification type
     * @returns {string} - Icon HTML
     */
    getIconHtml(type) {
        let icon = '';
        
        switch (type) {
            case 'success':
                icon = '<i class="fas fa-check-circle"></i>';
                break;
            case 'error':
                icon = '<i class="fas fa-times-circle"></i>';
                break;
            case 'warning':
                icon = '<i class="fas fa-exclamation-triangle"></i>';
                break;
            case 'info':
                icon = '<i class="fas fa-info-circle"></i>';
                break;
            default:
                icon = '<i class="fas fa-bell"></i>';
        }
        
        return `<div class="notification-icon">${icon}</div>`;
    }
    
    /**
     * Position the notification container based on the position setting
     * @param {string} position - The position setting
     */
    positionContainer(position) {
        // Remove existing position classes
        this.container.classList.remove(
            'top-right', 'top-center', 'top-left',
            'bottom-right', 'bottom-center', 'bottom-left'
        );
        
        // Add new position class
        this.container.classList.add(position);
    }
    
    /**
     * Dismiss a notification
     * @param {HTMLElement} notification - The notification element to dismiss
     */
    dismiss(notification) {
        // Cancel progress animation if exists
        if (notification.progressAnimation) {
            cancelAnimationFrame(notification.progressAnimation);
        }
        
        // Hide animation
        notification.classList.remove('show');
        notification.classList.add('hiding');
        
        // Remove after animation completes
        setTimeout(() => {
            if (notification.parentNode) {
                notification.parentNode.removeChild(notification);
                
                // Call onHide callback if provided
                if (notification.onHide && typeof notification.onHide === 'function') {
                    notification.onHide(notification);
                }
            }
        }, 300);
    }
    
    /**
     * Dismiss all notifications
     */
    dismissAll() {
        const notifications = this.container.querySelectorAll('.notification');
        notifications.forEach(notification => {
            this.dismiss(notification);
        });
    }
    
    /**
     * Show a success notification
     * @param {string} message - The notification message
     * @param {string} title - The notification title
     * @param {Object} options - Additional options
     * @returns {HTMLElement} - The notification element
     */
    success(message, title = 'Success', options = {}) {
        return this.show({
            type: 'success',
            title,
            message,
            ...options
        });
    }
    
    /**
     * Show an error notification
     * @param {string} message - The notification message
     * @param {string} title - The notification title
     * @param {Object} options - Additional options
     * @returns {HTMLElement} - The notification element
     */
    error(message, title = 'Error', options = {}) {
        return this.show({
            type: 'error',
            title,
            message,
            duration: 8000, // Errors stay longer by default
            ...options
        });
    }
    
    /**
     * Show a warning notification
     * @param {string} message - The notification message
     * @param {string} title - The notification title
     * @param {Object} options - Additional options
     * @returns {HTMLElement} - The notification element
     */
    warning(message, title = 'Warning', options = {}) {
        return this.show({
            type: 'warning',
            title,
            message,
            duration: 7000, // Warnings stay a bit longer by default
            ...options
        });
    }
    
    /**
     * Show an info notification
     * @param {string} message - The notification message
     * @param {string} title - The notification title
     * @param {Object} options - Additional options
     * @returns {HTMLElement} - The notification element
     */
    info(message, title = 'Information', options = {}) {
        return this.show({
            type: 'info',
            title,
            message,
            ...options
        });
    }
    
    /**
     * Show a loading notification that can be updated later
     * @param {string} message - The notification message
     * @param {string} title - The notification title
     * @param {Object} options - Additional options
     * @returns {Object} - An object with the notification and update/complete methods
     */
    loading(message = 'Please wait...', title = 'Loading', options = {}) {
        const notification = this.show({
            type: 'info',
            title,
            message,
            icon: true,
            dismissible: false,
            autoHide: false,
            ...options
        });
        
        // Replace icon with spinner
        const iconContainer = notification.querySelector('.notification-icon');
        if (iconContainer) {
            iconContainer.innerHTML = '<div class="spinner-border spinner-border-sm" role="status"><span class="visually-hidden">Loading...</span></div>';
        }
        
        return {
            notification,
            
            // Update the loading message
            update: (newMessage, newTitle = null) => {
                const messageEl = notification.querySelector('.notification-message');
                if (messageEl) {
                    messageEl.textContent = newMessage;
                }
                
                if (newTitle) {
                    const titleEl = notification.querySelector('.notification-title');
                    if (titleEl) {
                        titleEl.textContent = newTitle;
                    }
                }
                
                return this;
            },
            
            // Complete the loading process with success or error
            complete: (success = true, finalMessage = null, finalTitle = null) => {
                const iconContainer = notification.querySelector('.notification-icon');
                
                if (iconContainer) {
                    if (success) {
                        iconContainer.innerHTML = '<i class="fas fa-check-circle"></i>';
                        notification.classList.remove('notification-info');
                        notification.classList.add('notification-success');
                    } else {
                        iconContainer.innerHTML = '<i class="fas fa-times-circle"></i>';
                        notification.classList.remove('notification-info');
                        notification.classList.add('notification-error');
                    }
                }
                
                if (finalMessage) {
                    const messageEl = notification.querySelector('.notification-message');
                    if (messageEl) {
                        messageEl.textContent = finalMessage;
                    }
                }
                
                if (finalTitle) {
                    const titleEl = notification.querySelector('.notification-title');
                    if (titleEl) {
                        titleEl.textContent = finalTitle;
                    }
                }
                
                // Add close button and auto-hide
                notification.querySelector('.notification-content').insertAdjacentHTML(
                    'beforeend',
                    '<button type="button" class="notification-close">&times;</button>'
                );
                
                const closeBtn = notification.querySelector('.notification-close');
                if (closeBtn) {
                    closeBtn.addEventListener('click', () => this.dismiss(notification));
                }
                
                // Add progress bar for auto-hide
                const progressBar = notification.querySelector('.notification-progress');
                progressBar.style.display = 'block';
                
                let duration = success ? 5000 : 8000;
                
                // Animate progress bar
                let start = null;
                const animate = (timestamp) => {
                    if (!start) start = timestamp;
                    const progress = timestamp - start;
                    const percentage = Math.min(progress / duration * 100, 100);
                    
                    progressBar.style.width = `${100 - percentage}%`;
                    
                    if (progress < duration) {
                        notification.progressAnimation = requestAnimationFrame(animate);
                    } else {
                        this.dismiss(notification);
                    }
                };
                
                notification.progressAnimation = requestAnimationFrame(animate);
                
                return this;
            }
        };
    }
    
    /**
     * Show an OS-style notification if supported
     * Falls back to a regular notification if not supported or permission denied
     * @param {Object} options - Notification options
     */
    system(options = {}) {
        // Check if browser notifications are supported
        if (!('Notification' in window)) {
            // Fallback to regular notification
            return this.show(options);
        }
        
        // Check if permission has been granted
        if (Notification.permission === 'granted') {
            this.showSystemNotification(options);
        } 
        // Check if permission is not denied (could be default)
        else if (Notification.permission !== 'denied') {
            // Request permission
            Notification.requestPermission().then(permission => {
                if (permission === 'granted') {
                    this.showSystemNotification(options);
                } else {
                    // Fallback to regular notification
                    return this.show(options);
                }
            });
        } else {
            // Permission denied, fallback to regular notification
            return this.show(options);
        }
    }
    
    /**
     * Show a system notification
     * @param {Object} options - Notification options
     */
    showSystemNotification(options) {
        const defaults = {
            type: 'info',
            title: 'Notification',
            message: '',
            icon: '/static/images/logo.png',
            onClick: null
        };
        
        const settings = { ...defaults, ...options };
        
        // Create system notification
        const notification = new Notification(settings.title, {
            body: settings.message,
            icon: settings.icon
        });
        
        // Add click handler
        if (settings.onClick) {
            notification.onclick = () => {
                settings.onClick(notification);
                window.focus();
                notification.close();
            };
        }
        
        return notification;
    }
}

// Create a singleton instance
const notificationSystem = new NotificationSystem();

// Export the notification system
window.notificationSystem = notificationSystem; 
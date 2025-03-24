/**
 * Modal Dialog Component for Mobilize CRM
 * Provides a reusable modal dialog system
 */

class ModalComponent {
    /**
     * Create a new modal
     * @param {Object} options - Modal configuration options
     */
    constructor(options = {}) {
        this.options = {
            id: options.id || `modal-${Math.random().toString(36).substring(2, 9)}`,
            title: options.title || 'Modal Title',
            content: options.content || '',
            size: options.size || 'medium', // small, medium, large, xlarge
            backdrop: options.backdrop !== false,
            closeButton: options.closeButton !== false,
            buttons: options.buttons || [],
            onShow: options.onShow || (() => {}),
            onHide: options.onHide || (() => {}),
            onConfirm: options.onConfirm || (() => {}),
            onCancel: options.onCancel || (() => {}),
            contentType: options.contentType || 'html' // 'html', 'text', 'ajax'
        };
        
        this.isVisible = false;
        this.element = null;
        this.backdropElement = null;
        
        this.create();
    }
    
    /**
     * Create the modal elements
     */
    create() {
        // Create modal element
        this.element = document.createElement('div');
        this.element.id = this.options.id;
        this.element.classList.add('modal');
        this.element.setAttribute('tabindex', '-1');
        this.element.setAttribute('role', 'dialog');
        this.element.setAttribute('aria-hidden', 'true');
        
        // Create modal dialog
        const sizeClass = this.getSizeClass();
        
        const modalContent = `
            <div class="modal-dialog ${sizeClass}" role="document">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title">${this.options.title}</h5>
                        ${this.options.closeButton ? '<button type="button" class="btn-close" data-dismiss="modal" aria-label="Close"></button>' : ''}
                    </div>
                    <div class="modal-body">
                        ${this.getContent()}
                    </div>
                    ${this.getFooterContent()}
                </div>
            </div>
        `;
        
        this.element.innerHTML = modalContent;
        
        // Add event listeners
        this.addEventListeners();
        
        // Add to document
        document.body.appendChild(this.element);
    }
    
    /**
     * Get the content for the modal
     * @returns {string} - The HTML content
     */
    getContent() {
        if (this.options.contentType === 'text') {
            return `<p>${this.options.content}</p>`;
        } else if (this.options.contentType === 'ajax') {
            return '<div class="text-center"><div class="spinner-border" role="status"><span class="visually-hidden">Loading...</span></div></div>';
        } else {
            return this.options.content;
        }
    }
    
    /**
     * Get the footer content with buttons
     * @returns {string} - The HTML content for the footer
     */
    getFooterContent() {
        if (this.options.buttons.length === 0) {
            return '';
        }
        
        let buttonHtml = this.options.buttons.map(button => {
            const btnClass = button.class || 'btn-secondary';
            const btnId = button.id || '';
            const dataAttr = button.data ? Object.entries(button.data).map(([key, value]) => `data-${key}="${value}"`).join(' ') : '';
            
            return `<button type="button" class="btn ${btnClass}" id="${btnId}" ${dataAttr}>${button.text}</button>`;
        }).join('');
        
        return `<div class="modal-footer">${buttonHtml}</div>`;
    }
    
    /**
     * Get the CSS class for modal size
     * @returns {string} - The CSS class
     */
    getSizeClass() {
        switch (this.options.size) {
            case 'small':
                return 'modal-sm';
            case 'large':
                return 'modal-lg';
            case 'xlarge':
                return 'modal-xl';
            default:
                return '';
        }
    }
    
    /**
     * Add event listeners to modal elements
     */
    addEventListeners() {
        if (!this.element) return;
        
        // Close button click
        const closeButton = this.element.querySelector('.btn-close');
        if (closeButton) {
            closeButton.addEventListener('click', () => this.hide());
        }
        
        // Custom buttons
        this.options.buttons.forEach((button, index) => {
            const buttonElement = this.element.querySelector(`.modal-footer .btn:nth-child(${index + 1})`);
            if (buttonElement && typeof button.handler === 'function') {
                buttonElement.addEventListener('click', (e) => {
                    button.handler(e, this);
                });
            }
        });
        
        // ESC key
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && this.isVisible) {
                this.hide();
            }
        });
        
        // Handle backdrop click
        this.element.addEventListener('click', (e) => {
            if (e.target === this.element && this.options.backdrop) {
                this.hide();
            }
        });
    }
    
    /**
     * Create the backdrop element
     */
    createBackdrop() {
        if (!this.options.backdrop) return;
        
        this.backdropElement = document.createElement('div');
        this.backdropElement.classList.add('modal-backdrop', 'fade', 'show');
        document.body.appendChild(this.backdropElement);
    }
    
    /**
     * Remove the backdrop element
     */
    removeBackdrop() {
        if (this.backdropElement) {
            document.body.removeChild(this.backdropElement);
            this.backdropElement = null;
        }
    }
    
    /**
     * Show the modal
     */
    show() {
        if (!this.element || this.isVisible) return;
        
        // Create backdrop
        this.createBackdrop();
        
        // Show modal
        document.body.classList.add('modal-open');
        this.element.classList.add('show');
        this.element.style.display = 'block';
        this.element.setAttribute('aria-hidden', 'false');
        
        this.isVisible = true;
        
        // Load AJAX content if needed
        if (this.options.contentType === 'ajax' && this.options.content) {
            this.loadAjaxContent(this.options.content);
        }
        
        // Call onShow callback
        if (typeof this.options.onShow === 'function') {
            this.options.onShow(this);
        }
    }
    
    /**
     * Hide the modal
     */
    hide() {
        if (!this.element || !this.isVisible) return;
        
        // Hide modal
        this.element.classList.remove('show');
        this.element.style.display = 'none';
        this.element.setAttribute('aria-hidden', 'true');
        document.body.classList.remove('modal-open');
        
        // Remove backdrop
        this.removeBackdrop();
        
        this.isVisible = false;
        
        // Call onHide callback
        if (typeof this.options.onHide === 'function') {
            this.options.onHide(this);
        }
    }
    
    /**
     * Toggle modal visibility
     */
    toggle() {
        if (this.isVisible) {
            this.hide();
        } else {
            this.show();
        }
    }
    
    /**
     * Load AJAX content into the modal body
     * @param {string} url - The URL to load content from
     */
    loadAjaxContent(url) {
        const modalBody = this.element.querySelector('.modal-body');
        
        fetch(url)
            .then(response => {
                if (!response.ok) {
                    throw new Error(`HTTP error ${response.status}`);
                }
                return response.text();
            })
            .then(html => {
                modalBody.innerHTML = html;
            })
            .catch(error => {
                modalBody.innerHTML = `<div class="alert alert-danger">Error loading content: ${error.message}</div>`;
            });
    }
    
    /**
     * Update modal content
     * @param {string} content - New content
     */
    setContent(content) {
        const modalBody = this.element.querySelector('.modal-body');
        if (modalBody) {
            if (this.options.contentType === 'text') {
                modalBody.innerHTML = `<p>${content}</p>`;
            } else {
                modalBody.innerHTML = content;
            }
        }
    }
    
    /**
     * Update modal title
     * @param {string} title - New title
     */
    setTitle(title) {
        const modalTitle = this.element.querySelector('.modal-title');
        if (modalTitle) {
            modalTitle.textContent = title;
        }
    }
    
    /**
     * Add a button to the modal footer
     * @param {Object} button - Button configuration
     */
    addButton(button) {
        const modalFooter = this.element.querySelector('.modal-footer');
        
        if (!modalFooter) {
            // Create footer if it doesn't exist
            const footer = document.createElement('div');
            footer.classList.add('modal-footer');
            this.element.querySelector('.modal-content').appendChild(footer);
        }
        
        const buttonElement = document.createElement('button');
        buttonElement.type = 'button';
        buttonElement.classList.add('btn');
        buttonElement.classList.add(button.class || 'btn-secondary');
        buttonElement.textContent = button.text;
        
        if (button.id) {
            buttonElement.id = button.id;
        }
        
        if (button.data) {
            for (const [key, value] of Object.entries(button.data)) {
                buttonElement.dataset[key] = value;
            }
        }
        
        if (typeof button.handler === 'function') {
            buttonElement.addEventListener('click', (e) => {
                button.handler(e, this);
            });
        }
        
        modalFooter.appendChild(buttonElement);
    }
    
    /**
     * Remove the modal from the DOM
     */
    destroy() {
        if (this.element) {
            this.hide();
            document.body.removeChild(this.element);
            this.element = null;
        }
    }
}

/**
 * Static methods to create common modals
 */
ModalComponent.confirm = function(options = {}) {
    const modal = new ModalComponent({
        title: options.title || 'Confirm',
        content: options.content || 'Are you sure?',
        contentType: 'text',
        size: 'small',
        buttons: [
            {
                text: options.cancelText || 'Cancel',
                class: 'btn-secondary',
                handler: (e, modal) => {
                    modal.hide();
                    if (typeof options.onCancel === 'function') {
                        options.onCancel();
                    }
                }
            },
            {
                text: options.confirmText || 'Confirm',
                class: 'btn-primary',
                handler: (e, modal) => {
                    modal.hide();
                    if (typeof options.onConfirm === 'function') {
                        options.onConfirm();
                    }
                }
            }
        ],
        ...options
    });
    
    modal.show();
    return modal;
};

ModalComponent.alert = function(options = {}) {
    const modal = new ModalComponent({
        title: options.title || 'Alert',
        content: options.content || '',
        contentType: options.contentType || 'text',
        size: 'small',
        buttons: [
            {
                text: options.buttonText || 'OK',
                class: 'btn-primary',
                handler: (e, modal) => {
                    modal.hide();
                    if (typeof options.onClose === 'function') {
                        options.onClose();
                    }
                }
            }
        ],
        ...options
    });
    
    modal.show();
    return modal;
};

ModalComponent.form = function(options = {}) {
    const formId = options.formId || `form-${Math.random().toString(36).substring(2, 9)}`;
    const formContent = options.form || `<form id="${formId}"></form>`;
    
    const modal = new ModalComponent({
        title: options.title || 'Form',
        content: formContent,
        size: options.size || 'medium',
        buttons: [
            {
                text: options.cancelText || 'Cancel',
                class: 'btn-secondary',
                handler: (e, modal) => {
                    modal.hide();
                    if (typeof options.onCancel === 'function') {
                        options.onCancel();
                    }
                }
            },
            {
                text: options.submitText || 'Submit',
                class: 'btn-primary',
                handler: (e, modal) => {
                    const form = document.getElementById(formId);
                    if (form) {
                        // Trigger form validation
                        if (form.checkValidity()) {
                            if (typeof options.onSubmit === 'function') {
                                const formData = new FormData(form);
                                const success = options.onSubmit(formData, form, modal);
                                
                                // Only hide if submission was successful
                                if (success !== false) {
                                    modal.hide();
                                }
                            } else {
                                modal.hide();
                            }
                        } else {
                            // Trigger validation display
                            form.classList.add('was-validated');
                        }
                    } else {
                        modal.hide();
                    }
                }
            }
        ],
        ...options
    });
    
    modal.formId = formId;
    modal.show();
    return modal;
};

// Export the ModalComponent class
window.ModalComponent = ModalComponent; 
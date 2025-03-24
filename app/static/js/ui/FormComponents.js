/**
 * Form Components for Mobilize CRM
 * Provides reusable form elements and validation
 */

class FormComponents {
    /**
     * Initialize form components
     * @param {string} formId - The ID of the form to initialize
     */
    constructor(formId) {
        this.form = document.getElementById(formId);
        if (!this.form) {
            console.error(`Form with ID ${formId} not found`);
            return;
        }
        
        this.initializeValidation();
        this.initializeFormControls();
    }

    /**
     * Initialize form validation
     */
    initializeValidation() {
        if (!this.form) return;
        
        // Add submit event listener
        this.form.addEventListener('submit', (event) => {
            if (!this.validateForm()) {
                event.preventDefault();
                event.stopPropagation();
            }
            this.form.classList.add('was-validated');
        });
        
        // Add input event listeners for real-time validation
        const inputs = this.form.querySelectorAll('input, select, textarea');
        inputs.forEach(input => {
            input.addEventListener('input', () => this.validateInput(input));
            input.addEventListener('blur', () => this.validateInput(input));
        });
    }
    
    /**
     * Initialize custom form controls
     */
    initializeFormControls() {
        this.initializeTagInputs();
        this.initializeDatePickers();
        this.initializeRichTextEditors();
        this.initializeSelectControls();
    }
    
    /**
     * Validate the entire form
     * @returns {boolean} - Whether the form is valid
     */
    validateForm() {
        if (!this.form) return false;
        
        let isValid = true;
        const inputs = this.form.querySelectorAll('input, select, textarea');
        
        inputs.forEach(input => {
            if (!this.validateInput(input)) {
                isValid = false;
            }
        });
        
        return isValid;
    }
    
    /**
     * Validate a single input
     * @param {HTMLElement} input - The input to validate
     * @returns {boolean} - Whether the input is valid
     */
    validateInput(input) {
        if (!input) return false;
        
        const isValid = input.checkValidity();
        const feedbackElement = input.nextElementSibling;
        
        if (isValid) {
            input.classList.remove('is-invalid');
            input.classList.add('is-valid');
        } else {
            input.classList.remove('is-valid');
            input.classList.add('is-invalid');
            
            // Display custom error message if available
            if (feedbackElement && feedbackElement.classList.contains('invalid-feedback')) {
                const errorMessage = this.getErrorMessage(input);
                if (errorMessage) {
                    feedbackElement.textContent = errorMessage;
                }
            }
        }
        
        return isValid;
    }
    
    /**
     * Get custom error message based on validation type
     * @param {HTMLElement} input - The input element
     * @returns {string} - The error message
     */
    getErrorMessage(input) {
        if (input.validity.valueMissing) {
            return input.dataset.requiredMessage || 'This field is required';
        } else if (input.validity.typeMismatch) {
            if (input.type === 'email') {
                return input.dataset.emailMessage || 'Please enter a valid email address';
            } else if (input.type === 'url') {
                return input.dataset.urlMessage || 'Please enter a valid URL';
            }
        } else if (input.validity.patternMismatch) {
            return input.dataset.patternMessage || 'Please match the requested format';
        } else if (input.validity.tooShort) {
            return `Please enter at least ${input.minLength} characters`;
        } else if (input.validity.tooLong) {
            return `Please enter no more than ${input.maxLength} characters`;
        }
        
        return input.validationMessage;
    }
    
    /**
     * Initialize tag input fields
     */
    initializeTagInputs() {
        const tagInputs = this.form.querySelectorAll('.tag-input');
        
        tagInputs.forEach(container => {
            const input = container.querySelector('input[type="text"]');
            const hiddenInput = container.querySelector('input[type="hidden"]');
            const tagContainer = container.querySelector('.tags-container');
            
            input.addEventListener('keydown', (e) => {
                if (e.key === 'Enter' || e.key === ',') {
                    e.preventDefault();
                    
                    const tag = input.value.trim();
                    if (tag) {
                        this.addTag(tag, tagContainer, hiddenInput);
                        input.value = '';
                    }
                }
            });
            
            // Initialize with existing tags if available
            if (hiddenInput.value) {
                const tags = hiddenInput.value.split(',');
                tags.forEach(tag => {
                    if (tag.trim()) {
                        this.addTag(tag.trim(), tagContainer, hiddenInput);
                    }
                });
            }
        });
    }
    
    /**
     * Add a tag to the tag container
     * @param {string} tag - The tag text
     * @param {HTMLElement} container - The tag container element
     * @param {HTMLElement} hiddenInput - The hidden input to store tags
     */
    addTag(tag, container, hiddenInput) {
        const tagElement = document.createElement('span');
        tagElement.classList.add('badge', 'bg-primary', 'me-2', 'mb-2');
        tagElement.textContent = tag;
        
        const removeButton = document.createElement('span');
        removeButton.classList.add('ms-1', 'tag-remove');
        removeButton.innerHTML = '&times;';
        removeButton.addEventListener('click', () => {
            container.removeChild(tagElement);
            this.updateHiddenTagInput(container, hiddenInput);
        });
        
        tagElement.appendChild(removeButton);
        container.appendChild(tagElement);
        this.updateHiddenTagInput(container, hiddenInput);
    }
    
    /**
     * Update the hidden input with current tags
     * @param {HTMLElement} container - The tag container element
     * @param {HTMLElement} hiddenInput - The hidden input to update
     */
    updateHiddenTagInput(container, hiddenInput) {
        const tags = Array.from(container.querySelectorAll('.badge'))
            .map(tag => tag.textContent.replace('×', '').trim());
        hiddenInput.value = tags.join(',');
    }
    
    /**
     * Initialize date picker fields
     */
    initializeDatePickers() {
        const dateInputs = this.form.querySelectorAll('.date-picker');
        
        dateInputs.forEach(input => {
            // Using native date input with fallback
            input.type = 'date';
            
            // Add custom validation for date format
            input.addEventListener('change', () => {
                const dateValue = input.value;
                if (dateValue && !this.isValidDate(dateValue)) {
                    input.setCustomValidity('Please enter a valid date in YYYY-MM-DD format');
                } else {
                    input.setCustomValidity('');
                }
                this.validateInput(input);
            });
        });
    }
    
    /**
     * Check if a string is a valid date
     * @param {string} dateString - The date string to validate
     * @returns {boolean} - Whether the date is valid
     */
    isValidDate(dateString) {
        const regex = /^\d{4}-\d{2}-\d{2}$/;
        if (!regex.test(dateString)) return false;
        
        const date = new Date(dateString);
        return date instanceof Date && !isNaN(date);
    }
    
    /**
     * Initialize rich text editors
     */
    initializeRichTextEditors() {
        const richTextAreas = this.form.querySelectorAll('.rich-text-editor');
        
        richTextAreas.forEach(textarea => {
            // Basic rich text toolbar
            const toolbarId = `toolbar-${Math.random().toString(36).substring(2, 9)}`;
            const toolbar = document.createElement('div');
            toolbar.id = toolbarId;
            toolbar.classList.add('rich-text-toolbar', 'btn-toolbar', 'mb-2');
            toolbar.innerHTML = `
                <div class="btn-group me-2">
                    <button type="button" class="btn btn-sm btn-outline-secondary" data-command="bold">
                        <i class="fas fa-bold"></i>
                    </button>
                    <button type="button" class="btn btn-sm btn-outline-secondary" data-command="italic">
                        <i class="fas fa-italic"></i>
                    </button>
                    <button type="button" class="btn btn-sm btn-outline-secondary" data-command="underline">
                        <i class="fas fa-underline"></i>
                    </button>
                </div>
                <div class="btn-group me-2">
                    <button type="button" class="btn btn-sm btn-outline-secondary" data-command="insertUnorderedList">
                        <i class="fas fa-list-ul"></i>
                    </button>
                    <button type="button" class="btn btn-sm btn-outline-secondary" data-command="insertOrderedList">
                        <i class="fas fa-list-ol"></i>
                    </button>
                </div>
                <div class="btn-group">
                    <button type="button" class="btn btn-sm btn-outline-secondary" data-command="createLink">
                        <i class="fas fa-link"></i>
                    </button>
                </div>
            `;
            
            // Create editable div
            const editableDiv = document.createElement('div');
            editableDiv.classList.add('form-control', 'rich-text-content');
            editableDiv.setAttribute('contenteditable', 'true');
            editableDiv.innerHTML = textarea.value;
            editableDiv.style.minHeight = '150px';
            
            // Hide the original textarea
            textarea.style.display = 'none';
            
            // Insert the new elements
            textarea.parentNode.insertBefore(toolbar, textarea);
            textarea.parentNode.insertBefore(editableDiv, textarea);
            
            // Add event listeners to toolbar buttons
            toolbar.querySelectorAll('button').forEach(button => {
                button.addEventListener('click', (e) => {
                    e.preventDefault();
                    const command = button.getAttribute('data-command');
                    
                    if (command === 'createLink') {
                        const url = prompt('Enter the link URL:');
                        if (url) {
                            document.execCommand(command, false, url);
                        }
                    } else {
                        document.execCommand(command, false, null);
                    }
                    
                    // Update original textarea
                    textarea.value = editableDiv.innerHTML;
                });
            });
            
            // Update textarea on editable div changes
            editableDiv.addEventListener('input', () => {
                textarea.value = editableDiv.innerHTML;
            });
            
            // Focus handling
            editableDiv.addEventListener('focus', () => {
                editableDiv.classList.add('focus');
            });
            
            editableDiv.addEventListener('blur', () => {
                editableDiv.classList.remove('focus');
                textarea.dispatchEvent(new Event('change'));
            });
        });
    }
    
    /**
     * Initialize custom select controls
     */
    initializeSelectControls() {
        const selectElements = this.form.querySelectorAll('.custom-select');
        
        selectElements.forEach(select => {
            // Only initialize if not already enhanced
            if (select.classList.contains('select-initialized')) {
                return;
            }
            
            // Create wrapper
            const wrapper = document.createElement('div');
            wrapper.classList.add('custom-select-wrapper');
            select.parentNode.insertBefore(wrapper, select);
            wrapper.appendChild(select);
            
            // Mark as initialized
            select.classList.add('select-initialized');
            
            // Add searchable functionality if specified
            if (select.classList.contains('searchable-select')) {
                this.makeSelectSearchable(select, wrapper);
            }
        });
    }
    
    /**
     * Make a select element searchable
     * @param {HTMLElement} select - The select element
     * @param {HTMLElement} wrapper - The wrapper element
     */
    makeSelectSearchable(select, wrapper) {
        // Create search input
        const searchInput = document.createElement('input');
        searchInput.type = 'text';
        searchInput.classList.add('form-control', 'select-search');
        searchInput.placeholder = 'Search...';
        
        // Create dropdown container
        const dropdownContainer = document.createElement('div');
        dropdownContainer.classList.add('custom-select-dropdown');
        
        // Add elements to wrapper
        wrapper.appendChild(searchInput);
        wrapper.appendChild(dropdownContainer);
        
        // Populate dropdown options
        this.updateDropdownOptions(select, dropdownContainer, '');
        
        // Handle search input
        searchInput.addEventListener('input', () => {
            const searchTerm = searchInput.value.toLowerCase();
            this.updateDropdownOptions(select, dropdownContainer, searchTerm);
        });
        
        // Handle dropdown item selection
        dropdownContainer.addEventListener('click', (e) => {
            if (e.target.classList.contains('dropdown-item')) {
                const value = e.target.getAttribute('data-value');
                select.value = value;
                select.dispatchEvent(new Event('change'));
                searchInput.value = e.target.textContent;
                dropdownContainer.style.display = 'none';
            }
        });
        
        // Toggle dropdown on search input focus
        searchInput.addEventListener('focus', () => {
            dropdownContainer.style.display = 'block';
        });
        
        // Close dropdown when clicking outside
        document.addEventListener('click', (e) => {
            if (!wrapper.contains(e.target)) {
                dropdownContainer.style.display = 'none';
            }
        });
        
        // Initialize with selected value
        const selectedOption = select.options[select.selectedIndex];
        if (selectedOption) {
            searchInput.value = selectedOption.textContent;
        }
    }
    
    /**
     * Update dropdown options based on search term
     * @param {HTMLElement} select - The select element
     * @param {HTMLElement} container - The dropdown container
     * @param {string} searchTerm - The search term
     */
    updateDropdownOptions(select, container, searchTerm) {
        container.innerHTML = '';
        
        Array.from(select.options).forEach(option => {
            const text = option.textContent;
            const value = option.value;
            
            if (value && (searchTerm === '' || text.toLowerCase().includes(searchTerm))) {
                const item = document.createElement('div');
                item.classList.add('dropdown-item');
                item.setAttribute('data-value', value);
                item.textContent = text;
                
                if (value === select.value) {
                    item.classList.add('active');
                }
                
                container.appendChild(item);
            }
        });
    }
}

// Export the FormComponents class
window.FormComponents = FormComponents; 
/**
 * GoogleComponents.js
 * UI components specific to Google integration functionality
 */

class GoogleComponents {
    constructor() {
        this.initialize();
    }

    initialize() {
        // Initialize components when needed
    }

    /**
     * Creates a contact selector component for choosing Google contacts to import
     * @param {string} containerId - ID of the container element
     * @param {Array} contacts - Array of Google contacts
     * @param {Object} options - Configuration options
     */
    createContactSelector(containerId, contacts, options = {}) {
        const container = document.getElementById(containerId);
        if (!container) {
            console.error(`Container with ID '${containerId}' not found`);
            return;
        }

        const defaults = {
            selectable: true,
            searchable: true,
            pagination: true,
            itemsPerPage: 20,
            showEmail: true,
            showPhone: true,
            onSelectionChange: null
        };

        const settings = { ...defaults, ...options };
        this.contacts = contacts || [];
        this.selectedContacts = [];
        this.currentPage = 1;
        this.filteredContacts = [...this.contacts];

        // Create component structure
        container.innerHTML = `
            <div class="google-contact-selector">
                ${settings.searchable ? `
                <div class="contact-search-container">
                    <input type="text" class="contact-search" placeholder="Search contacts...">
                </div>` : ''}
                <div class="contacts-list-container">
                    <table class="contacts-list">
                        <thead>
                            <tr>
                                ${settings.selectable ? '<th class="selector-col"><input type="checkbox" class="select-all-contacts"></th>' : ''}
                                <th>Name</th>
                                ${settings.showEmail ? '<th>Email</th>' : ''}
                                ${settings.showPhone ? '<th>Phone</th>' : ''}
                                <th>Actions</th>
                            </tr>
                        </thead>
                        <tbody></tbody>
                    </table>
                </div>
                ${settings.pagination ? `
                <div class="contact-pagination">
                    <button class="prev-page" disabled>&laquo; Previous</button>
                    <span class="page-info">Page <span class="current-page">1</span> of <span class="total-pages">1</span></span>
                    <button class="next-page" disabled>Next &raquo;</button>
                </div>` : ''}
                <div class="selection-summary" ${settings.selectable ? '' : 'style="display:none"'}>
                    <span class="selected-count">0</span> contacts selected
                    <button class="import-selected" disabled>Import Selected</button>
                </div>
            </div>
        `;

        // Initialize component
        this._setupContactSelector(container, settings);
        this._renderContacts();
    }

    /**
     * Sets up event listeners for the contact selector
     * @param {HTMLElement} container - The container element
     * @param {Object} settings - Component settings
     * @private
     */
    _setupContactSelector(container, settings) {
        if (settings.searchable) {
            const searchInput = container.querySelector('.contact-search');
            searchInput.addEventListener('input', () => {
                this.filterContacts(searchInput.value);
                this.currentPage = 1;
                this._renderContacts();
            });
        }

        if (settings.selectable) {
            const selectAll = container.querySelector('.select-all-contacts');
            selectAll.addEventListener('change', () => {
                this.toggleSelectAll(selectAll.checked);
            });

            container.querySelector('.import-selected').addEventListener('click', () => {
                if (typeof settings.onImport === 'function') {
                    settings.onImport(this.selectedContacts);
                }
            });
        }

        if (settings.pagination) {
            container.querySelector('.prev-page').addEventListener('click', () => {
                if (this.currentPage > 1) {
                    this.currentPage--;
                    this._renderContacts();
                }
            });

            container.querySelector('.next-page').addEventListener('click', () => {
                const totalPages = Math.ceil(this.filteredContacts.length / settings.itemsPerPage);
                if (this.currentPage < totalPages) {
                    this.currentPage++;
                    this._renderContacts();
                }
            });
        }

        // Delegate clicks for contact rows
        container.querySelector('.contacts-list').addEventListener('click', (e) => {
            if (e.target.matches('.contact-checkbox')) {
                const contactId = e.target.closest('tr').dataset.id;
                this.toggleContactSelection(contactId, e.target.checked);
            } else if (e.target.matches('.view-details')) {
                const contactId = e.target.closest('tr').dataset.id;
                if (typeof settings.onViewDetails === 'function') {
                    const contact = this.contacts.find(c => c.id === contactId);
                    settings.onViewDetails(contact);
                }
            }
        });
    }

    /**
     * Filters contacts based on search term
     * @param {string} term - Search term
     */
    filterContacts(term) {
        if (!term) {
            this.filteredContacts = [...this.contacts];
            return;
        }

        term = term.toLowerCase();
        this.filteredContacts = this.contacts.filter(contact => {
            const name = (contact.name || '').toLowerCase();
            const email = (contact.email || '').toLowerCase();
            const phone = (contact.phone || '').toLowerCase();
            return name.includes(term) || email.includes(term) || phone.includes(term);
        });
    }

    /**
     * Renders contacts in the table
     * @private
     */
    _renderContacts() {
        const container = document.querySelector('.google-contact-selector');
        const settings = container._settings;
        const tbody = container.querySelector('tbody');
        tbody.innerHTML = '';

        if (this.filteredContacts.length === 0) {
            const row = document.createElement('tr');
            row.innerHTML = `<td colspan="${settings.selectable ? 4 : 3}" class="no-contacts">No contacts found</td>`;
            tbody.appendChild(row);
            this._updatePagination();
            return;
        }

        // Calculate pagination
        const startIndex = (this.currentPage - 1) * settings.itemsPerPage;
        const endIndex = Math.min(startIndex + settings.itemsPerPage, this.filteredContacts.length);
        const displayedContacts = this.filteredContacts.slice(startIndex, endIndex);

        // Render contacts
        displayedContacts.forEach(contact => {
            const isSelected = this.selectedContacts.includes(contact.id);
            const row = document.createElement('tr');
            row.dataset.id = contact.id;
            
            row.innerHTML = `
                ${settings.selectable ? `
                <td class="selector-col">
                    <input type="checkbox" class="contact-checkbox" ${isSelected ? 'checked' : ''}>
                </td>` : ''}
                <td>${contact.name || '<No name>'}</td>
                ${settings.showEmail ? `<td>${contact.email || '<No email>'}</td>` : ''}
                ${settings.showPhone ? `<td>${contact.phone || '<No phone>'}</td>` : ''}
                <td>
                    <button class="view-details">Details</button>
                </td>
            `;
            
            tbody.appendChild(row);
        });

        this._updatePagination();
    }

    /**
     * Updates pagination controls
     * @private
     */
    _updatePagination() {
        const container = document.querySelector('.google-contact-selector');
        const settings = container._settings;
        
        if (!settings.pagination) return;
        
        const totalPages = Math.ceil(this.filteredContacts.length / settings.itemsPerPage);
        container.querySelector('.current-page').textContent = this.currentPage;
        container.querySelector('.total-pages').textContent = totalPages;
        
        container.querySelector('.prev-page').disabled = this.currentPage <= 1;
        container.querySelector('.next-page').disabled = this.currentPage >= totalPages;
    }

    /**
     * Toggles selection of all contacts
     * @param {boolean} select - Whether to select or deselect all
     */
    toggleSelectAll(select) {
        if (select) {
            this.selectedContacts = this.filteredContacts.map(contact => contact.id);
        } else {
            this.selectedContacts = [];
        }
        this._renderContacts();
        this._updateSelectionCount();
    }

    /**
     * Toggles selection of a specific contact
     * @param {string} contactId - ID of the contact
     * @param {boolean} select - Whether to select or deselect
     */
    toggleContactSelection(contactId, select) {
        if (select && !this.selectedContacts.includes(contactId)) {
            this.selectedContacts.push(contactId);
        } else if (!select) {
            this.selectedContacts = this.selectedContacts.filter(id => id !== contactId);
        }
        this._updateSelectionCount();
    }

    /**
     * Updates the selection count display
     * @private
     */
    _updateSelectionCount() {
        const container = document.querySelector('.google-contact-selector');
        container.querySelector('.selected-count').textContent = this.selectedContacts.length;
        container.querySelector('.import-selected').disabled = this.selectedContacts.length === 0;
        
        // Update select all checkbox
        const selectAll = container.querySelector('.select-all-contacts');
        if (this.filteredContacts.length > 0) {
            selectAll.checked = this.selectedContacts.length === this.filteredContacts.length;
            selectAll.indeterminate = this.selectedContacts.length > 0 && 
                this.selectedContacts.length < this.filteredContacts.length;
        }
    }

    /**
     * Creates a sync status indicator component
     * @param {string} containerId - ID of the container element
     * @param {Object} syncStatus - Current sync status
     */
    createSyncStatusIndicator(containerId, syncStatus = {}) {
        const container = document.getElementById(containerId);
        if (!container) {
            console.error(`Container with ID '${containerId}' not found`);
            return;
        }

        const defaults = {
            lastSync: null,
            status: 'never', // Options: 'never', 'in-progress', 'success', 'error'
            contactCount: 0,
            errorMessage: '',
            onSync: null
        };

        const status = { ...defaults, ...syncStatus };
        
        // Format last sync time
        let lastSyncText = 'Never synchronized';
        if (status.lastSync) {
            const date = new Date(status.lastSync);
            lastSyncText = `Last sync: ${date.toLocaleDateString()} at ${date.toLocaleTimeString()}`;
        }

        // Create the status indicator
        container.innerHTML = `
            <div class="sync-status-indicator status-${status.status}">
                <div class="sync-icon"></div>
                <div class="sync-info">
                    <div class="sync-status">${this._getSyncStatusText(status.status)}</div>
                    <div class="sync-time">${lastSyncText}</div>
                    ${status.contactCount ? `<div class="sync-count">${status.contactCount} contacts synced</div>` : ''}
                    ${status.errorMessage ? `<div class="sync-error">${status.errorMessage}</div>` : ''}
                </div>
                <div class="sync-actions">
                    <button class="sync-now-btn" ${status.status === 'in-progress' ? 'disabled' : ''}>
                        ${status.status === 'in-progress' ? 'Syncing...' : 'Sync Now'}
                    </button>
                </div>
            </div>
        `;

        // Add event listener for sync button
        container.querySelector('.sync-now-btn').addEventListener('click', () => {
            if (status.status !== 'in-progress' && typeof status.onSync === 'function') {
                this.updateSyncStatus(containerId, { status: 'in-progress' });
                status.onSync();
            }
        });
    }

    /**
     * Updates the sync status indicator
     * @param {string} containerId - ID of the container element
     * @param {Object} newStatus - Updated sync status
     */
    updateSyncStatus(containerId, newStatus = {}) {
        const container = document.getElementById(containerId);
        if (!container) return;
        
        const indicator = container.querySelector('.sync-status-indicator');
        if (!indicator) return;
        
        // Update status class
        if (newStatus.status) {
            indicator.className = `sync-status-indicator status-${newStatus.status}`;
            container.querySelector('.sync-status').textContent = this._getSyncStatusText(newStatus.status);
            
            const syncButton = container.querySelector('.sync-now-btn');
            if (newStatus.status === 'in-progress') {
                syncButton.disabled = true;
                syncButton.textContent = 'Syncing...';
            } else {
                syncButton.disabled = false;
                syncButton.textContent = 'Sync Now';
            }
        }
        
        // Update last sync time
        if (newStatus.lastSync) {
            const date = new Date(newStatus.lastSync);
            container.querySelector('.sync-time').textContent = 
                `Last sync: ${date.toLocaleDateString()} at ${date.toLocaleTimeString()}`;
        }
        
        // Update contact count
        if (newStatus.contactCount !== undefined) {
            let countElement = container.querySelector('.sync-count');
            if (newStatus.contactCount > 0) {
                if (!countElement) {
                    countElement = document.createElement('div');
                    countElement.className = 'sync-count';
                    container.querySelector('.sync-info').appendChild(countElement);
                }
                countElement.textContent = `${newStatus.contactCount} contacts synced`;
            } else if (countElement) {
                countElement.remove();
            }
        }
        
        // Update error message
        if (newStatus.errorMessage !== undefined) {
            let errorElement = container.querySelector('.sync-error');
            if (newStatus.errorMessage) {
                if (!errorElement) {
                    errorElement = document.createElement('div');
                    errorElement.className = 'sync-error';
                    container.querySelector('.sync-info').appendChild(errorElement);
                }
                errorElement.textContent = newStatus.errorMessage;
            } else if (errorElement) {
                errorElement.remove();
            }
        }
    }

    /**
     * Returns text representation of sync status
     * @param {string} status - Status code
     * @returns {string} Status text
     * @private
     */
    _getSyncStatusText(status) {
        switch (status) {
            case 'never': return 'Never synchronized';
            case 'in-progress': return 'Synchronization in progress';
            case 'success': return 'Synchronized successfully';
            case 'error': return 'Synchronization failed';
            default: return 'Unknown status';
        }
    }

    /**
     * Creates a contact merge resolver component for resolving conflicts
     * @param {string} containerId - ID of the container element
     * @param {Object} contactPair - Pair of conflicting contacts
     * @param {Object} options - Configuration options
     */
    createContactMergeResolver(containerId, contactPair, options = {}) {
        const container = document.getElementById(containerId);
        if (!container) {
            console.error(`Container with ID '${containerId}' not found`);
            return;
        }

        const defaults = {
            onResolve: null,
            onSkip: null,
            highlightDifferences: true
        };

        const settings = { ...defaults, ...options };
        
        // Ensure we have both contacts
        if (!contactPair || !contactPair.local || !contactPair.google) {
            container.innerHTML = '<div class="error-message">Invalid contact data provided</div>';
            return;
        }

        const local = contactPair.local;
        const google = contactPair.google;
        
        // Create fields comparison
        const fields = [
            { key: 'name', label: 'Name' },
            { key: 'email', label: 'Email' },
            { key: 'phone', label: 'Phone' },
            { key: 'address', label: 'Address' },
            { key: 'company', label: 'Company' },
            { key: 'title', label: 'Job Title' },
            { key: 'notes', label: 'Notes' }
        ];
        
        let fieldRows = '';
        let hasDifferences = false;
        
        fields.forEach(field => {
            const localValue = local[field.key] || '';
            const googleValue = google[field.key] || '';
            const isDifferent = localValue !== googleValue && (localValue || googleValue);
            
            if (isDifferent) hasDifferences = true;
            
            if (isDifferent || !settings.highlightDifferences) {
                fieldRows += `
                    <tr class="${isDifferent ? 'different' : ''}">
                        <td class="field-name">${field.label}</td>
                        <td class="local-value">
                            <div class="value-container">
                                <span class="value">${localValue || '<empty>'}</span>
                                <input type="radio" name="${field.key}" value="local" ${!googleValue || localValue && !isDifferent ? 'checked' : ''} />
                            </div>
                        </td>
                        <td class="google-value">
                            <div class="value-container">
                                <span class="value">${googleValue || '<empty>'}</span>
                                <input type="radio" name="${field.key}" value="google" ${!localValue && googleValue ? 'checked' : ''} />
                            </div>
                        </td>
                    </tr>
                `;
            }
        });
        
        // Create the component
        container.innerHTML = `
            <div class="contact-merge-resolver">
                <h3>Resolve Contact Conflict</h3>
                <div class="contact-pair-info">
                    <div class="local-contact">
                        <h4>Local Contact</h4>
                        <div class="contact-id">ID: ${local.id}</div>
                        <div class="last-updated">Last Updated: ${new Date(local.updatedAt).toLocaleString()}</div>
                    </div>
                    <div class="google-contact">
                        <h4>Google Contact</h4>
                        <div class="contact-id">ID: ${google.id}</div>
                        <div class="last-updated">Last Updated: ${new Date(google.updatedAt).toLocaleString()}</div>
                    </div>
                </div>
                
                <div class="field-selection">
                    <table class="merge-fields">
                        <thead>
                            <tr>
                                <th>Field</th>
                                <th>
                                    Local Value
                                    <button class="select-all-local">Select All</button>
                                </th>
                                <th>
                                    Google Value
                                    <button class="select-all-google">Select All</button>
                                </th>
                            </tr>
                        </thead>
                        <tbody>
                            ${fieldRows || '<tr><td colspan="3">No differences found between contacts</td></tr>'}
                        </tbody>
                    </table>
                </div>
                
                <div class="merge-actions">
                    <button class="skip-merge-btn">Skip</button>
                    <button class="resolve-merge-btn" ${!hasDifferences ? 'disabled' : ''}>
                        Merge Contacts
                    </button>
                </div>
            </div>
        `;
        
        // Add event listeners
        container.querySelector('.select-all-local').addEventListener('click', (e) => {
            e.preventDefault();
            container.querySelectorAll('input[type="radio"][value="local"]').forEach(radio => {
                radio.checked = true;
            });
        });
        
        container.querySelector('.select-all-google').addEventListener('click', (e) => {
            e.preventDefault();
            container.querySelectorAll('input[type="radio"][value="google"]').forEach(radio => {
                radio.checked = true;
            });
        });
        
        container.querySelector('.skip-merge-btn').addEventListener('click', () => {
            if (typeof settings.onSkip === 'function') {
                settings.onSkip(contactPair);
            }
        });
        
        container.querySelector('.resolve-merge-btn').addEventListener('click', () => {
            if (typeof settings.onResolve === 'function') {
                const resolvedData = { id: local.id, googleId: google.id };
                
                // Get selections for each field
                fields.forEach(field => {
                    const selected = container.querySelector(`input[name="${field.key}"]:checked`);
                    if (selected) {
                        resolvedData[field.key] = selected.value === 'local' ? 
                            local[field.key] : google[field.key];
                    }
                });
                
                settings.onResolve(resolvedData);
            }
        });
    }

    /**
     * Creates an import progress tracker component
     * @param {string} containerId - ID of the container element
     * @param {Object} options - Configuration options
     */
    createImportProgressTracker(containerId, options = {}) {
        const container = document.getElementById(containerId);
        if (!container) {
            console.error(`Container with ID '${containerId}' not found`);
            return;
        }

        const defaults = {
            totalContacts: 0,
            processedContacts: 0,
            successCount: 0,
            errorCount: 0,
            skipCount: 0,
            onCancel: null,
            showDetails: true
        };

        const settings = { ...defaults, ...options };
        this.progressSettings = settings;
        
        // Calculate progress percentage
        const progress = settings.totalContacts > 0 ? 
            Math.round((settings.processedContacts / settings.totalContacts) * 100) : 0;
        
        // Create the component
        container.innerHTML = `
            <div class="import-progress-tracker">
                <h3>Import Progress</h3>
                <div class="progress-info">
                    <div class="progress-bar-container">
                        <div class="progress-bar" style="width: ${progress}%"></div>
                        <div class="progress-text">${progress}%</div>
                    </div>
                    <div class="progress-counts">
                        <span class="processed-count">${settings.processedContacts}</span> / 
                        <span class="total-count">${settings.totalContacts}</span> contacts processed
                    </div>
                    <div class="estimated-time">
                        ${this._calculateEstimatedTime(settings)}
                    </div>
                </div>
                
                ${settings.showDetails ? `
                <div class="progress-details">
                    <div class="success-count">
                        <i class="success-icon"></i> ${settings.successCount} successful
                    </div>
                    <div class="error-count">
                        <i class="error-icon"></i> ${settings.errorCount} errors
                    </div>
                    <div class="skip-count">
                        <i class="skip-icon"></i> ${settings.skipCount} skipped
                    </div>
                </div>` : ''}
                
                <div class="progress-actions">
                    <button class="cancel-import-btn">Cancel Import</button>
                </div>
            </div>
        `;
        
        // Add event listener for cancel button
        container.querySelector('.cancel-import-btn').addEventListener('click', () => {
            if (typeof settings.onCancel === 'function') {
                settings.onCancel();
            }
        });
    }

    /**
     * Updates the import progress tracker
     * @param {string} containerId - ID of the container element
     * @param {Object} progress - Progress update data
     */
    updateImportProgress(containerId, progress = {}) {
        const container = document.getElementById(containerId);
        if (!container) return;
        
        const tracker = container.querySelector('.import-progress-tracker');
        if (!tracker) return;
        
        // Update settings with new values
        this.progressSettings = { ...this.progressSettings, ...progress };
        const settings = this.progressSettings;
        
        // Update progress bar
        const progressPercent = settings.totalContacts > 0 ? 
            Math.round((settings.processedContacts / settings.totalContacts) * 100) : 0;
            
        container.querySelector('.progress-bar').style.width = `${progressPercent}%`;
        container.querySelector('.progress-text').textContent = `${progressPercent}%`;
        
        // Update counts
        container.querySelector('.processed-count').textContent = settings.processedContacts;
        container.querySelector('.total-count').textContent = settings.totalContacts;
        
        // Update estimated time
        container.querySelector('.estimated-time').textContent = this._calculateEstimatedTime(settings);
        
        // Update details if shown
        if (settings.showDetails) {
            container.querySelector('.success-count').innerHTML = 
                `<i class="success-icon"></i> ${settings.successCount} successful`;
            container.querySelector('.error-count').innerHTML = 
                `<i class="error-icon"></i> ${settings.errorCount} errors`;
            container.querySelector('.skip-count').innerHTML = 
                `<i class="skip-icon"></i> ${settings.skipCount} skipped`;
        }
        
        // If complete, update UI
        if (settings.processedContacts >= settings.totalContacts && settings.totalContacts > 0) {
            this._showImportComplete(container, settings);
        }
    }

    /**
     * Shows import completion message
     * @param {HTMLElement} container - The container element
     * @param {Object} settings - Current progress settings
     * @private
     */
    _showImportComplete(container, settings) {
        const actionsDiv = container.querySelector('.progress-actions');
        actionsDiv.innerHTML = `
            <div class="import-complete-message">
                Import complete! ${settings.successCount} contacts successfully imported.
            </div>
            <button class="close-progress-btn">Close</button>
        `;
        
        container.querySelector('.close-progress-btn').addEventListener('click', () => {
            container.innerHTML = '';
        });
    }

    /**
     * Calculates and formats estimated remaining time
     * @param {Object} settings - Progress settings
     * @returns {string} Formatted estimated time
     * @private
     */
    _calculateEstimatedTime(settings) {
        if (settings.processedContacts === 0 || settings.totalContacts === 0) {
            return 'Estimating time...';
        }
        
        if (settings.processedContacts >= settings.totalContacts) {
            return 'Import complete';
        }
        
        // If import start time is available, calculate based on elapsed time
        if (settings.startTime) {
            const elapsedMs = Date.now() - new Date(settings.startTime).getTime();
            const msPerContact = elapsedMs / settings.processedContacts;
            const remainingContacts = settings.totalContacts - settings.processedContacts;
            const estimatedRemainingMs = msPerContact * remainingContacts;
            
            // Format the time
            return this._formatTimeRemaining(estimatedRemainingMs);
        }
        
        return 'Calculating...';
    }

    /**
     * Formats time in milliseconds to a human-readable format
     * @param {number} ms - Time in milliseconds
     * @returns {string} Formatted time string
     * @private
     */
    _formatTimeRemaining(ms) {
        if (ms < 1000) return 'Less than a second';
        
        const seconds = Math.floor(ms / 1000);
        const minutes = Math.floor(seconds / 60);
        const hours = Math.floor(minutes / 60);
        
        if (hours > 0) {
            return `About ${hours} hour${hours > 1 ? 's' : ''} remaining`;
        } else if (minutes > 0) {
            return `About ${minutes} minute${minutes > 1 ? 's' : ''} remaining`;
        } else {
            return `About ${seconds} second${seconds > 1 ? 's' : ''} remaining`;
        }
    }
}

// Export to global scope
window.GoogleComponents = new GoogleComponents(); 
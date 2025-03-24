/**
 * Data Table Component for Mobilize CRM
 * Enhances HTML tables with sorting, filtering, and pagination
 */

class DataTableComponent {
    /**
     * Initialize a data table component
     * @param {string} tableId - The ID of the table to enhance
     * @param {Object} options - Configuration options
     */
    constructor(tableId, options = {}) {
        this.table = document.getElementById(tableId);
        if (!this.table) {
            console.error(`Table with ID ${tableId} not found`);
            return;
        }
        
        this.options = {
            perPage: options.perPage || 10,
            paginate: options.paginate !== false,
            search: options.search !== false,
            sortable: options.sortable !== false,
            selectable: options.selectable || false,
            actionsColumn: options.actionsColumn || false,
            emptyMessage: options.emptyMessage || 'No data available',
            ...options
        };
        
        this.currentPage = 1;
        this.sortColumn = null;
        this.sortDirection = 'asc';
        this.filterValue = '';
        this.selectedRows = new Set();
        
        this.initialize();
    }
    
    /**
     * Initialize table enhancements
     */
    initialize() {
        this.wrapTable();
        this.setupTableHeader();
        
        if (this.options.search) {
            this.addSearchBar();
        }
        
        if (this.options.selectable) {
            this.addSelectionColumn();
        }
        
        if (this.options.paginate) {
            this.addPagination();
        }
        
        this.processData();
        this.render();
    }
    
    /**
     * Wrap the table in a container
     */
    wrapTable() {
        const wrapper = document.createElement('div');
        wrapper.classList.add('data-table-wrapper');
        this.table.parentNode.insertBefore(wrapper, this.table);
        wrapper.appendChild(this.table);
        
        this.wrapper = wrapper;
        this.table.classList.add('data-table');
    }
    
    /**
     * Set up the table header for sorting
     */
    setupTableHeader() {
        const headerRow = this.table.querySelector('thead tr');
        if (!headerRow) return;
        
        const headers = headerRow.querySelectorAll('th');
        headers.forEach((header, index) => {
            // Skip actions column and selection column if present
            if ((this.options.actionsColumn && index === headers.length - 1) || 
                (this.options.selectable && index === 0)) {
                return;
            }
            
            if (this.options.sortable) {
                header.classList.add('sortable');
                header.addEventListener('click', () => this.sortBy(index));
                
                // Add sort indicator
                const sortIndicator = document.createElement('span');
                sortIndicator.classList.add('sort-indicator');
                sortIndicator.innerHTML = '⇵';
                header.appendChild(document.createTextNode(' '));
                header.appendChild(sortIndicator);
            }
        });
    }
    
    /**
     * Add search functionality
     */
    addSearchBar() {
        const searchContainer = document.createElement('div');
        searchContainer.classList.add('data-table-search');
        
        const searchInput = document.createElement('input');
        searchInput.type = 'text';
        searchInput.classList.add('form-control');
        searchInput.placeholder = 'Search...';
        
        searchInput.addEventListener('input', (e) => {
            this.filterValue = e.target.value.toLowerCase();
            this.currentPage = 1;
            this.processData();
            this.render();
        });
        
        searchContainer.appendChild(searchInput);
        this.wrapper.insertBefore(searchContainer, this.table);
    }
    
    /**
     * Add row selection functionality
     */
    addSelectionColumn() {
        // Add header checkbox
        const headerRow = this.table.querySelector('thead tr');
        if (!headerRow) return;
        
        const selectAllHeader = document.createElement('th');
        selectAllHeader.classList.add('selection-column');
        
        const selectAllCheckbox = document.createElement('input');
        selectAllCheckbox.type = 'checkbox';
        selectAllCheckbox.addEventListener('change', (e) => {
            this.toggleSelectAll(e.target.checked);
        });
        
        selectAllHeader.appendChild(selectAllCheckbox);
        headerRow.insertBefore(selectAllHeader, headerRow.firstChild);
        
        // Add checkboxes to each row
        const rows = this.table.querySelectorAll('tbody tr');
        rows.forEach(row => {
            const selectionCell = document.createElement('td');
            selectionCell.classList.add('selection-column');
            
            const checkbox = document.createElement('input');
            checkbox.type = 'checkbox';
            checkbox.addEventListener('change', (e) => {
                this.toggleRowSelection(row, e.target.checked);
            });
            
            selectionCell.appendChild(checkbox);
            row.insertBefore(selectionCell, row.firstChild);
        });
    }
    
    /**
     * Add pagination controls
     */
    addPagination() {
        const paginationContainer = document.createElement('div');
        paginationContainer.classList.add('data-table-pagination');
        
        // Create page size selector
        const pageSizeContainer = document.createElement('div');
        pageSizeContainer.classList.add('page-size-selector');
        
        const pageSizeLabel = document.createElement('span');
        pageSizeLabel.textContent = 'Rows per page: ';
        
        const pageSizeSelect = document.createElement('select');
        pageSizeSelect.classList.add('form-select', 'form-select-sm');
        
        [10, 25, 50, 100].forEach(size => {
            const option = document.createElement('option');
            option.value = size;
            option.textContent = size;
            if (size === this.options.perPage) {
                option.selected = true;
            }
            pageSizeSelect.appendChild(option);
        });
        
        pageSizeSelect.addEventListener('change', (e) => {
            this.options.perPage = parseInt(e.target.value);
            this.currentPage = 1;
            this.processData();
            this.render();
        });
        
        pageSizeContainer.appendChild(pageSizeLabel);
        pageSizeContainer.appendChild(pageSizeSelect);
        
        // Create page navigation
        const pageNavigation = document.createElement('div');
        pageNavigation.classList.add('page-navigation');
        
        this.paginationContainer = paginationContainer;
        this.pageNavigation = pageNavigation;
        
        paginationContainer.appendChild(pageSizeContainer);
        paginationContainer.appendChild(pageNavigation);
        
        this.wrapper.appendChild(paginationContainer);
    }
    
    /**
     * Update pagination controls
     */
    updatePagination() {
        if (!this.pageNavigation) return;
        
        this.pageNavigation.innerHTML = '';
        
        // Info text
        const infoText = document.createElement('span');
        infoText.classList.add('pagination-info');
        
        const startRow = (this.currentPage - 1) * this.options.perPage + 1;
        const endRow = Math.min(startRow + this.options.perPage - 1, this.filteredData.length);
        
        if (this.filteredData.length > 0) {
            infoText.textContent = `${startRow}-${endRow} of ${this.filteredData.length}`;
        } else {
            infoText.textContent = '0 results';
        }
        
        // Previous button
        const prevButton = document.createElement('button');
        prevButton.classList.add('btn', 'btn-sm', 'btn-outline-secondary');
        prevButton.innerHTML = '&laquo;';
        prevButton.disabled = this.currentPage === 1;
        prevButton.addEventListener('click', () => {
            if (this.currentPage > 1) {
                this.currentPage--;
                this.render();
            }
        });
        
        // Next button
        const nextButton = document.createElement('button');
        nextButton.classList.add('btn', 'btn-sm', 'btn-outline-secondary');
        nextButton.innerHTML = '&raquo;';
        
        const totalPages = Math.ceil(this.filteredData.length / this.options.perPage);
        nextButton.disabled = this.currentPage === totalPages || totalPages === 0;
        
        nextButton.addEventListener('click', () => {
            if (this.currentPage < totalPages) {
                this.currentPage++;
                this.render();
            }
        });
        
        // Page number
        const pageNumber = document.createElement('span');
        pageNumber.classList.add('page-number');
        pageNumber.textContent = `Page ${this.currentPage} of ${totalPages || 1}`;
        
        this.pageNavigation.appendChild(infoText);
        this.pageNavigation.appendChild(prevButton);
        this.pageNavigation.appendChild(pageNumber);
        this.pageNavigation.appendChild(nextButton);
    }
    
    /**
     * Process table data for filtering and sorting
     */
    processData() {
        // Extract data
        this.tableData = Array.from(this.table.querySelectorAll('tbody tr')).map(row => {
            const cells = Array.from(row.querySelectorAll('td')).map(cell => cell.textContent.trim());
            return {
                element: row,
                data: cells,
                visible: true
            };
        });
        
        // Apply filter
        if (this.filterValue) {
            this.filteredData = this.tableData.filter(row => {
                return row.data.some(cell => cell.toLowerCase().includes(this.filterValue));
            });
        } else {
            this.filteredData = [...this.tableData];
        }
        
        // Apply sorting
        if (this.sortColumn !== null) {
            this.filteredData.sort((a, b) => {
                const aValue = a.data[this.sortColumn];
                const bValue = b.data[this.sortColumn];
                
                // Try to compare as numbers if possible
                const aNum = parseFloat(aValue);
                const bNum = parseFloat(bValue);
                
                if (!isNaN(aNum) && !isNaN(bNum)) {
                    return this.sortDirection === 'asc' ? aNum - bNum : bNum - aNum;
                }
                
                // Otherwise compare as strings
                return this.sortDirection === 'asc' 
                    ? aValue.localeCompare(bValue) 
                    : bValue.localeCompare(aValue);
            });
        }
    }
    
    /**
     * Render the table with current settings
     */
    render() {
        // Hide all rows first
        this.tableData.forEach(row => {
            row.element.style.display = 'none';
        });
        
        // Show rows for current page
        const startIndex = (this.currentPage - 1) * this.options.perPage;
        const endIndex = startIndex + this.options.perPage;
        
        this.filteredData.slice(startIndex, endIndex).forEach(row => {
            row.element.style.display = '';
        });
        
        // Update pagination
        if (this.options.paginate) {
            this.updatePagination();
        }
        
        // Update checkboxes
        if (this.options.selectable) {
            this.updateCheckboxes();
        }
        
        // Show empty message if needed
        this.showEmptyMessage();
    }
    
    /**
     * Show empty message if no data is available
     */
    showEmptyMessage() {
        // Remove existing message if any
        const existingMessage = this.wrapper.querySelector('.data-table-empty-message');
        if (existingMessage) {
            existingMessage.remove();
        }
        
        // Show message if no data
        if (this.filteredData.length === 0) {
            const emptyMessage = document.createElement('div');
            emptyMessage.classList.add('data-table-empty-message');
            emptyMessage.textContent = this.options.emptyMessage;
            
            // Insert after the search bar if exists, otherwise before the table
            const searchBar = this.wrapper.querySelector('.data-table-search');
            if (searchBar) {
                searchBar.parentNode.insertBefore(emptyMessage, searchBar.nextSibling);
            } else {
                this.wrapper.insertBefore(emptyMessage, this.table);
            }
            
            // Hide the table
            this.table.style.display = 'none';
        } else {
            // Show the table
            this.table.style.display = '';
        }
    }
    
    /**
     * Sort the table by a column
     * @param {number} columnIndex - The index of the column to sort by
     */
    sortBy(columnIndex) {
        // If already sorting by this column, toggle direction
        if (this.sortColumn === columnIndex) {
            this.sortDirection = this.sortDirection === 'asc' ? 'desc' : 'asc';
        } else {
            this.sortColumn = columnIndex;
            this.sortDirection = 'asc';
        }
        
        // Update header appearance
        const headers = this.table.querySelectorAll('thead th');
        headers.forEach((header, index) => {
            // Skip the selection column
            if (this.options.selectable && index === 0) return;
            
            // Remove existing sort classes
            header.classList.remove('sort-asc', 'sort-desc');
            
            // Update sort indicator
            const indicator = header.querySelector('.sort-indicator');
            if (indicator) {
                indicator.innerHTML = '⇵';
            }
            
            // Add class to sorted column
            if (index === columnIndex) {
                header.classList.add(`sort-${this.sortDirection}`);
                if (indicator) {
                    indicator.innerHTML = this.sortDirection === 'asc' ? '↑' : '↓';
                }
            }
        });
        
        this.processData();
        this.render();
    }
    
    /**
     * Toggle selection status of all rows
     * @param {boolean} selected - Whether to select or deselect all rows
     */
    toggleSelectAll(selected) {
        if (selected) {
            this.filteredData.forEach(row => {
                this.selectedRows.add(row.element);
            });
        } else {
            this.selectedRows.clear();
        }
        
        this.updateCheckboxes();
        
        // Trigger selection change event
        this.triggerSelectionChangeEvent();
    }
    
    /**
     * Toggle selection status of a single row
     * @param {HTMLElement} row - The row element
     * @param {boolean} selected - Whether to select or deselect the row
     */
    toggleRowSelection(row, selected) {
        if (selected) {
            this.selectedRows.add(row);
        } else {
            this.selectedRows.delete(row);
        }
        
        // Update header checkbox
        this.updateHeaderCheckbox();
        
        // Trigger selection change event
        this.triggerSelectionChangeEvent();
    }
    
    /**
     * Update all checkboxes based on selection state
     */
    updateCheckboxes() {
        // Update row checkboxes
        this.tableData.forEach(row => {
            const checkbox = row.element.querySelector('td.selection-column input[type="checkbox"]');
            if (checkbox) {
                checkbox.checked = this.selectedRows.has(row.element);
            }
        });
        
        // Update header checkbox
        this.updateHeaderCheckbox();
    }
    
    /**
     * Update the state of the header checkbox
     */
    updateHeaderCheckbox() {
        const headerCheckbox = this.table.querySelector('th.selection-column input[type="checkbox"]');
        if (!headerCheckbox) return;
        
        const visibleRows = this.filteredData.map(row => row.element);
        const selectedVisibleRows = Array.from(this.selectedRows).filter(row => 
            visibleRows.includes(row)
        );
        
        headerCheckbox.checked = visibleRows.length > 0 && selectedVisibleRows.length === visibleRows.length;
        headerCheckbox.indeterminate = selectedVisibleRows.length > 0 && selectedVisibleRows.length < visibleRows.length;
    }
    
    /**
     * Trigger a custom event when selection changes
     */
    triggerSelectionChangeEvent() {
        const event = new CustomEvent('selectionchange', {
            detail: {
                selectedRows: Array.from(this.selectedRows)
            }
        });
        
        this.table.dispatchEvent(event);
    }
    
    /**
     * Get the currently selected rows
     * @returns {Array} - Array of selected row elements
     */
    getSelectedRows() {
        return Array.from(this.selectedRows);
    }
    
    /**
     * Refresh the table after data changes
     */
    refresh() {
        this.processData();
        this.render();
    }
}

// Export the DataTableComponent class
window.DataTableComponent = DataTableComponent; 
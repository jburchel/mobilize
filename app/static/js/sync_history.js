/**
 * Sync History JavaScript
 * 
 * Handles the functionality of the sync history page,
 * including DataTable initialization and filtering.
 */

document.addEventListener('DOMContentLoaded', function() {
    // Initialize DataTable
    initializeDataTable();
    
    // Set up filter dropdown
    setupFilterDropdown();
});

/**
 * Initialize the DataTable for sync history
 */
function initializeDataTable() {
    const table = $('#history-table').DataTable({
        pageLength: 10,
        order: [[2, 'desc']], // Sort by date descending
        columnDefs: [
            { orderable: false, targets: -1 } // Disable sorting on details column
        ],
        language: {
            search: "Search history:",
            lengthMenu: "Show _MENU_ entries per page",
            info: "Showing _START_ to _END_ of _TOTAL_ entries",
            infoEmpty: "No history entries available",
            emptyTable: "No history entries found"
        }
    });
    
    // Add search box class
    $('.dataTables_filter input').addClass('form-control');
    
    // Add pagination classes
    $('.dataTables_paginate').addClass('mt-3');
    $('.paginate_button').addClass('btn btn-sm');
}

/**
 * Set up the filter dropdown functionality
 */
function setupFilterDropdown() {
    const filterDropdown = document.getElementById('sync-type-filter');
    
    if (filterDropdown) {
        filterDropdown.addEventListener('change', function() {
            const selectedValue = this.value;
            const urlParams = new URLSearchParams(window.location.search);
            
            if (selectedValue === 'all') {
                urlParams.delete('type');
            } else {
                urlParams.set('type', selectedValue);
            }
            
            // Redirect to filtered URL
            window.location.href = `${window.location.pathname}?${urlParams.toString()}`;
        });
        
        // Set initial value based on URL param
        const urlParams = new URLSearchParams(window.location.search);
        const typeParam = urlParams.get('type');
        
        if (typeParam) {
            filterDropdown.value = typeParam;
        }
    }
}

/**
 * Format duration in seconds to human-readable format
 */
function formatDuration(seconds) {
    if (!seconds || isNaN(seconds)) {
        return 'N/A';
    }
    
    if (seconds < 60) {
        return `${Math.round(seconds)} sec`;
    } else if (seconds < 3600) {
        const minutes = Math.floor(seconds / 60);
        const remainingSeconds = Math.round(seconds % 60);
        return `${minutes} min ${remainingSeconds} sec`;
    } else {
        const hours = Math.floor(seconds / 3600);
        const remainingMinutes = Math.floor((seconds % 3600) / 60);
        return `${hours} hr ${remainingMinutes} min`;
    }
} 
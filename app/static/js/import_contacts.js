/**
 * Google Contact Import Wizard JavaScript
 * 
 * Handles the functionality of the contact import wizard,
 * including selection, pagination, and continuing to the mapping step.
 */

document.addEventListener('DOMContentLoaded', function() {
    // Initialize DataTable
    initializeDataTable();
    
    // Set up select all functionality
    setupSelectAll();
    
    // Set up continue button state
    updateContinueButtonState();
    
    // Set up checkbox change listeners
    setupCheckboxListeners();
});

/**
 * Initialize the DataTable for contacts
 */
function initializeDataTable() {
    const table = $('#contacts-table').DataTable({
        pageLength: 25,
        order: [[1, 'asc']], // Sort by name
        columnDefs: [
            { orderable: false, targets: 0 } // Disable sorting on checkbox column
        ],
        language: {
            search: "Search contacts:",
            lengthMenu: "Show _MENU_ contacts per page",
            info: "Showing _START_ to _END_ of _TOTAL_ contacts",
            infoEmpty: "No contacts available",
            emptyTable: "No contacts found"
        }
    });
    
    // Add search box class
    $('.dataTables_filter input').addClass('form-control');
    
    // Add pagination classes
    $('.dataTables_paginate').addClass('mt-3');
    $('.paginate_button').addClass('btn btn-sm');
}

/**
 * Set up "Select All" checkbox functionality
 */
function setupSelectAll() {
    const selectAllCheckbox = document.getElementById('select-all');
    
    if (selectAllCheckbox) {
        selectAllCheckbox.addEventListener('change', function() {
            const isChecked = this.checked;
            document.querySelectorAll('input[name="contact[]"]').forEach(checkbox => {
                checkbox.checked = isChecked;
            });
            
            updateContinueButtonState();
        });
    }
}

/**
 * Set up individual checkbox change listeners
 */
function setupCheckboxListeners() {
    document.querySelectorAll('input[name="contact[]"]').forEach(checkbox => {
        checkbox.addEventListener('change', function() {
            updateContinueButtonState();
            updateSelectAllCheckbox();
        });
    });
}

/**
 * Update the state of the "Select All" checkbox
 */
function updateSelectAllCheckbox() {
    const selectAllCheckbox = document.getElementById('select-all');
    const checkboxes = document.querySelectorAll('input[name="contact[]"]');
    const checkedCount = document.querySelectorAll('input[name="contact[]"]:checked').length;
    
    if (selectAllCheckbox) {
        // Set to checked if all checkboxes are checked
        selectAllCheckbox.checked = checkedCount === checkboxes.length;
        
        // Set to indeterminate if some (but not all) are checked
        selectAllCheckbox.indeterminate = checkedCount > 0 && checkedCount < checkboxes.length;
    }
}

/**
 * Update the state of the continue button based on selections
 */
function updateContinueButtonState() {
    const continueButton = document.getElementById('continue-button');
    const checkedCount = document.querySelectorAll('input[name="contact[]"]:checked').length;
    
    if (continueButton) {
        if (checkedCount > 0) {
            continueButton.removeAttribute('disabled');
            
            // Update the button text to show count
            continueButton.textContent = `Continue with ${checkedCount} Contact${checkedCount !== 1 ? 's' : ''}`;
        } else {
            continueButton.setAttribute('disabled', 'disabled');
            continueButton.textContent = 'Continue to Mapping';
        }
    }
}

/**
 * Handle form submission for selected contacts
 */
function submitSelectedContacts() {
    const form = document.getElementById('import-form');
    
    if (form) {
        // Get all checked checkboxes
        const checkedBoxes = document.querySelectorAll('input[name="contact[]"]:checked');
        
        if (checkedBoxes.length === 0) {
            alert('Please select at least one contact to import.');
            return false;
        }
        
        // Submit the form
        form.submit();
    }
    
    return true;
} 
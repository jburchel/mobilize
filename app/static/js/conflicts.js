/**
 * Google Conflicts Resolution JavaScript
 * 
 * Handles the functionality of the conflicts resolution page,
 * including toggling merge options and form submission.
 */

document.addEventListener('DOMContentLoaded', function() {
    // Set up resolution option change listeners
    setupResolutionOptions();
    
    // Set up form submission
    setupFormSubmission();
});

/**
 * Set up change listeners for resolution radio buttons
 */
function setupResolutionOptions() {
    document.querySelectorAll('input[name^="resolution"]').forEach(radio => {
        radio.addEventListener('change', function() {
            const contactId = this.name.match(/resolution\[(\d+)\]/)[1];
            toggleMergeOptions(contactId, this.value);
        });
    });
    
    // Initialize merge options visibility
    document.querySelectorAll('input[name^="resolution"]:checked').forEach(radio => {
        const contactId = radio.name.match(/resolution\[(\d+)\]/)[1];
        toggleMergeOptions(contactId, radio.value);
    });
}

/**
 * Toggle visibility of merge options based on selected resolution
 */
function toggleMergeOptions(contactId, resolution) {
    const mergeOptionsContainer = document.getElementById(`merge-options-${contactId}`);
    
    if (mergeOptionsContainer) {
        if (resolution === 'merge') {
            mergeOptionsContainer.classList.remove('d-none');
        } else {
            mergeOptionsContainer.classList.add('d-none');
        }
    }
}

/**
 * Set up form submission with validation
 */
function setupFormSubmission() {
    const form = document.getElementById('conflicts-form');
    
    if (form) {
        form.addEventListener('submit', function(event) {
            // Check if all conflicts have a resolution selected
            const unresolved = document.querySelectorAll('.conflict-card').length - 
                               document.querySelectorAll('input[name^="resolution"]:checked').length;
            
            if (unresolved > 0) {
                event.preventDefault();
                alert(`Please select a resolution for all ${unresolved} remaining conflict(s).`);
                return false;
            }
            
            // Additional validation for merge options
            const mergeSelections = document.querySelectorAll('input[name^="resolution"]:checked[value="merge"]');
            let valid = true;
            
            mergeSelections.forEach(radio => {
                const contactId = radio.name.match(/resolution\[(\d+)\]/)[1];
                const mergeOptionsContainer = document.getElementById(`merge-options-${contactId}`);
                
                // Check if all merge fields have a selection
                const fields = mergeOptionsContainer.querySelectorAll('input[name^="field_choice"]');
                const selectedFields = mergeOptionsContainer.querySelectorAll('input[name^="field_choice"]:checked');
                
                if (fields.length !== selectedFields.length) {
                    valid = false;
                    alert(`Please select options for all fields in conflict ${contactId}.`);
                    return;
                }
            });
            
            if (!valid) {
                event.preventDefault();
                return false;
            }
            
            // Continue with form submission
            return true;
        });
    }
}

/**
 * Select all fields from one source (local or Google)
 */
function selectAllFrom(contactId, source) {
    const mergeOptionsContainer = document.getElementById(`merge-options-${contactId}`);
    
    if (mergeOptionsContainer) {
        mergeOptionsContainer.querySelectorAll(`input[value="${source}"]`).forEach(radio => {
            radio.checked = true;
        });
    }
} 
/**
 * Pipeline Stage Color Display Helper
 * This script ensures stage colors are properly displayed in various UI layouts
 */
document.addEventListener('DOMContentLoaded', function() {
    console.log('Pipeline color helper script loaded');
    
    // Add color indicators to pipeline stages in simplified view
    function addPipelineStageColors() {
        // Target table rows in the pipeline stages view
        const stageItems = document.querySelectorAll('tr, [data-stage-id], .stage-item');
        console.log(`Found ${stageItems.length} stage items to process`);
        
        stageItems.forEach(function(item) {
            const stageId = item.getAttribute('data-stage-id') || 
                           (item.id && item.id.includes('stage-') ? item.id.split('stage-')[1] : null);
            
            if (!stageId) return;
            
            // Try to get the color from the data attribute
            let stageColor = item.getAttribute('data-color');
            
            // If no color found, try to find it in stageList
            if (!stageColor) {
                const matchingStage = document.querySelector(`.stage-item[data-stage-id="${stageId}"]`);
                if (matchingStage) {
                    stageColor = matchingStage.getAttribute('data-color');
                }
            }
            
            if (stageColor) {
                console.log(`Adding color ${stageColor} to stage ${stageId}`);
                
                // Add left border with stage color
                item.style.borderLeft = `6px solid ${stageColor}`;
                
                // Add color dot if this is a table row
                if (item.tagName === 'TR') {
                    const firstCell = item.querySelector('td:first-child');
                    if (firstCell) {
                        const colorDot = document.createElement('span');
                        colorDot.className = 'pipeline-stage-color-indicator';
                        colorDot.style.backgroundColor = stageColor;
                        colorDot.title = `Stage color: ${stageColor}`;
                        
                        // Insert at the beginning of the cell
                        if (firstCell.firstChild) {
                            firstCell.insertBefore(colorDot, firstCell.firstChild);
                        } else {
                            firstCell.appendChild(colorDot);
                        }
                    }
                }
            }
        });
        
        // Specifically check for the UI in the screenshot 
        // (targeting stage rows with ID/name/number)
        document.querySelectorAll('.pipeline-stages-table tr, #pipeline-stages tr').forEach(function(row) {
            // Try to find stage info
            const stageNameEl = row.querySelector('.stage-name, .stage-info');
            
            if (stageNameEl) {
                const stageName = stageNameEl.textContent.trim();
                console.log(`Found stage row for "${stageName}"`);
                
                // Look for color in any hidden inputs or data attributes
                let stageColor = row.getAttribute('data-color') || 
                               row.getAttribute('data-stage-color') ||
                               (row.querySelector('[data-color]') ? 
                                row.querySelector('[data-color]').getAttribute('data-color') : null);
                
                // If still no color, try to find matching stage by name
                if (!stageColor) {
                    const allStages = document.querySelectorAll('.stage-item, [data-stage-id]');
                    for (const stage of allStages) {
                        const nameEl = stage.querySelector('.stage-name');
                        if (nameEl && nameEl.textContent.trim() === stageName) {
                            stageColor = stage.getAttribute('data-color');
                            break;
                        }
                    }
                }
                
                // If we found a color, apply it
                if (stageColor) {
                    console.log(`Adding color ${stageColor} to stage "${stageName}"`);
                    
                    // Add border
                    row.style.borderLeft = `6px solid ${stageColor}`;
                    
                    // Add color indicator
                    const firstCell = row.querySelector('td:first-child');
                    if (firstCell) {
                        const colorDot = document.createElement('span');
                        colorDot.className = 'pipeline-stage-color-indicator';
                        colorDot.style.backgroundColor = stageColor;
                        
                        // Insert at beginning
                        if (firstCell.firstChild) {
                            firstCell.insertBefore(colorDot, firstCell.firstChild);
                        } else {
                            firstCell.appendChild(colorDot);
                        }
                    }
                }
            }
        });
    }
    
    // Run immediately
    addPipelineStageColors();
    
    // Also run after a short delay to make sure everything is loaded
    setTimeout(addPipelineStageColors, 500);
    
    // Add a MutationObserver to handle dynamically added stages
    const observer = new MutationObserver(function(mutations) {
        mutations.forEach(function(mutation) {
            if (mutation.type === 'childList' && mutation.addedNodes.length > 0) {
                // Check if any added nodes might be stage-related
                let hasRelevantChanges = false;
                
                mutation.addedNodes.forEach(function(node) {
                    if (node.nodeType === 1 && 
                        (node.classList.contains('stage-item') || 
                         node.hasAttribute('data-stage-id') ||
                         node.tagName === 'TR')) {
                        hasRelevantChanges = true;
                    }
                });
                
                if (hasRelevantChanges) {
                    console.log('Detected new stage items, updating colors');
                    addPipelineStageColors();
                }
            }
        });
    });
    
    // Start observing changes to the document
    observer.observe(document.body, { childList: true, subtree: true });
}); 
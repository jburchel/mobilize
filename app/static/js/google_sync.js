/**
 * Google Sync Dashboard JavaScript
 * 
 * Handles the dynamic functionality of the Google Sync dashboard,
 * including status updates, conflict counts, and sync operations.
 */

document.addEventListener('DOMContentLoaded', function() {
    // Initialize dashboard
    loadSyncStatus();
    loadConflictCount();
    
    // Set up interval for status update
    setInterval(loadSyncStatus, 10000); // Check status every 10 seconds
    
    // Set up event listeners for sync buttons
    initializeSyncButtons();
});

/**
 * Load sync status from the API
 */
function loadSyncStatus() {
    fetch('/api/v1/google-sync/status', {
        method: 'GET',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${getToken()}`
        }
    })
    .then(response => response.json())
    .then(data => {
        updateConnectionStatus(data.is_connected);
        updateLastSyncInfo(data.last_sync);
    })
    .catch(error => {
        console.error('Error fetching sync status:', error);
    });
}

/**
 * Load conflict count from the API
 */
function loadConflictCount() {
    fetch('/api/v1/google-sync/conflicts/count', {
        method: 'GET',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${getToken()}`
        }
    })
    .then(response => response.json())
    .then(data => {
        updateConflictCount(data.count);
    })
    .catch(error => {
        console.error('Error fetching conflict count:', error);
    });
}

/**
 * Update the connection status in the UI
 */
function updateConnectionStatus(isConnected) {
    const statusElement = document.getElementById('connection-status');
    const statusIconElement = document.getElementById('connection-status-icon');
    const connectButton = document.getElementById('connect-button');
    
    if (isConnected) {
        statusElement.textContent = 'Connected';
        statusElement.classList.remove('text-danger');
        statusElement.classList.add('text-success');
        
        statusIconElement.classList.remove('bi-x-circle-fill', 'text-danger');
        statusIconElement.classList.add('bi-check-circle-fill', 'text-success');
        
        connectButton.textContent = 'Reconnect';
        
        // Enable sync buttons
        document.querySelectorAll('.sync-action-button').forEach(button => {
            button.removeAttribute('disabled');
        });
    } else {
        statusElement.textContent = 'Not Connected';
        statusElement.classList.remove('text-success');
        statusElement.classList.add('text-danger');
        
        statusIconElement.classList.remove('bi-check-circle-fill', 'text-success');
        statusIconElement.classList.add('bi-x-circle-fill', 'text-danger');
        
        connectButton.textContent = 'Connect';
        
        // Disable sync buttons
        document.querySelectorAll('.sync-action-button').forEach(button => {
            button.setAttribute('disabled', 'disabled');
        });
    }
}

/**
 * Update the last sync information in the UI
 */
function updateLastSyncInfo(lastSync) {
    const lastSyncElement = document.getElementById('last-sync-info');
    
    if (lastSync) {
        const date = new Date(lastSync.end_time || lastSync.start_time);
        const formattedDate = date.toLocaleString();
        const syncType = formatSyncType(lastSync.type);
        const status = formatSyncStatus(lastSync.status);
        
        lastSyncElement.innerHTML = `
            <div>Type: <span class="fw-bold">${syncType}</span></div>
            <div>Status: <span class="fw-bold">${status}</span></div>
            <div>Time: <span class="fw-bold">${formattedDate}</span></div>
        `;
    } else {
        lastSyncElement.innerHTML = '<div class="text-muted">No sync data available</div>';
    }
}

/**
 * Update the conflict count in the UI
 */
function updateConflictCount(count) {
    const conflictCountElement = document.getElementById('conflict-count');
    const conflictBadge = document.getElementById('conflict-badge');
    
    if (conflictCountElement) {
        conflictCountElement.textContent = count;
    }
    
    if (conflictBadge) {
        conflictBadge.textContent = count;
        
        if (count > 0) {
            conflictBadge.classList.remove('d-none');
        } else {
            conflictBadge.classList.add('d-none');
        }
    }
}

/**
 * Initialize sync action buttons
 */
function initializeSyncButtons() {
    // Sync Contacts button
    const syncContactsButton = document.getElementById('sync-contacts-button');
    if (syncContactsButton) {
        syncContactsButton.addEventListener('click', function() {
            startSync('contacts');
        });
    }
    
    // Sync Calendar button
    const syncCalendarButton = document.getElementById('sync-calendar-button');
    if (syncCalendarButton) {
        syncCalendarButton.addEventListener('click', function() {
            startSync('calendar');
        });
    }
    
    // Sync Email button
    const syncEmailButton = document.getElementById('sync-email-button');
    if (syncEmailButton) {
        syncEmailButton.addEventListener('click', function() {
            startSync('email');
        });
    }
    
    // Import Contacts button
    const importContactsButton = document.getElementById('import-contacts-button');
    if (importContactsButton) {
        importContactsButton.addEventListener('click', function() {
            window.location.href = '/google-sync/import-contacts';
        });
    }
    
    // Resolve Conflicts button
    const resolveConflictsButton = document.getElementById('resolve-conflicts-button');
    if (resolveConflictsButton) {
        resolveConflictsButton.addEventListener('click', function() {
            window.location.href = '/google-sync/conflicts';
        });
    }
}

/**
 * Start a sync operation
 */
function startSync(type) {
    // Show loading state
    const button = document.getElementById(`sync-${type}-button`);
    const originalText = button.innerHTML;
    button.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Syncing...';
    button.disabled = true;
    
    // Call the API
    fetch('/api/v1/google-sync/sync', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${getToken()}`
        },
        body: JSON.stringify({ type: type })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Show success message
            showNotification('Sync completed successfully', 'success');
            
            // Refresh data
            loadSyncStatus();
            loadConflictCount();
        } else {
            // Show error message
            showNotification(`Sync failed: ${data.error}`, 'danger');
        }
    })
    .catch(error => {
        console.error(`Error syncing ${type}:`, error);
        showNotification(`Error syncing ${type}`, 'danger');
    })
    .finally(() => {
        // Restore button state
        button.innerHTML = originalText;
        button.disabled = false;
    });
}

/**
 * Show a notification message
 */
function showNotification(message, type = 'info') {
    const alertContainer = document.getElementById('alert-container');
    
    if (!alertContainer) {
        console.error('Alert container not found');
        return;
    }
    
    const alert = document.createElement('div');
    alert.className = `alert alert-${type} alert-dismissible fade show`;
    alert.role = 'alert';
    alert.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    `;
    
    alertContainer.appendChild(alert);
    
    // Auto-dismiss after 5 seconds
    setTimeout(() => {
        alert.classList.remove('show');
        setTimeout(() => {
            alertContainer.removeChild(alert);
        }, 150);
    }, 5000);
}

/**
 * Format sync type for display
 */
function formatSyncType(type) {
    if (!type) return 'Unknown';
    
    const typeMap = {
        'contacts_sync': 'Contacts Sync',
        'contacts_import': 'Contacts Import',
        'calendar_sync': 'Calendar Sync',
        'email_sync': 'Email Sync',
        'conflicts_resolution': 'Conflicts Resolution'
    };
    
    return typeMap[type] || type.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
}

/**
 * Format sync status for display
 */
function formatSyncStatus(status) {
    if (!status) return 'Unknown';
    
    const statusMap = {
        'in_progress': 'In Progress',
        'completed': 'Completed',
        'failed': 'Failed'
    };
    
    return statusMap[status] || status.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
}

/**
 * Get JWT token from localStorage
 */
function getToken() {
    return localStorage.getItem('access_token');
} 
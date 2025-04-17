// Debounce function to limit API calls
function debounce(func, wait) {
    let timeout;
    return function() {
        const context = this;
        const args = arguments;
        clearTimeout(timeout);
        timeout = setTimeout(() => {
            func.apply(context, args);
        }, wait);
    };
}

// Initialize search functionality for people list
function initializePeopleSearch() {
    const searchInput = document.getElementById('tableSearch');
    const clearSearchBtn = document.getElementById('clearSearch');
    const tableBody = document.querySelector('#peopleTable tbody');
    const visibleCountElement = document.getElementById('visibleCount');

    if (!searchInput || !tableBody) return;

    async function searchPeople() {
        const searchTerm = searchInput.value.trim();
        
        // Show/hide clear button
        if (clearSearchBtn) {
            clearSearchBtn.style.display = searchTerm ? 'block' : 'none';
        }
        
        try {
            // Build query parameters
            const params = new URLSearchParams();
            if (searchTerm) params.append('q', searchTerm);
            
            // Call API
            const response = await fetch(`/people/search?${params.toString()}`);
            
            if (!response.ok) {
                throw new Error(`Search request failed with status ${response.status}`);
            }
            
            const people = await response.json();
            
            // Clear table
            tableBody.innerHTML = '';
            
            // Update visible count
            if (visibleCountElement) {
                visibleCountElement.textContent = people.length;
            }
            
            if (people.length === 0) {
                // Show no results message
                const noResultsRow = document.createElement('tr');
                noResultsRow.innerHTML = '<td colspan="7" class="text-center">No people match your search criteria.</td>';
                tableBody.appendChild(noResultsRow);
                return;
            }
            
            // Populate table with results
            people.forEach(person => {
                const row = document.createElement('tr');
                
                // Create initials for avatar
                const firstInitial = person.first_name ? person.first_name[0] : '';
                const lastInitial = person.last_name ? person.last_name[0] : '';
                const initials = firstInitial + lastInitial;
                
                // Determine avatar background color based on priority
                const bgColor = person.priority === 'HIGH' ? 'var(--bs-primary)' : 
                               person.priority === 'MEDIUM' ? 'var(--bs-info)' : 
                               'var(--bs-secondary)';
                
                row.innerHTML = `
                    <td>
                        <div class="table-user">
                            <div class="table-user-avatar" style="background-color: ${bgColor};">
                                ${initials}
                            </div>
                            <div class="table-user-info">
                                <a href="/people/${person.id}" class="text-decoration-none">
                                    <div class="table-user-name">${person.first_name} ${person.last_name}</div>
                                    <div class="table-user-title">${person.role || 'Contact'}</div>
                                </a>
                            </div>
                        </div>
                    </td>
                    <td>${person.email || ''}</td>
                    <td>${person.phone || ''}</td>
                    <td>
                        ${person.people_pipeline ? 
                            `<span class="badge badge-${getBadgeColorForPipeline(person.people_pipeline)}">
                                ${person.people_pipeline}
                            </span>` : 
                            '<span class="badge badge-secondary">None</span>'}
                    </td>
                    <td>
                        ${person.priority ? 
                            `<span class="badge badge-${getBadgeColorForPriority(person.priority)}">
                                ${person.priority}
                            </span>` : 
                            '<span class="badge badge-secondary">Not Set</span>'}
                    </td>
                    <td>${person.last_contact_date || ''}</td>
                    <td>
                        <div class="table-actions">
                            <a href="/people/${person.id}/edit" class="btn-icon btn-sm" aria-label="Edit">
                                <i class="bi bi-pencil"></i>
                            </a>
                            <form action="/people/${person.id}/delete" method="POST" class="d-inline" 
                                  onsubmit="return confirm('Are you sure you want to delete this person?');">
                                <input type="hidden" name="csrf_token" value="${document.querySelector('meta[name="csrf-token"]')?.content || ''}">
                                <button type="submit" class="btn-icon btn-sm" aria-label="Delete">
                                    <i class="bi bi-trash"></i>
                                </button>
                            </form>
                        </div>
                    </td>
                `;
                
                tableBody.appendChild(row);
            });
            
        } catch (error) {
            console.error('Search error:', error);
            tableBody.innerHTML = '<tr><td colspan="7" class="text-center text-danger">Error loading search results. Please try again.</td></tr>';
        }
    }

    // Add event listeners
    searchInput.addEventListener('input', debounce(searchPeople, 300));
    
    // Clear search button
    if (clearSearchBtn) {
        clearSearchBtn.addEventListener('click', function() {
            searchInput.value = '';
            searchPeople();
        });
    }
}

// Initialize search functionality for churches list
function initializeChurchesSearch() {
    const searchInput = document.getElementById('tableSearch');
    const clearSearchBtn = document.getElementById('clearSearch');
    const tableBody = document.querySelector('table tbody');
    const visibleCountElement = document.getElementById('visibleCount');

    if (!searchInput || !tableBody) return;

    async function searchChurches() {
        const searchTerm = searchInput.value.trim();
        
        // Show/hide clear button
        if (clearSearchBtn) {
            clearSearchBtn.style.display = searchTerm ? 'block' : 'none';
        }
        
        try {
            // Build query parameters
            const params = new URLSearchParams();
            if (searchTerm) params.append('q', searchTerm);
            
            // Call API
            const response = await fetch(`/churches/search?${params.toString()}`);
            
            if (!response.ok) {
                throw new Error(`Search request failed with status ${response.status}`);
            }
            
            const churches = await response.json();
            
            // Clear table
            tableBody.innerHTML = '';
            
            // Update visible count
            if (visibleCountElement) {
                visibleCountElement.textContent = churches.length;
            }
            
            if (churches.length === 0) {
                // Show no results message
                const noResultsRow = document.createElement('tr');
                noResultsRow.innerHTML = '<td colspan="7" class="text-center">No churches match your search criteria.</td>';
                tableBody.appendChild(noResultsRow);
                return;
            }
            
            // Populate table with results
            churches.forEach(church => {
                const row = document.createElement('tr');
                
                // Create church initial
                const initials = church.name ? church.name.substring(0, 2) : '';
                
                row.innerHTML = `
                    <td>
                        <div class="table-user">
                            <div class="table-user-avatar" style="background-color: var(--color-primary-blue);">
                                ${initials}
                            </div>
                            <div class="table-user-info">
                                <a href="/churches/${church.id}" class="text-decoration-none">
                                    <div class="table-user-name">${church.name}</div>
                                    <div class="table-user-title">${church.type || 'Church'}</div>
                                </a>
                            </div>
                        </div>
                    </td>
                    <td>${formatLocation(church)}</td>
                    <td>${church.main_contact ? church.main_contact.full_name : 'Not Set'}</td>
                    <td>
                        <span class="badge badge-secondary">${church.denomination || 'Not Set'}</span>
                    </td>
                    <td>
                        ${formatPipelineBadge(church.pipeline_stage)}
                    </td>
                    <td>
                        ${church.email ? `<a href="mailto:${church.email}" class="me-2" title="Email"><i class="bi bi-envelope"></i></a>` : ''}
                        ${church.phone ? `<a href="tel:${church.phone}" class="me-2" title="Call"><i class="bi bi-telephone"></i></a>` : ''}
                        ${church.website ? `<a href="${church.website}" target="_blank" title="Website"><i class="bi bi-globe"></i></a>` : ''}
                    </td>
                    <td>
                        <div class="table-actions">
                            <a href="/churches/${church.id}/edit" class="btn-icon btn-sm" aria-label="Edit">
                                <i class="bi bi-pencil"></i>
                            </a>
                            <form action="/churches/${church.id}/delete" method="POST" class="d-inline" 
                                  onsubmit="return confirm('Are you sure you want to delete this church?');">
                                <input type="hidden" name="csrf_token" value="${document.querySelector('meta[name="csrf-token"]')?.content || ''}">
                                <button type="submit" class="btn-icon btn-sm" aria-label="Delete">
                                    <i class="bi bi-trash"></i>
                                </button>
                            </form>
                        </div>
                    </td>
                `;
                
                tableBody.appendChild(row);
            });
            
        } catch (error) {
            console.error('Search error:', error);
            tableBody.innerHTML = '<tr><td colspan="7" class="text-center text-danger">Error loading search results. Please try again.</td></tr>';
        }
    }

    // Add event listeners
    searchInput.addEventListener('input', debounce(searchChurches, 300));
    
    // Clear search button
    if (clearSearchBtn) {
        clearSearchBtn.addEventListener('click', function() {
            searchInput.value = '';
            searchChurches();
        });
    }
}

// Helper functions
function getBadgeColorForPipeline(pipeline) {
    switch(pipeline) {
        case 'PROMOTION': return 'primary';
        case 'INFORMATION': return 'success';
        case 'INVITATION': return 'warning';
        case 'CONFIRMATION': return 'info';
        case 'AUTOMATION': return 'secondary';
        default: return 'secondary';
    }
}

function getBadgeColorForPriority(priority) {
    switch(priority) {
        case 'URGENT': return 'danger';
        case 'HIGH': return 'danger';
        case 'MEDIUM': return 'warning';
        case 'LOW': return 'success';
        default: return 'secondary';
    }
}

function formatLocation(church) {
    const parts = [];
    if (church.city) parts.push(church.city);
    if (church.state) parts.push(church.state);
    if (parts.length === 0 && church.location) return church.location;
    return parts.join(', ');
}

function formatPipelineBadge(pipeline) {
    if (!pipeline) return '<span class="badge bg-light text-dark">Not Set</span>';

    const badgeColors = {
        'INFORMATION': 'bg-info',
        'PROMOTION': 'bg-primary',
        'INVITATION': 'bg-warning',
        'CONFIRMATION': 'bg-success',
        'EN42': 'bg-secondary',
        'AUTOMATION': 'bg-dark'
    };

    const color = badgeColors[pipeline] || 'bg-secondary';
    const label = pipeline.replace(/_/g, ' ').toLowerCase()
        .replace(/\b\w/g, l => l.toUpperCase());
    
    return `<span class="badge ${color}">${label}</span>`;
}

// Initialize search on page load
document.addEventListener('DOMContentLoaded', function() {
    // Check which page we're on and initialize appropriate search
    if (document.getElementById('peopleTable')) {
        initializePeopleSearch();
    } else if (document.querySelector('table') && document.getElementById('tableSearch')) {
        initializeChurchesSearch();
    }
}); 
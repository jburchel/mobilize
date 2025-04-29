// Drag-and-drop pipeline logic for People
export default {
    init() {
        // Find all table rows representing people
        const rows = document.querySelectorAll('#peopleTable tbody tr');
        rows.forEach(row => {
            row.setAttribute('draggable', 'true');
            row.addEventListener('dragstart', this.handleDragStart);
        });

        // Find all pipeline stage cells
        const stageCells = document.querySelectorAll('#peopleTable td:nth-child(4)');
        stageCells.forEach(cell => {
            cell.addEventListener('dragover', this.handleDragOver);
            cell.addEventListener('drop', this.handleDrop);
        });
    },

    handleDragStart(e) {
        e.dataTransfer.setData('text/plain', e.target.rowIndex);
        e.dataTransfer.effectAllowed = 'move';
    },

    handleDragOver(e) {
        e.preventDefault();
        e.dataTransfer.dropEffect = 'move';
    },

    handleDrop(e) {
        e.preventDefault();
        const draggedRowIndex = e.dataTransfer.getData('text/plain');
        const table = document.getElementById('peopleTable');
        const draggedRow = table.rows[draggedRowIndex];
        const targetCell = e.target.closest('td');
        const targetRow = targetCell.parentElement;
        const personId = draggedRow.querySelector('a').href.split('/').pop();
        const newStage = targetCell.textContent.trim();

        // Send AJAX request to update stage
        fetch(`/api/v1/people/${personId}/stage`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-Requested-With': 'XMLHttpRequest',
            },
            body: JSON.stringify({ stage: newStage })
        })
        .then(response => {
            if (!response.ok) throw new Error('Failed to update stage');
            return response.json();
        })
        .then(data => {
            // Optionally update the UI or reload the page/section
            window.location.reload();
        })
        .catch(err => {
            alert('Error updating stage: ' + err.message);
        });
    }
}; 
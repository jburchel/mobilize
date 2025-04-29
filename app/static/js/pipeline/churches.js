// Drag-and-drop pipeline logic for Churches
export default {
    init() {
        // Find all table rows representing churches
        const rows = document.querySelectorAll('table tbody tr');
        rows.forEach(row => {
            row.setAttribute('draggable', 'true');
            row.addEventListener('dragstart', this.handleDragStart);
        });

        // Find all pipeline stage cells (5th column for churches)
        const stageCells = document.querySelectorAll('table td:nth-child(5)');
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
        const table = document.querySelector('table');
        const draggedRow = table.rows[draggedRowIndex];
        const targetCell = e.target.closest('td');
        const targetRow = targetCell.parentElement;
        const churchId = draggedRow.querySelector('a').href.split('/').pop();
        const newStage = targetCell.textContent.trim();

        // Send AJAX request to update stage
        fetch(`/api/v1/churches/${churchId}/stage`, {
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
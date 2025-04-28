// Global handler for .email-link clicks to open the in-app email modal

document.addEventListener('DOMContentLoaded', function() {
    document.body.addEventListener('click', function(e) {
        const target = e.target.closest('.email-link');
        if (target) {
            e.preventDefault();
            const email = target.getAttribute('data-email');
            const name = target.getAttribute('data-name');
            const id = target.getAttribute('data-id');
            const type = target.getAttribute('data-type');
            openEmailDialog(email, name, id, type);
        }
    });
});

function openEmailDialog(email, name, id, type) {
    // Compose URL for AJAX load
    let url = '/communications/compose?modal=1&';
    if (type === 'person') {
        url += 'person_id=' + encodeURIComponent(id);
    } else if (type === 'church') {
        url += 'church_id=' + encodeURIComponent(id);
    }
    // Optionally add email/name as fallback
    url += '&email=' + encodeURIComponent(email);
    url += '&name=' + encodeURIComponent(name);

    // Use ModalComponent if available
    if (window.ModalComponent) {
        const modal = new ModalComponent({
            title: 'Send Email',
            contentType: 'ajax',
            content: url,
            size: 'large',
            closeButton: true
        });
        modal.show();
        modal.loadAjaxContent(url);
    } else {
        // Fallback: load content and inject into #global-email-modal-container
        fetch(url)
            .then(res => res.text())
            .then(html => {
                let container = document.getElementById('global-email-modal-container');
                container.innerHTML = html;
                // Try to show the modal (assume Bootstrap modal markup)
                const modalEl = container.querySelector('.modal');
                if (modalEl && window.bootstrap) {
                    modalEl.classList.add('modal-lg'); // Ensure large modal
                    const modal = new window.bootstrap.Modal(modalEl);
                    modal.show();
                }
            });
    }
} 
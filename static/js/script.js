document.addEventListener("DOMContentLoaded", function() {
    // Dismiss loading animation window
    const spinner = document.getElementById('loading-spinner');
    if (spinner) {
        setTimeout(() => {
            spinner.style.opacity = '0';
            setTimeout(() => spinner.remove(), 300);
        }, 250);
    }

    // Dynamic Bootstrap Form Client-side Validations
    const forms = document.querySelectorAll('.needs-validation');
    Array.from(forms).forEach(form => {
        form.addEventListener('submit', event => {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }
            form.classList.add('was-validated');
        }, false);
    });
});

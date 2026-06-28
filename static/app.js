document.addEventListener('DOMContentLoaded', () => {
    // Add simple entry animations
    const elements = document.querySelectorAll('.card, .btn-primary');
    elements.forEach((el, index) => {
        el.style.opacity = '0';
        el.style.animation = `fadeIn 0.5s ease-out forwards ${index * 0.1}s`;
    });

    // Auto-hide flash messages after 5 seconds
    const flashMessages = document.querySelectorAll('.alert');
    flashMessages.forEach(msg => {
        setTimeout(() => {
            msg.style.transition = 'opacity 0.5s ease';
            msg.style.opacity = '0';
            setTimeout(() => msg.remove(), 500);
        }, 5000);
    });
});

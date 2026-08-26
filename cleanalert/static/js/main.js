function setupPasswordToggle(buttonId, fieldId, iconId) {
    const button = document.getElementById(buttonId);
    const field = document.getElementById(fieldId);
    const icon = document.getElementById(iconId);
    if (button && icon && field) {
        button.addEventListener('click', function () {
            const type = field.getAttribute('type') === 'password' ? 'text' : 'password';
            field.setAttribute('type', type);
            icon.classList.toggle('bi-eye');
            icon.classList.toggle('bi-eye-slash');
        });
    }
}
document.addEventListener('DOMContentLoaded', function () {
    setupPasswordToggle('toggle-password', 'password-field', 'toggle-password-icon');
    setupPasswordToggle('toggle-confirm', 'confirm-field', 'toggle-confirm-icon');
});
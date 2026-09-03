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

function validatePasswordRealtime(passwordFieldId, feedbackContainerId) {
    const passwordField = document.getElementById(passwordFieldId);
    const feedbackContainer = document.getElementById(feedbackContainerId);
    
    if (!passwordField || !feedbackContainer) return;
    
    passwordField.addEventListener('input', function () {
        const password = this.value;
        
        // Validation checks
        const hasUppercase = /[A-Z]/.test(password);
        const hasLowercase = /[a-z]/.test(password);
        const hasNumber = /[0-9]/.test(password);
        const hasSymbol = /[!@#$%^&*()_+\-=\[\]{}|;:\'",.<>?/\\]/.test(password);
        const hasMinLength = password.length >= 8;
        
        // Update requirement indicators
        updateRequirement(feedbackContainer, 'uppercase', hasUppercase);
        updateRequirement(feedbackContainer, 'lowercase', hasLowercase);
        updateRequirement(feedbackContainer, 'number', hasNumber);
        updateRequirement(feedbackContainer, 'symbol', hasSymbol);
        updateRequirement(feedbackContainer, 'length', hasMinLength);
        
        // Update password field styling
        const allValid = hasUppercase && hasLowercase && hasNumber && hasSymbol && hasMinLength;
        if (password.length > 0) {
            if (allValid) {
                passwordField.classList.remove('is-invalid');
                passwordField.classList.add('is-valid');
            } else {
                passwordField.classList.remove('is-valid');
                passwordField.classList.add('is-invalid');
            }
        } else {
            passwordField.classList.remove('is-valid', 'is-invalid');
        }
    });
}

function updateRequirement(container, requirementId, isValid) {
    const element = container.querySelector(`[data-requirement="${requirementId}"]`);
    if (element) {
        if (isValid) {
            element.classList.remove('requirement-invalid');
            element.classList.add('requirement-valid');
            element.querySelector('i').classList.remove('bi-x-circle');
            element.querySelector('i').classList.add('bi-check-circle');
        } else {
            element.classList.remove('requirement-valid');
            element.classList.add('requirement-invalid');
            element.querySelector('i').classList.remove('bi-check-circle');
            element.querySelector('i').classList.add('bi-x-circle');
        }
    }
}

document.addEventListener('DOMContentLoaded', function () {
    setupPasswordToggle('toggle-password', 'password-field', 'toggle-password-icon');
    setupPasswordToggle('toggle-confirm', 'confirm-field', 'toggle-confirm-icon');
    validatePasswordRealtime('password-field', 'password-feedback');
});
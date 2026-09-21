// Register Page JavaScript

document.addEventListener('DOMContentLoaded', function() {
    const registerForm = document.getElementById('registerForm');
    const usernameInput = document.getElementById('username');
    const passwordInput = document.getElementById('password');
    const confirmPasswordInput = document.getElementById('confirm_password');
    const errorMessage = document.getElementById('errorMessage');
    const successMessage = document.getElementById('successMessage');

    // Form submission handler
    registerForm.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        // Clear previous messages
        hideMessages();
        
        // Get form values
        const username = usernameInput.value.trim();
        const password = passwordInput.value.trim();
        const confirmPassword = confirmPasswordInput.value.trim();
        
        // Client-side validation
        if (!username) {
            showError('Please enter a username');
            usernameInput.focus();
            return;
        }
        
        if (username.length < 3) {
            showError('Username must be at least 3 characters long');
            usernameInput.focus();
            return;
        }
        
        if (username.length > 50) {
            showError('Username must be less than 50 characters');
            usernameInput.focus();
            return;
        }
        
        if (!password) {
            showError('Please enter a password');
            passwordInput.focus();
            return;
        }
        
        if (password.length < 6) {
            showError('Password must be at least 6 characters long');
            passwordInput.focus();
            return;
        }
        
        if (!confirmPassword) {
            showError('Please confirm your password');
            confirmPasswordInput.focus();
            return;
        }
        
        if (password !== confirmPassword) {
            showError('Passwords do not match');
            confirmPasswordInput.focus();
            confirmPasswordInput.classList.add('invalid');
            return;
        }
        
        // Disable form during submission
        const registerButton = registerForm.querySelector('.register-button');
        const originalButtonText = registerButton.innerHTML;
        registerButton.disabled = true;
        registerButton.innerHTML = '<span>CREATING ACCOUNT...</span>';
        
        try {
            // Send registration request to server
            const response = await fetch('/register', {
                method: 'POST',
                headers: { 'X-CSRFToken': document.querySelector('meta[name="csrf-token"]').getAttribute('content'),
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    username: username,
                    password: password,
                    confirm_password: confirmPassword
                })
            });
            
            const data = await response.json();
            
            if (response.ok && data.success) {
                // Registration successful
                showSuccess('Account created successfully! Redirecting...');
                
                // Clear form
                registerForm.reset();
                
                // Redirect after a short delay
                setTimeout(() => {
                    window.location.href = data.redirect || '/';
                }, 1500);
            } else {
                // Registration failed
                showError(data.message || 'Registration failed. Please try again.');
                registerButton.disabled = false;
                registerButton.innerHTML = originalButtonText;
            }
        } catch (error) {
            console.error('Registration error:', error);
            showError('An error occurred. Please try again later.');
            registerButton.disabled = false;
            registerButton.innerHTML = originalButtonText;
        }
    });
    
    // Real-time password match validation
    confirmPasswordInput.addEventListener('input', function() {
        const password = passwordInput.value;
        const confirmPassword = this.value;
        
        if (confirmPassword && password !== confirmPassword) {
            this.classList.remove('valid');
            this.classList.add('invalid');
        } else if (confirmPassword && password === confirmPassword) {
            this.classList.remove('invalid');
            this.classList.add('valid');
        } else {
            this.classList.remove('valid', 'invalid');
        }
    });
    
    // Input animations
    [usernameInput, passwordInput, confirmPasswordInput].forEach(input => {
        input.addEventListener('focus', function() {
            this.parentElement.style.transform = 'scale(1.02)';
        });
        
        input.addEventListener('blur', function() {
            this.parentElement.style.transform = 'scale(1)';
        });
        
        // Clear error on input
        input.addEventListener('input', function() {
            hideMessages();
            this.classList.remove('invalid');
        });
    });
    
    // Utility functions
    function showError(message) {
        errorMessage.textContent = message;
        errorMessage.style.display = 'block';
        successMessage.style.display = 'none';
        
        // Auto-hide after 5 seconds
        setTimeout(hideMessages, 5000);
    }
    
    function showSuccess(message) {
        successMessage.textContent = message;
        successMessage.style.display = 'block';
        errorMessage.style.display = 'none';
    }
    
    function hideMessages() {
        errorMessage.style.display = 'none';
        successMessage.style.display = 'none';
    }
    
    // Add keyboard shortcuts
    document.addEventListener('keydown', function(e) {
        // ESC to clear form
        if (e.key === 'Escape') {
            registerForm.reset();
            hideMessages();
            [usernameInput, passwordInput, confirmPasswordInput].forEach(input => {
                input.classList.remove('valid', 'invalid');
            });
        }
    });
    
    // Add smooth input transitions
    const style = document.createElement('style');
    style.textContent = `
        .input-wrapper {
            transition: transform 0.2s ease;
        }
    `;
    document.head.appendChild(style);
});


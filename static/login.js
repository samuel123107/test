// Login Page JavaScript

document.addEventListener('DOMContentLoaded', function() {
    const loginForm = document.getElementById('loginForm');
    const usernameInput = document.getElementById('username');
    const passwordInput = document.getElementById('password');
    const forgotPasswordLink = document.getElementById('forgotPasswordLink');
    const errorMessage = document.getElementById('errorMessage');
    const successMessage = document.getElementById('successMessage');
    const socialButtons = document.querySelectorAll('.social-button');

    // Form submission handler
    loginForm.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        // Clear previous messages
        hideMessages();
        
        // Get form values
        const username = usernameInput.value.trim();
        const password = passwordInput.value.trim();
        
        // Client-side validation
        if (!username) {
            showError('Please enter your username');
            usernameInput.focus();
            return;
        }
        
        if (!password) {
            showError('Please enter your password');
            passwordInput.focus();
            return;
        }
        
        if (password.length < 6) {
            showError('Password must be at least 6 characters long');
            passwordInput.focus();
            return;
        }
        
        // Disable form during submission
        const loginButton = loginForm.querySelector('.login-button');
        const originalButtonText = loginButton.innerHTML;
        loginButton.disabled = true;
        loginButton.innerHTML = '<span>LOGGING IN...</span>';
        
        try {
            // Send login request to server
            const response = await fetch('/login', {
                method: 'POST',
                headers: { 'X-CSRFToken': document.querySelector('meta[name="csrf-token"]').getAttribute('content'),
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    username: username,
                    password: password
                })
            });
            
            const data = await response.json();
            
            if (response.ok && data.success) {
                // Login successful
                showSuccess('Login successful! Redirecting...');
                
                // Redirect after a short delay
                setTimeout(() => {
                    window.location.href = data.redirect || '/';
                }, 1500);
            } else {
                // Login failed
                showError(data.message || 'Invalid username or password');
                loginButton.disabled = false;
                loginButton.innerHTML = originalButtonText;
            }
        } catch (error) {
            console.error('Login error:', error);
            showError('An error occurred. Please try again later.');
            loginButton.disabled = false;
            loginButton.innerHTML = originalButtonText;
        }
    });
    
    // Input animations and validations
    [usernameInput, passwordInput].forEach(input => {
        input.addEventListener('focus', function() {
            this.parentElement.style.transform = 'scale(1.02)';
        });
        
        input.addEventListener('blur', function() {
            this.parentElement.style.transform = 'scale(1)';
        });
        
        // Clear error on input
        input.addEventListener('input', function() {
            hideMessages();
        });
    });
    
    // Forgot password handler
    forgotPasswordLink.addEventListener('click', function(e) {
        e.preventDefault();
        
        const email = prompt('Please enter your email address:');
        
        if (email && validateEmail(email)) {
            showSuccess('Password reset link sent to ' + email);
            // Here you would typically send a request to your backend
            // to handle password reset
        } else if (email) {
            showError('Please enter a valid email address');
        }
    });
    
    // Social login handlers
    socialButtons.forEach(button => {
        button.addEventListener('click', function() {
            const platform = this.classList.contains('facebook') ? 'Facebook' :
                           this.classList.contains('twitter') ? 'Twitter' :
                           this.classList.contains('google') ? 'Google' : 'Social';
            
            showError(`${platform} login is not yet implemented`);
            
            // In a real application, you would redirect to the OAuth flow:
            // window.location.href = '/auth/' + platform.toLowerCase();
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
    
    function validateEmail(email) {
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return emailRegex.test(email);
    }
    
    // Add keyboard shortcuts
    document.addEventListener('keydown', function(e) {
        // ESC to clear form
        if (e.key === 'Escape') {
            loginForm.reset();
            hideMessages();
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


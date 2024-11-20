// Form validation
document.addEventListener('DOMContentLoaded', function() {
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        form.addEventListener('submit', function(event) {
            if (!validateForm(form)) {
                event.preventDefault();
            }
        });
    });
});

function validateForm(form) {
    let isValid = true;
    const inputs = form.querySelectorAll('input[required], textarea[required]');
    
    inputs.forEach(input => {
        if (!input.value.trim()) {
            showError(input, 'This field is required');
            isValid = false;
        } else {
            clearError(input);
            
            // Email validation
            if (input.type === 'email' && !validateEmail(input.value)) {
                showError(input, 'Please enter a valid email address');
                isValid = false;
            }
            
            // Password validation
            if (input.type === 'password' && input.value.length < 8) {
                showError(input, 'Password must be at least 8 characters long');
                isValid = false;
            }
        }
    });
    
    return isValid;
}

function validateEmail(email) {
    const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return re.test(email);
}

function showError(input, message) {
    const errorDiv = input.nextElementSibling?.classList.contains('error-message') 
        ? input.nextElementSibling 
        : createErrorElement();
    
    errorDiv.textContent = message;
    if (!input.nextElementSibling?.classList.contains('error-message')) {
        input.parentNode.insertBefore(errorDiv, input.nextSibling);
    }
    input.classList.add('error');
}

function clearError(input) {
    const errorDiv = input.nextElementSibling;
    if (errorDiv?.classList.contains('error-message')) {
        errorDiv.remove();
    }
    input.classList.remove('error');
}

function createErrorElement() {
    const div = document.createElement('div');
    div.className = 'error-message text-red-500 text-xs mt-1';
    return div;
}

// Modal handling
function openModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.classList.remove('hidden');
        document.body.style.overflow = 'hidden';
    }
}

function closeModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.classList.add('hidden');
        document.body.style.overflow = 'auto';
    }
}

// Close modal when clicking outside
document.addEventListener('click', function(event) {
    if (event.target.classList.contains('modal-backdrop')) {
        closeModal(event.target.firstElementChild.id);
    }
});

// File upload preview
function handleFileUpload(input) {
    if (input.files && input.files[0]) {
        const reader = new FileReader();
        const preview = document.getElementById(`${input.id}-preview`);
        
        reader.onload = function(e) {
            if (preview) {
                if (input.accept.includes('image')) {
                    preview.src = e.target.result;
                }
                preview.classList.remove('hidden');
            }
        };
        
        reader.readAsDataURL(input.files[0]);
    }
}

// Dynamic form fields
function addFormField(containerId, template) {
    const container = document.getElementById(containerId);
    const newField = template.content.cloneNode(true);
    container.appendChild(newField);
}

function removeFormField(button) {
    button.closest('.form-field').remove();
}

// Toast notifications
function showToast(message, type = 'info') {
    const toast = document.createElement('div');
    toast.className = `fixed bottom-4 right-4 px-4 py-2 rounded-lg text-white ${
        type === 'success' ? 'bg-green-500' :
        type === 'error' ? 'bg-red-500' :
        type === 'warning' ? 'bg-yellow-500' :
        'bg-blue-500'
    } fade-in`;
    toast.textContent = message;
    
    document.body.appendChild(toast);
    
    setTimeout(() => {
        toast.remove();
    }, 3000);
}

// Confirmation dialogs
function confirmAction(message, onConfirm) {
    const confirmed = window.confirm(message);
    if (confirmed && typeof onConfirm === 'function') {
        onConfirm();
    }
}

// Loading spinner
function showLoading(buttonElement) {
    const originalContent = buttonElement.innerHTML;
    buttonElement.disabled = true;
    buttonElement.innerHTML = '<div class="spinner mr-2"></div>Loading...';
    return originalContent;
}

function hideLoading(buttonElement, originalContent) {
    buttonElement.disabled = false;
    buttonElement.innerHTML = originalContent;
}

// Form submission with loading state
document.querySelectorAll('form').forEach(form => {
    form.addEventListener('submit', function(event) {
        const submitButton = form.querySelector('button[type="submit"]');
        if (submitButton) {
            const originalContent = showLoading(submitButton);
            // Restore button state after submission (for failed submissions)
            setTimeout(() => {
                if (submitButton.disabled) {
                    hideLoading(submitButton, originalContent);
                }
            }, 5000);
        }
    });
});

// Tooltips
document.querySelectorAll('[data-tooltip]').forEach(element => {
    const tooltip = document.createElement('span');
    tooltip.className = 'tooltip-text';
    tooltip.textContent = element.getAttribute('data-tooltip');
    element.appendChild(tooltip);
});

// Responsive navigation menu
const menuButton = document.querySelector('[data-menu-button]');
const mobileMenu = document.querySelector('[data-mobile-menu]');

if (menuButton && mobileMenu) {
    menuButton.addEventListener('click', () => {
        mobileMenu.classList.toggle('hidden');
    });
}

// Handle file size validation
function validateFileSize(input, maxSize) {
    const file = input.files[0];
    if (file && file.size > maxSize) {
        showError(input, `File size must be less than ${Math.round(maxSize/1024/1024)}MB`);
        input.value = '';
        return false;
    }
    clearError(input);
    return true;
}

// Debounce function for search inputs
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// Handle search inputs
const searchInputs = document.querySelectorAll('[data-search-input]');
searchInputs.forEach(input => {
    input.addEventListener('input', debounce((e) => {
        // Implement search functionality
        const searchTerm = e.target.value.toLowerCase();
        const searchContainer = document.querySelector(input.dataset.searchContainer);
        if (searchContainer) {
            const items = searchContainer.querySelectorAll('[data-search-item]');
            items.forEach(item => {
                const text = item.textContent.toLowerCase();
                item.style.display = text.includes(searchTerm) ? '' : 'none';
            });
        }
    }, 300));
});

// MDM Agent JavaScript Utilities

document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
    
    // Add fade-in animation to cards
    const cards = document.querySelectorAll('.card');
    cards.forEach((card, index) => {
        card.style.animationDelay = `${index * 0.1}s`;
        card.classList.add('fade-in');
    });
    
    // API status check
    checkApiStatus();
    
    // Periodically check API status
    setInterval(checkApiStatus, 30000); // Every 30 seconds
});

// Global utility functions
window.MDMAgent = {
    // Format date strings
    formatDate: function(dateString) {
        try {
            const date = new Date(dateString);
            return date.toLocaleDateString('en-US', {
                year: 'numeric',
                month: 'short',
                day: 'numeric',
                hour: '2-digit',
                minute: '2-digit'
            });
        } catch (e) {
            return dateString;
        }
    },
    
    // Format file sizes
    formatFileSize: function(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    },
    
    // Show notification
    showNotification: function(message, type = 'info', duration = 5000) {
        const alertHtml = `
            <div class="alert alert-${type} alert-dismissible fade show position-fixed" 
                 style="top: 1rem; right: 1rem; z-index: 9999; min-width: 300px;" role="alert">
                <i class="fas fa-${getIconForType(type)} me-2"></i>
                ${message}
                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
            </div>
        `;
        
        document.body.insertAdjacentHTML('beforeend', alertHtml);
        
        // Auto-dismiss after duration
        setTimeout(() => {
            const alerts = document.querySelectorAll('.alert.position-fixed');
            if (alerts.length > 0) {
                alerts[0].remove();
            }
        }, duration);
        
        function getIconForType(type) {
            const icons = {
                'success': 'check-circle',
                'danger': 'exclamation-triangle',
                'warning': 'exclamation-circle',
                'info': 'info-circle',
                'primary': 'info-circle'
            };
            return icons[type] || 'info-circle';
        }
    },
    
    // Copy text to clipboard
    copyToClipboard: function(text, showNotification = true) {
        navigator.clipboard.writeText(text).then(() => {
            if (showNotification) {
                this.showNotification('Copied to clipboard!', 'success', 2000);
            }
        }).catch(err => {
            console.error('Failed to copy text: ', err);
            if (showNotification) {
                this.showNotification('Failed to copy to clipboard', 'danger', 3000);
            }
        });
    },
    
    // Make API request with error handling
    apiRequest: function(url, options = {}) {
        const defaultOptions = {
            headers: {
                'Content-Type': 'application/json',
            }
        };
        
        const mergedOptions = { ...defaultOptions, ...options };
        
        return fetch(url, mergedOptions)
            .then(response => {
                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                }
                return response.json();
            })
            .catch(error => {
                console.error('API Request failed:', error);
                this.showNotification(`API Error: ${error.message}`, 'danger');
                throw error;
            });
    },
    
    // Load data with loading indicator
    loadWithSpinner: function(spinnerId, containerSelector, loadFunction) {
        const spinner = document.getElementById(spinnerId);
        const container = document.querySelector(containerSelector);
        
        if (spinner) spinner.classList.remove('d-none');
        if (container) container.style.opacity = '0.5';
        
        return loadFunction().finally(() => {
            if (spinner) spinner.classList.add('d-none');
            if (container) container.style.opacity = '1';
        });
    }
};

// API Status Checker
function checkApiStatus() {
    fetch('/health')
        .then(response => response.json())
        .then(data => {
            updateStatusIndicator(true);
        })
        .catch(error => {
            updateStatusIndicator(false);
        });
}

function updateStatusIndicator(isOnline) {
    const indicators = document.querySelectorAll('.status-indicator');
    indicators.forEach(indicator => {
        indicator.className = `status-indicator ${isOnline ? 'online' : 'offline'}`;
        indicator.title = isOnline ? 'API is online' : 'API is offline';
    });
}

// Search functionality
function initializeSearch(inputSelector, resultSelector, searchFunction) {
    const searchInput = document.querySelector(inputSelector);
    if (!searchInput) return;
    
    let searchTimeout;
    
    searchInput.addEventListener('input', function() {
        clearTimeout(searchTimeout);
        searchTimeout = setTimeout(() => {
            const query = this.value.trim();
            if (query.length >= 2) {
                searchFunction(query);
            } else {
                // Clear results or show all
                const resultsContainer = document.querySelector(resultSelector);
                if (resultsContainer) {
                    resultsContainer.innerHTML = '';
                }
            }
        }, 300);
    });
}

// Form validation utilities
function validateForm(formSelector) {
    const form = document.querySelector(formSelector);
    if (!form) return false;
    
    let isValid = true;
    const requiredFields = form.querySelectorAll('[required]');
    
    requiredFields.forEach(field => {
        if (!field.value.trim()) {
            field.classList.add('is-invalid');
            isValid = false;
        } else {
            field.classList.remove('is-invalid');
            field.classList.add('is-valid');
        }
    });
    
    return isValid;
}

// Dark mode toggle
function toggleDarkMode() {
    document.body.classList.toggle('dark-mode');
    
    // Save preference
    const isDark = document.body.classList.contains('dark-mode');
    localStorage.setItem('darkMode', isDark);
}

// Load dark mode preference
if (localStorage.getItem('darkMode') === 'true') {
    document.body.classList.add('dark-mode');
}

// Keyboard shortcuts
document.addEventListener('keydown', function(e) {
    // Ctrl/Cmd + K for search
    if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
        e.preventDefault();
        const searchInput = document.querySelector('input[type="search"], input[placeholder*="search" i]');
        if (searchInput) {
            searchInput.focus();
        }
    }
    
    // Escape to close modals
    if (e.key === 'Escape') {
        const openModals = document.querySelectorAll('.modal.show');
        openModals.forEach(modal => {
            bootstrap.Modal.getInstance(modal)?.hide();
        });
    }
});

// Progressive loading for images
function lazyLoadImages() {
    const images = document.querySelectorAll('img[data-src]');
    
    const imageObserver = new IntersectionObserver((entries, observer) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const img = entry.target;
                img.src = img.dataset.src;
                img.classList.remove('lazy');
                imageObserver.unobserve(img);
            }
        });
    });
    
    images.forEach(img => imageObserver.observe(img));
}

// Initialize lazy loading when DOM is ready
document.addEventListener('DOMContentLoaded', lazyLoadImages);

// Export for use in other scripts
window.MDMUtils = {
    checkApiStatus,
    updateStatusIndicator,
    initializeSearch,
    validateForm,
    toggleDarkMode,
    lazyLoadImages
};

/**
 * Main JavaScript for Digital Clone IITG
 */

document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
    
    // Setup task polling for any active tasks
    setupTaskPolling();
    
    // Setup form validation
    setupFormValidation();
    
    // Setup AJAX error handling
    setupGlobalErrorHandling();
});

/**
 * Poll for task status updates
 */
function setupTaskPolling() {
    const taskElements = document.querySelectorAll('[data-task-id]');
    
    taskElements.forEach(function(element) {
        const taskId = element.getAttribute('data-task-id');
        
        if (taskId) {
            // Make sure container has task-container class and id
            element.classList.add('task-container');
            if (!element.id) {
                element.id = 'task-container-' + taskId;
            }
            
            // Start polling for this task
            pollTaskStatus(taskId, element);
        }
    });
}

/**
 * Setup form validation for all forms
 */
function setupFormValidation() {
    const forms = document.querySelectorAll('.needs-validation');
    
    Array.from(forms).forEach(function (form) {
        form.addEventListener('submit', function (event) {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }
            
            form.classList.add('was-validated');
        }, false);
        
        // Add data-validate attribute to forms that need client-side validation
        if (form.hasAttribute('data-validate')) {
            form.addEventListener('submit', function (event) {
                event.preventDefault();
                
                const formId = this.id || 'form-' + Math.random().toString(36).substr(2, 9);
                if (!this.id) {
                    this.id = formId;
                }
                
                // Get validation rules
                const rulesAttr = this.getAttribute('data-validation-rules');
                let validationRules = {};
                
                try {
                    if (rulesAttr) {
                        validationRules = JSON.parse(rulesAttr);
                    }
                } catch (e) {
                    console.error('Invalid validation rules JSON:', e);
                }
                
                // Validate form
                if (validateForm(this, validationRules)) {
                    // If valid, submit via AJAX if data-ajax="true"
                    if (this.getAttribute('data-ajax') === 'true') {
                        submitFormAjax(this);
                    } else {
                        // Otherwise, submit normally
                        this.submit();
                    }
                }
            });
        }
    });
}

/**
 * Display confirmation dialog
 * 
 * @param {string} message - Message to display
 * @param {Function} callback - Function to call if confirmed
 */
function confirmAction(message, callback) {
    if (confirm(message)) {
        callback();
    }
}

/**
 * Preview uploaded image before submission
 * 
 * @param {HTMLElement} input - File input element
 * @param {string} previewId - ID of preview element
 */
function previewImage(input, previewId) {
    if (input.files && input.files[0]) {
        const reader = new FileReader();
        
        reader.onload = function(e) {
            document.getElementById(previewId).src = e.target.result;
            document.getElementById(previewId).classList.remove('d-none');
        };
        
        reader.readAsDataURL(input.files[0]);
    }
}

/**
 * Submit form via AJAX
 * @param {HTMLFormElement} form - Form to submit
 */
function submitFormAjax(form) {
    const url = form.action;
    const method = form.method || 'POST';
    const formData = new FormData(form);
    const submitButton = form.querySelector('button[type="submit"]');
    const resultContainer = document.getElementById(form.getAttribute('data-result-container') || 'form-result');
    
    // Disable submit button and show loading state
    if (submitButton) {
        submitButton.disabled = true;
        submitButton.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Processing...';
    }
    
    // Clear previous result
    if (resultContainer) {
        resultContainer.innerHTML = '';
    }
    
    // Submit form
    fetch(url, {
        method: method,
        body: formData,
        headers: {
            'X-Requested-With': 'XMLHttpRequest'
        }
    })
    .then(handleApiResponse)
    .then(data => {
        // Re-enable submit button
        if (submitButton) {
            submitButton.disabled = false;
            submitButton.innerHTML = submitButton.getAttribute('data-original-text') || 'Submit';
        }
        
        // Handle success
        if (data.success) {
            // Show success message
            if (resultContainer) {
                const successElement = document.createElement('div');
                successElement.className = 'alert alert-success mt-3';
                successElement.innerHTML = data.message || 'Success!';
                resultContainer.appendChild(successElement);
            }
            
            // Reset form if requested
            if (form.getAttribute('data-reset-on-success') === 'true') {
                form.reset();
            }
            
            // Redirect if specified
            if (data.redirect) {
                setTimeout(() => {
                    window.location.href = data.redirect;
                }, 1000);
            }
            
            // Reload page if requested
            if (form.getAttribute('data-reload-on-success') === 'true') {
                setTimeout(() => {
                    window.location.reload();
                }, 1000);
            }
            
            // Call custom success handler if provided
            const successCallback = form.getAttribute('data-success-callback');
            if (successCallback && typeof window[successCallback] === 'function') {
                window[successCallback](data);
            }
        } else {
            // Handle server-side validation errors
            if (data.errors) {
                Object.keys(data.errors).forEach(field => {
                    const inputField = form.elements[field];
                    if (inputField) {
                        markFieldInvalid(inputField, data.errors[field]);
                    }
                });
            }
            
            // Show general error message
            if (resultContainer && data.error) {
                displayErrorMessage(data.error, resultContainer.id, true);
            }
        }
    })
    .catch(error => {
        // Re-enable submit button
        if (submitButton) {
            submitButton.disabled = false;
            submitButton.innerHTML = submitButton.getAttribute('data-original-text') || 'Submit';
        }
        
        // Show error message
        if (resultContainer) {
            displayErrorMessage(`Error: ${error.message}`, resultContainer.id, true);
        }
        
        console.error('Form submission error:', error);
    });
}

/**
 * Set up global error handling for AJAX requests
 */
function setupGlobalErrorHandling() {
    // Store original fetch function
    const originalFetch = window.fetch;
    
    // Override fetch to add error handling
    window.fetch = function() {
        return originalFetch.apply(this, arguments)
            .then(response => {
                // Check for 401 Unauthorized and redirect to login if needed
                if (response.status === 401 && !response.url.includes('/auth/')) {
                    const loginUrl = '/auth/login?next=' + encodeURIComponent(window.location.pathname);
                    window.location.href = loginUrl;
                    return Promise.reject(new Error('Authentication required. Redirecting to login...'));
                }
                
                // Check for 403 Forbidden
                if (response.status === 403) {
                    showGlobalErrorMessage('You do not have permission to access this resource');
                }
                
                // Check for 500 Server Error
                if (response.status === 500) {
                    showGlobalErrorMessage('The server encountered an error. Please try again later.');
                }
                
                return response;
            })
            .catch(error => {
                // Handle network errors
                if (error.name === 'TypeError' && error.message.includes('NetworkError')) {
                    showGlobalErrorMessage('Network error. Please check your internet connection.');
                }
                
                throw error;
            });
    };
    
    // Add global error event handler
    window.addEventListener('error', function(event) {
        console.error('Global error:', event.error);
    });
}

/**
 * Show a global error message at the top of the page
 * @param {string} message - Error message to display
 */
function showGlobalErrorMessage(message) {
    const container = document.createElement('div');
    container.className = 'global-error-container';
    container.style.position = 'fixed';
    container.style.top = '1rem';
    container.style.left = '50%';
    container.style.transform = 'translateX(-50%)';
    container.style.zIndex = '9999';
    container.style.minWidth = '30%';
    
    const alert = document.createElement('div');
    alert.className = 'alert alert-danger alert-dismissible fade show';
    alert.innerHTML = `
        <strong>Error:</strong> ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    `;
    
    container.appendChild(alert);
    document.body.appendChild(container);
    
    setTimeout(() => {
        alert.classList.remove('show');
        setTimeout(() => container.remove(), 300);
    }, 8000);
}

/**
 * Use audio for video generation
 * @param {string} audioId - ID of the audio to use
 */
function useAudioForVideo(audioId) {
    const modal = new bootstrap.Modal(document.getElementById('generateVideoModal'));
    
    // Set audio ID in the form
    document.getElementById('audioIdInput').value = audioId;
    
    // Show the modal
    modal.show();
}

/**
 * Use video for presentation
 * @param {string} videoId - ID of the video to use
 */
function useVideoForPresentation(videoId) {
    const videoCheckbox = document.querySelector(`input[name="videos[]"][value="${videoId}"]`);
    if (videoCheckbox) {
        videoCheckbox.checked = true;
    }
    
    const modal = new bootstrap.Modal(document.getElementById('createPresentationModal'));
    modal.show();
}

/**
 * Create SCORM package from PowerPoint
 * @param {string} powerPointId - ID of the PowerPoint to use
 */
function createScormPackage(powerPointId) {
    const modal = new bootstrap.Modal(document.getElementById('createScormModal'));
    
    // Set PowerPoint ID in the form
    document.getElementById('presentationIdInput').value = powerPointId;
    
    // Show the modal
    modal.show();
}

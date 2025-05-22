/**
 * Error handling utilities
 */

/**
 * Handles API errors from fetch responses
 * @param {Response} response - Fetch API response
 * @returns {Promise} - Resolves with data or rejects with error
 */
function handleApiResponse(response) {
    return response.json().then(data => {
        if (!response.ok) {
            // Create error object with response details
            const error = new Error(data.error || 'Unknown error occurred');
            error.status = response.status;
            error.statusText = response.statusText;
            error.data = data;
            throw error;
        }
        return data;
    });
}

/**
 * Display error message in the UI
 * @param {string} message - Error message to display
 * @param {string} containerId - DOM container ID to show error in
 * @param {boolean} isApiError - Whether this is an API error
 */
function displayErrorMessage(message, containerId, isApiError = false) {
    const container = document.getElementById(containerId);
    if (!container) return;
    
    const errorElement = document.createElement('div');
    errorElement.className = 'alert alert-danger alert-dismissible fade show mt-3';
    errorElement.role = 'alert';
    
    let errorContent = message;
    if (isApiError) {
        errorContent = `<strong>Error:</strong> ${message}`;
    }
    
    errorElement.innerHTML = `
        ${errorContent}
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    `;
    
    container.appendChild(errorElement);
    
    // Auto-remove after 8 seconds
    setTimeout(() => {
        errorElement.classList.remove('show');
        setTimeout(() => errorElement.remove(), 300);
    }, 8000);
}

/**
 * Validate form data and show validation errors
 * @param {HTMLFormElement} form - Form to validate
 * @param {Object} validationRules - Rules for each field
 * @returns {boolean} - Is form valid
 */
function validateForm(form, validationRules) {
    let isValid = true;
    
    // Clear previous error messages
    const errorElements = form.querySelectorAll('.invalid-feedback');
    errorElements.forEach(element => element.remove());
    
    // Reset validation classes
    form.querySelectorAll('.is-invalid').forEach(element => {
        element.classList.remove('is-invalid');
    });
    
    // Validate each field
    Object.keys(validationRules).forEach(fieldName => {
        const field = form.elements[fieldName];
        if (!field) return;
        
        const rules = validationRules[fieldName];
        const value = field.value;
        
        // Required field
        if (rules.required && !value.trim()) {
            markFieldInvalid(field, 'This field is required');
            isValid = false;
            return;
        }
        
        // Minimum length
        if (rules.minLength && value.length < rules.minLength) {
            markFieldInvalid(field, `Must be at least ${rules.minLength} characters`);
            isValid = false;
            return;
        }
        
        // Maximum length
        if (rules.maxLength && value.length > rules.maxLength) {
            markFieldInvalid(field, `Must be no more than ${rules.maxLength} characters`);
            isValid = false;
            return;
        }
        
        // Pattern match
        if (rules.pattern && !new RegExp(rules.pattern).test(value)) {
            markFieldInvalid(field, rules.patternMessage || 'Invalid format');
            isValid = false;
            return;
        }
        
        // Custom validator
        if (rules.validator && typeof rules.validator === 'function') {
            const validatorResult = rules.validator(value, form);
            if (validatorResult !== true) {
                markFieldInvalid(field, validatorResult || 'Invalid value');
                isValid = false;
                return;
            }
        }
    });
    
    return isValid;
}

/**
 * Mark a form field as invalid
 * @param {HTMLElement} field - Field to mark
 * @param {string} message - Error message
 */
function markFieldInvalid(field, message) {
    field.classList.add('is-invalid');
    
    const errorElement = document.createElement('div');
    errorElement.className = 'invalid-feedback';
    errorElement.textContent = message;
    
    field.parentNode.appendChild(errorElement);
}

/**
 * Handle task failure with appropriate UI updates
 * @param {Object} taskData - Task data from API
 * @param {HTMLElement} container - Container to update
 */
function handleTaskFailure(taskData, container) {
    // Remove any spinner
    const spinner = container.querySelector('.spinner-border');
    if (spinner) {
        spinner.remove();
    }
    
    // Update status display
    const statusElement = container.querySelector('.status-text');
    if (statusElement) {
        statusElement.textContent = 'Failed';
        statusElement.className = 'status-text text-danger';
    }
    
    // Show error message
    const errorMessage = taskData.error || 'An unknown error occurred';
    const errorAlert = document.createElement('div');
    errorAlert.className = 'alert alert-danger mt-3';
    errorAlert.innerHTML = `
        <h5>Task Failed</h5>
        <p>${errorMessage}</p>
        <button type="button" class="btn btn-sm btn-outline-danger" onclick="retryTask('${taskData.task_id}', this)">
            <i class="bi bi-arrow-clockwise"></i> Retry
        </button>
    `;
    container.appendChild(errorAlert);
}

/**
 * Retry a failed task
 * @param {string} taskId - ID of task to retry
 * @param {HTMLElement} button - Button that was clicked
 */
function retryTask(taskId, button) {
    const container = button.closest('.task-container');
    if (!container) return;
    
    // Display spinner
    button.disabled = true;
    button.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Retrying...';
    
    // Call API to retry task
    fetch(`/api/task/${taskId}/retry`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        }
    })
    .then(handleApiResponse)
    .then(data => {
        if (data.success) {
            // Reset container for new task
            const newTaskId = data.task_id;
            container.innerHTML = `
                <div class="d-flex align-items-center">
                    <span class="spinner-border spinner-border-sm me-2"></span>
                    <span class="status-text">Processing</span>
                </div>
                <div class="progress mt-2">
                    <div class="progress-bar progress-bar-striped progress-bar-animated" style="width: 0%"></div>
                </div>
                <div class="task-message small text-muted mt-1"></div>
            `;
            container.setAttribute('data-task-id', newTaskId);
            
            // Start polling for new task status
            pollTaskStatus(newTaskId, container);
        } else {
            displayErrorMessage(data.error || 'Failed to retry task', container.id);
            button.disabled = false;
            button.innerHTML = '<i class="bi bi-arrow-clockwise"></i> Retry';
        }
    })
    .catch(error => {
        displayErrorMessage(`Error: ${error.message}`, container.id);
        button.disabled = false;
        button.innerHTML = '<i class="bi bi-arrow-clockwise"></i> Retry';
    });
}

/**
 * Poll for task status and update UI
 * @param {string} taskId - Task ID to poll for
 * @param {HTMLElement} container - Container to update
 */
function pollTaskStatus(taskId, container) {
    const statusElement = container.querySelector('.status-text');
    const progressBar = container.querySelector('.progress-bar');
    const messageElement = container.querySelector('.task-message');
    
    const poll = () => {
        fetch(`/api/task/${taskId}`)
            .then(handleApiResponse)
            .then(data => {
                // Update status text
                if (statusElement) {
                    statusElement.textContent = data.status;
                }
                
                // Update progress bar if info available
                if (progressBar && data.info && data.info.progress !== undefined) {
                    const progress = Math.round(data.info.progress * 100);
                    progressBar.style.width = `${progress}%`;
                    progressBar.setAttribute('aria-valuenow', progress);
                }
                
                // Update message if available
                if (messageElement && data.info && data.info.message) {
                    messageElement.textContent = data.info.message;
                }
                
                // Handle task completion
                if (data.status === 'SUCCESS') {
                    onTaskSuccess(data, container);
                    return;
                }
                
                // Handle task failure
                if (data.status === 'FAILURE') {
                    handleTaskFailure(data, container);
                    return;
                }
                
                // Continue polling if task is still running
                setTimeout(poll, 2000);
            })
            .catch(error => {
                console.error('Error polling task status:', error);
                if (statusElement) {
                    statusElement.textContent = 'Error';
                    statusElement.className = 'status-text text-danger';
                }
                
                displayErrorMessage(`Error checking task status: ${error.message}`, container.id);
                
                // Retry polling after a longer delay
                setTimeout(poll, 5000);
            });
    };
    
    // Start polling
    poll();
}

/**
 * Handle successful task completion
 * @param {Object} data - Task result data 
 * @param {HTMLElement} container - Container to update
 */
function onTaskSuccess(data, container) {
    // Remove spinner
    const spinner = container.querySelector('.spinner-border');
    if (spinner) {
        spinner.remove();
    }
    
    // Update status display
    const statusElement = container.querySelector('.status-text');
    if (statusElement) {
        statusElement.textContent = 'Completed';
        statusElement.className = 'status-text text-success';
    }
    
    // Update progress bar
    const progressBar = container.querySelector('.progress-bar');
    if (progressBar) {
        progressBar.style.width = '100%';
        progressBar.classList.remove('progress-bar-animated', 'progress-bar-striped');
        progressBar.classList.add('bg-success');
    }
    
    // Handle result based on type
    if (data.result && data.result.url) {
        if (data.result.url.endsWith('.mp3') || data.result.url.endsWith('.wav')) {
            // Audio result
            const audioPlayer = document.createElement('div');
            audioPlayer.className = 'mt-3';
            audioPlayer.innerHTML = `
                <h6>Generated Audio:</h6>
                <audio controls class="w-100">
                    <source src="${data.result.url}" type="audio/mpeg">
                    Your browser does not support the audio element.
                </audio>
                <div class="btn-group mt-2">
                    <a href="${data.result.url}" class="btn btn-sm btn-outline-primary" target="_blank" download>
                        <i class="bi bi-download"></i> Download
                    </a>
                    <button class="btn btn-sm btn-outline-success" onclick="useAudioForVideo('${data.result.audio_id}')">
                        <i class="bi bi-camera-video"></i> Generate Video
                    </button>
                </div>
            `;
            container.appendChild(audioPlayer);
        } else if (data.result.url.endsWith('.mp4')) {
            // Video result
            const videoPlayer = document.createElement('div');
            videoPlayer.className = 'mt-3';
            videoPlayer.innerHTML = `
                <h6>Generated Video:</h6>
                <div class="ratio ratio-16x9">
                    <video controls>
                        <source src="${data.result.url}" type="video/mp4">
                        Your browser does not support the video tag.
                    </video>
                </div>
                <div class="btn-group mt-2">
                    <a href="${data.result.url}" class="btn btn-sm btn-outline-primary" target="_blank" download>
                        <i class="bi bi-download"></i> Download
                    </a>
                    <button class="btn btn-sm btn-outline-success" onclick="useVideoForPresentation('${data.result.video_id}')">
                        <i class="bi bi-file-earmark-slides"></i> Add to Presentation
                    </button>
                </div>
            `;
            container.appendChild(videoPlayer);
        } else if (data.result.url.endsWith('.pptx')) {
            // Presentation result
            const presentationLink = document.createElement('div');
            presentationLink.className = 'mt-3';
            presentationLink.innerHTML = `
                <h6>Generated Presentation:</h6>
                <div class="alert alert-success">
                    <p>Your presentation has been successfully created!</p>
                    <div class="btn-group">
                        <a href="${data.result.url}" class="btn btn-sm btn-outline-primary" target="_blank" download>
                            <i class="bi bi-download"></i> Download
                        </a>
                        <button class="btn btn-sm btn-outline-success" onclick="createScormPackage('${data.result.powerpoint_id}')">
                            <i class="bi bi-box"></i> Create SCORM Package
                        </button>
                    </div>
                </div>
            `;
            container.appendChild(presentationLink);
        }
    }
    
    // Check if we need to reload the page
    if (container.getAttribute('data-reload-on-complete') === 'true') {
        const successAlert = document.createElement('div');
        successAlert.className = 'alert alert-info mt-3';
        successAlert.innerHTML = 'Reloading page to show updated content...';
        container.appendChild(successAlert);
        
        setTimeout(() => {
            window.location.reload();
        }, 2000);
    }
}

/**
 * Task Status Monitor
 * This script checks the status of long-running tasks
 */

let activePollingTasks = {};

/**
 * Start polling for task status
 * @param {string} taskId - Celery task ID
 * @param {Object} options - Configuration options
 * @param {string} options.statusUrl - URL to check status (default: /api/tasks/{taskId})
 * @param {number} options.interval - Polling interval in ms (default: 2000)
 * @param {Function} options.onSuccess - Success callback function
 * @param {Function} options.onFailure - Error callback function
 * @param {Function} options.onProgress - Progress update callback
 * @param {string} options.resultContainerId - DOM ID to show results (default: task-result)
 * @returns {string} - Task polling ID
 */
function startTaskPolling(taskId, options = {}) {
    const pollingId = `task_${Date.now()}`;
    
    // Default options
    const settings = {
        statusUrl: `/api/tasks/${taskId}`,
        interval: 2000,
        resultContainerId: 'task-result',
        ...options
    };
    
    // Show initial message
    const resultContainer = document.getElementById(settings.resultContainerId);
    if (resultContainer) {
        resultContainer.innerHTML = `
            <div class="alert alert-info">
                <div class="d-flex align-items-center">
                    <div class="spinner-border spinner-border-sm me-2" role="status">
                        <span class="visually-hidden">Processing...</span>
                    </div>
                    <div>Task is processing. This may take a few minutes.</div>
                </div>
            </div>
        `;
    }
    
    // Start polling
    const pollFunction = () => {
        fetch(settings.statusUrl)
            .then(response => handleApiResponse(response))
            .then(data => {
                if (!activePollingTasks[pollingId]) {
                    // Polling was cancelled
                    return;
                }
                
                // Check task status
                if (data.status === 'SUCCESS') {
                    // Task completed successfully
                    stopTaskPolling(pollingId);
                    
                    if (settings.onSuccess) {
                        settings.onSuccess(data.result);
                    }
                    
                    // Update result container
                    if (resultContainer) {
                        resultContainer.innerHTML = `
                            <div class="alert alert-success">
                                <i class="bi bi-check-circle-fill me-2"></i>
                                Task completed successfully!
                            </div>
                        `;
                    }
                } else if (data.status === 'FAILURE') {
                    // Task failed
                    stopTaskPolling(pollingId);
                    
                    if (settings.onFailure) {
                        settings.onFailure(data.result);
                    }
                    
                    // Show error message
                    if (resultContainer) {
                        resultContainer.innerHTML = `
                            <div class="alert alert-danger">
                                <i class="bi bi-exclamation-triangle-fill me-2"></i>
                                <strong>Error:</strong> ${data.result.error || 'Task failed'}
                            </div>
                        `;
                    }
                } else if (data.status === 'PENDING' || data.status === 'STARTED') {
                    // Task still in progress
                    if (settings.onProgress) {
                        settings.onProgress(data);
                    }
                    
                    // Update progress information if available
                    if (resultContainer && data.meta && data.meta.progress) {
                        const progress = data.meta.progress;
                        const percent = Math.min(Math.max(parseInt(progress), 0), 100);
                        
                        resultContainer.innerHTML = `
                            <div class="alert alert-info">
                                <div class="d-flex align-items-center mb-2">
                                    <div class="spinner-border spinner-border-sm me-2" role="status">
                                        <span class="visually-hidden">Processing...</span>
                                    </div>
                                    <div>${data.meta.message || 'Task is processing...'}</div>
                                </div>
                                <div class="progress" role="progressbar" aria-valuenow="${percent}" aria-valuemin="0" aria-valuemax="100">
                                    <div class="progress-bar progress-bar-striped progress-bar-animated" style="width: ${percent}%">${percent}%</div>
                                </div>
                            </div>
                        `;
                    }
                    
                    // Continue polling
                    activePollingTasks[pollingId].timeoutId = setTimeout(pollFunction, settings.interval);
                }
            })
            .catch(error => {
                console.error('Task polling error:', error);
                
                // Show error message
                if (resultContainer) {
                    resultContainer.innerHTML = `
                        <div class="alert alert-danger">
                            <i class="bi bi-exclamation-triangle-fill me-2"></i>
                            <strong>Error checking task status:</strong> ${error.message || 'Unknown error'}
                        </div>
                    `;
                }
                
                // Continue polling despite error (might be temporary)
                // But use a longer interval to avoid overwhelming the server
                if (activePollingTasks[pollingId]) {
                    activePollingTasks[pollingId].timeoutId = setTimeout(pollFunction, settings.interval * 2);
                }
            });
    };
    
    // Store polling task reference
    activePollingTasks[pollingId] = {
        taskId: taskId,
        timeoutId: setTimeout(pollFunction, 0) // Start immediately
    };
    
    return pollingId;
}

/**
 * Stop polling for task status
 * @param {string} pollingId - Task polling ID from startTaskPolling
 */
function stopTaskPolling(pollingId) {
    if (activePollingTasks[pollingId]) {
        clearTimeout(activePollingTasks[pollingId].timeoutId);
        delete activePollingTasks[pollingId];
    }
}

/**
 * Stop all running task polls
 */
function stopAllTaskPolling() {
    for (const id in activePollingTasks) {
        stopTaskPolling(id);
    }
}

// Clean up polls when page is unloaded
window.addEventListener('beforeunload', stopAllTaskPolling);

/**
 * MVA2 Application JavaScript
 * Main JavaScript functionality for the MVA2 biomedical research platform
 */

// Global application object
window.MVA2 = window.MVA2 || {};

// Application configuration
MVA2.config = {
    apiBaseUrl: '/api/v1',
    chartColors: {
        primary: '#0d6efd',
        secondary: '#6c757d',
        success: '#198754',
        info: '#0dcaf0',
        warning: '#ffc107',
        danger: '#dc3545'
    },
    uploadSettings: {
        maxFileSize: 50 * 1024 * 1024, // 50MB
        allowedTypes: ['csv', 'xlsx', 'json', 'txt']
    }
};

// Utility functions
MVA2.utils = {
    /**
     * Show loading spinner
     */
    showLoading: function(container) {
        const spinner = `
            <div class="loading-spinner">
                <div class="spinner-border text-primary" role="status">
                    <span class="visually-hidden">Loading...</span>
                </div>
            </div>
        `;
        if (container) {
            container.innerHTML = spinner;
        }
    },

    /**
     * Hide loading spinner
     */
    hideLoading: function(container) {
        const spinner = container ? container.querySelector('.loading-spinner') : null;
        if (spinner) {
            spinner.remove();
        }
    },

    /**
     * Show toast notification
     */
    showToast: function(message, type = 'info') {
        const toastContainer = document.getElementById('toastContainer') || this.createToastContainer();
        const toastId = 'toast_' + Date.now();
        
        const toast = document.createElement('div');
        toast.id = toastId;
        toast.className = `toast align-items-center text-white bg-${type} border-0`;
        toast.setAttribute('role', 'alert');
        toast.innerHTML = `
            <div class="d-flex">
                <div class="toast-body">${message}</div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
            </div>
        `;
        
        toastContainer.appendChild(toast);
        
        const bsToast = new bootstrap.Toast(toast);
        bsToast.show();
        
        // Auto remove after hiding
        toast.addEventListener('hidden.bs.toast', () => {
            toast.remove();
        });
    },

    /**
     * Create toast container if it doesn't exist
     */
    createToastContainer: function() {
        const container = document.createElement('div');
        container.id = 'toastContainer';
        container.className = 'toast-container position-fixed top-0 end-0 p-3';
        container.style.zIndex = '9999';
        document.body.appendChild(container);
        return container;
    },

    /**
     * Format date for display
     */
    formatDate: function(dateString) {
        if (!dateString) return 'N/A';
        const date = new Date(dateString);
        return date.toLocaleDateString() + ' ' + date.toLocaleTimeString();
    },

    /**
     * Format number with appropriate precision
     */
    formatNumber: function(number, precision = 2) {
        if (number === null || number === undefined) return 'N/A';
        return parseFloat(number).toFixed(precision);
    },

    /**
     * Validate email format
     */
    validateEmail: function(email) {
        const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return re.test(email);
    },

    /**
     * Debounce function calls
     */
    debounce: function(func, wait) {
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
};

// API utilities
MVA2.api = {
    /**
     * Make API request with error handling
     */
    request: async function(endpoint, options = {}) {
        try {
            const url = MVA2.config.apiBaseUrl + endpoint;
            const defaultOptions = {
                headers: {
                    'Content-Type': 'application/json',
                }
            };
            
            const response = await fetch(url, { ...defaultOptions, ...options });
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            return await response.json();
        } catch (error) {
            console.error('API request failed:', error);
            MVA2.utils.showToast('API request failed: ' + error.message, 'danger');
            throw error;
        }
    },

    /**
     * GET request
     */
    get: function(endpoint) {
        return this.request(endpoint, { method: 'GET' });
    },

    /**
     * POST request
     */
    post: function(endpoint, data) {
        return this.request(endpoint, {
            method: 'POST',
            body: JSON.stringify(data)
        });
    },

    /**
     * PUT request
     */
    put: function(endpoint, data) {
        return this.request(endpoint, {
            method: 'PUT',
            body: JSON.stringify(data)
        });
    },

    /**
     * DELETE request
     */
    delete: function(endpoint) {
        return this.request(endpoint, { method: 'DELETE' });
    }
};

// Chart utilities
MVA2.charts = {
    /**
     * Create default chart options
     */
    getDefaultOptions: function() {
        return {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom'
                }
            }
        };
    },

    /**
     * Create survival curve chart
     */
    createSurvivalChart: function(canvas, data) {
        return new Chart(canvas, {
            type: 'line',
            data: {
                datasets: data.map((series, index) => ({
                    label: series.name,
                    data: series.data,
                    borderColor: Object.values(MVA2.config.chartColors)[index],
                    backgroundColor: Object.values(MVA2.config.chartColors)[index] + '20',
                    fill: false,
                    stepped: true
                }))
            },
            options: {
                ...this.getDefaultOptions(),
                scales: {
                    x: {
                        title: {
                            display: true,
                            text: 'Time (months)'
                        }
                    },
                    y: {
                        title: {
                            display: true,
                            text: 'Survival Probability'
                        },
                        min: 0,
                        max: 1
                    }
                }
            }
        });
    },

    /**
     * Create microbiome abundance heatmap
     */
    createHeatmap: function(canvas, data) {
        // This would use a specialized heatmap library like Chart.js Matrix
        // For now, create a simple bar chart representation
        return new Chart(canvas, {
            type: 'bar',
            data: {
                labels: data.labels,
                datasets: [{
                    label: 'Abundance',
                    data: data.values,
                    backgroundColor: MVA2.config.chartColors.primary
                }]
            },
            options: this.getDefaultOptions()
        });
    }
};

// File upload utilities
MVA2.upload = {
    /**
     * Initialize drag and drop upload
     */
    initDragDrop: function(dropZone, fileInput, callback) {
        dropZone.addEventListener('dragover', (e) => {
            e.preventDefault();
            dropZone.classList.add('dragover');
        });

        dropZone.addEventListener('dragleave', () => {
            dropZone.classList.remove('dragover');
        });

        dropZone.addEventListener('drop', (e) => {
            e.preventDefault();
            dropZone.classList.remove('dragover');
            
            const files = Array.from(e.dataTransfer.files);
            this.handleFiles(files, callback);
        });

        dropZone.addEventListener('click', () => {
            fileInput.click();
        });

        fileInput.addEventListener('change', (e) => {
            const files = Array.from(e.target.files);
            this.handleFiles(files, callback);
        });
    },

    /**
     * Handle file selection
     */
    handleFiles: function(files, callback) {
        const validFiles = files.filter(file => this.validateFile(file));
        
        if (validFiles.length !== files.length) {
            MVA2.utils.showToast('Some files were invalid and skipped', 'warning');
        }
        
        if (validFiles.length > 0) {
            callback(validFiles);
        }
    },

    /**
     * Validate file
     */
    validateFile: function(file) {
        const maxSize = MVA2.config.uploadSettings.maxFileSize;
        const allowedTypes = MVA2.config.uploadSettings.allowedTypes;
        
        if (file.size > maxSize) {
            MVA2.utils.showToast(`File ${file.name} is too large (max ${maxSize / 1024 / 1024}MB)`, 'danger');
            return false;
        }
        
        const extension = file.name.split('.').pop().toLowerCase();
        if (!allowedTypes.includes(extension)) {
            MVA2.utils.showToast(`File type .${extension} is not allowed`, 'danger');
            return false;
        }
        
        return true;
    },

    /**
     * Upload files with progress
     */
    uploadFiles: function(files, endpoint, progressCallback) {
        const promises = files.map(file => this.uploadFile(file, endpoint, progressCallback));
        return Promise.all(promises);
    },

    /**
     * Upload single file
     */
    uploadFile: function(file, endpoint, progressCallback) {
        return new Promise((resolve, reject) => {
            const formData = new FormData();
            formData.append('file', file);
            
            const xhr = new XMLHttpRequest();
            
            xhr.upload.addEventListener('progress', (e) => {
                if (e.lengthComputable && progressCallback) {
                    const progress = (e.loaded / e.total) * 100;
                    progressCallback(file.name, progress);
                }
            });
            
            xhr.addEventListener('load', () => {
                if (xhr.status === 200) {
                    resolve(JSON.parse(xhr.responseText));
                } else {
                    reject(new Error(`Upload failed: ${xhr.statusText}`));
                }
            });
            
            xhr.addEventListener('error', () => {
                reject(new Error('Upload failed'));
            });
            
            xhr.open('POST', MVA2.config.apiBaseUrl + endpoint);
            xhr.send(formData);
        });
    }
};

// Data table utilities
MVA2.table = {
    /**
     * Initialize DataTable with common options
     */
    init: function(tableElement, options = {}) {
        const defaultOptions = {
            responsive: true,
            pageLength: 25,
            lengthMenu: [[10, 25, 50, 100], [10, 25, 50, 100]],
            dom: '<"row"<"col-sm-12 col-md-6"l><"col-sm-12 col-md-6"f>>' +
                 '<"row"<"col-sm-12"tr>>' +
                 '<"row"<"col-sm-12 col-md-5"i><"col-sm-12 col-md-7"p>>',
            language: {
                search: "Search:",
                lengthMenu: "Show _MENU_ entries",
                info: "Showing _START_ to _END_ of _TOTAL_ entries",
                paginate: {
                    first: "First",
                    last: "Last",
                    next: "Next",
                    previous: "Previous"
                }
            }
        };
        
        return $(tableElement).DataTable({ ...defaultOptions, ...options });
    }
};

// Initialize application when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
    
    // Initialize popovers
    const popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });
    
    // Global error handler
    window.addEventListener('error', function(e) {
        console.error('Global error:', e.error);
        MVA2.utils.showToast('An unexpected error occurred', 'danger');
    });
    
    console.log('MVA2 application initialized');
});

// Export for module usage
if (typeof module !== 'undefined' && module.exports) {
    module.exports = MVA2;
}

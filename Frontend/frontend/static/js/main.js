// Main JavaScript for Health Monitoring System

document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Initialize popovers
    var popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    var popoverList = popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });

    // Auto-hide alerts after 5 seconds
    setTimeout(function() {
        var alerts = document.querySelectorAll('.alert:not(.alert-permanent)');
        alerts.forEach(function(alert) {
            var bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        });
    }, 5000);

    // File upload drag and drop
    const fileInput = document.getElementById('file');
    if (fileInput) {
        const uploadArea = fileInput.closest('.card-body');
        if (uploadArea) {
            uploadArea.classList.add('file-upload-area');
            
            uploadArea.addEventListener('dragover', function(e) {
                e.preventDefault();
                uploadArea.classList.add('dragover');
            });
            
            uploadArea.addEventListener('dragleave', function(e) {
                e.preventDefault();
                uploadArea.classList.remove('dragover');
            });
            
            uploadArea.addEventListener('drop', function(e) {
                e.preventDefault();
                uploadArea.classList.remove('dragover');
                
                const files = e.dataTransfer.files;
                if (files.length > 0) {
                    fileInput.files = files;
                    updateFileDisplay();
                }
            });
        }
        
        fileInput.addEventListener('change', updateFileDisplay);
    }
    
    function updateFileDisplay() {
        const file = fileInput.files[0];
        if (file) {
            const fileName = file.name;
            const fileSize = (file.size / 1024 / 1024).toFixed(2);
            const fileType = file.type || 'Unknown';
            
            let displayText = `Selected: ${fileName} (${fileSize} MB, ${fileType})`;
            
            // Create or update file info display
            let fileInfo = document.getElementById('file-info');
            if (!fileInfo) {
                fileInfo = document.createElement('div');
                fileInfo.id = 'file-info';
                fileInfo.className = 'mt-2 text-muted small';
                fileInput.parentNode.appendChild(fileInfo);
            }
            fileInfo.textContent = displayText;
        }
    }

    // Form validation
    const forms = document.querySelectorAll('.needs-validation');
    Array.from(forms).forEach(form => {
        form.addEventListener('submit', event => {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }
            form.classList.add('was-validated');
        });
    });

    // Auto-refresh demo output
    const demoOutput = document.getElementById('demoOutput');
    if (demoOutput && demoOutput.textContent.includes('Running demo...')) {
        const interval = setInterval(() => {
            if (demoOutput.textContent.includes('Demo completed') || 
                demoOutput.textContent.includes('Demo failed') ||
                demoOutput.textContent.includes('Error running demo')) {
                clearInterval(interval);
            } else {
                demoOutput.textContent += '.';
            }
        }, 1000);
    }

    // Smooth scrolling for anchor links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            const href = this.getAttribute('href');
            // Only process if href is not just '#' and has a valid target
            if (href && href !== '#' && href.length > 1) {
                const target = document.querySelector(href);
                if (target) {
                    target.scrollIntoView({
                        behavior: 'smooth',
                        block: 'start'
                    });
                }
            }
        });
    });

    // Add loading states to buttons
    document.querySelectorAll('button[type="submit"]').forEach(button => {
        button.addEventListener('click', function() {
            if (this.form && this.form.checkValidity()) {
                console.log('Upload form submitted');
                this.disabled = true;
                const originalText = this.innerHTML;
                this.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Processing...';
                
                // Re-enable after 10 seconds as fallback
                setTimeout(() => {
                    this.disabled = false;
                    this.innerHTML = originalText;
                }, 10000);
            }
        });
    });

    // Add console logging for form submission
    const uploadForm = document.querySelector('form[action="/upload"]');
    if (uploadForm) {
        uploadForm.addEventListener('submit', function(e) {
            console.log('Upload form submit event triggered');
            const formData = new FormData(this);
            console.log('Form data:', {
                patient_id: formData.get('patient_id'),
                device_id: formData.get('device_id'),
                file: formData.get('file')?.name || 'No file'
            });
        });
    }
});

// Utility functions
function showAlert(message, type = 'info') {
    const alertContainer = document.querySelector('.container.mt-3') || document.querySelector('main .container');
    if (alertContainer) {
        const alertDiv = document.createElement('div');
        alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
        alertDiv.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        alertContainer.insertBefore(alertDiv, alertContainer.firstChild);
        
        // Auto-hide after 5 seconds
        setTimeout(() => {
            const bsAlert = new bootstrap.Alert(alertDiv);
            bsAlert.close();
        }, 5000);
    }
}

function formatNumber(num, decimals = 2) {
    return parseFloat(num).toFixed(decimals);
}

function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString() + ' ' + date.toLocaleTimeString();
}

// API helper functions
async function makeApiRequest(endpoint, method = 'GET', data = null) {
    try {
        const options = {
            method: method,
            headers: {
                'Content-Type': 'application/json',
                'Authorization': 'Bearer dev-token-123'
            }
        };
        
        if (data) {
            options.body = JSON.stringify(data);
        }
        
        const response = await fetch(`/api/v1${endpoint}`, options);
        const result = await response.json();
        
        return {
            success: response.ok,
            data: result,
            status: response.status
        };
    } catch (error) {
        return {
            success: false,
            error: error.message
        };
    }
}

// Demo functionality
function runDemo() {
    const btn = document.getElementById('runDemoBtn');
    const output = document.getElementById('demoOutput');
    
    if (!btn || !output) return;
    
    btn.disabled = true;
    btn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Running Demo...';
    output.innerHTML = '<div class="text-info">Starting demo...</div>';
    
    fetch('/api/demo/run', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            output.innerHTML = '<div class="text-success">Demo completed successfully!</div><pre>' + data.output + '</pre>';
            updateSampleMetrics(data.output);
        } else {
            output.innerHTML = '<div class="text-danger">Demo failed:</div><pre>' + data.error + '</pre>';
        }
    })
    .catch(error => {
        output.innerHTML = '<div class="text-danger">Error running demo:</div><pre>' + error.message + '</pre>';
    })
    .finally(() => {
        btn.disabled = false;
        btn.innerHTML = '<i class="fas fa-play me-2"></i>Run Demo';
    });
}

function updateSampleMetrics(output) {
    const lines = output.split('\n');
    let heartRate = '--', respiration = '--', hrv = '--', riskScore = '--';
    
    lines.forEach(line => {
        if (line.includes('heart_rate')) {
            const match = line.match(/heart_rate['"]:\s*([\d.]+)/);
            if (match) heartRate = Math.round(parseFloat(match[1]));
        }
        if (line.includes('respiration_rate')) {
            const match = line.match(/respiration_rate['"]:\s*([\d.]+)/);
            if (match) respiration = Math.round(parseFloat(match[1]));
        }
        if (line.includes('hrv')) {
            const match = line.match(/hrv['"]:\s*([\d.]+)/);
            if (match) hrv = Math.round(parseFloat(match[1]));
        }
        if (line.includes('risk_score')) {
            const match = line.match(/risk_score['"]:\s*([\d.]+)/);
            if (match) riskScore = Math.round(parseFloat(match[1]));
        }
    });
    
    const heartRateEl = document.getElementById('sampleHeartRate');
    const respirationEl = document.getElementById('sampleRespiration');
    const hrvEl = document.getElementById('sampleHRV');
    const riskScoreEl = document.getElementById('sampleRiskScore');
    
    if (heartRateEl) heartRateEl.textContent = heartRate;
    if (respirationEl) respirationEl.textContent = respiration;
    if (hrvEl) hrvEl.textContent = hrv;
    if (riskScoreEl) riskScoreEl.textContent = riskScore;
}

// Export functions for global use
window.showAlert = showAlert;
window.formatNumber = formatNumber;
window.formatDate = formatDate;
window.makeApiRequest = makeApiRequest;
window.runDemo = runDemo;

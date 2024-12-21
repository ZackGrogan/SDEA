document.addEventListener('DOMContentLoaded', () => {
    const dataRetrievalForm = document.getElementById('data-retrieval-form');
    
    if (dataRetrievalForm) {
        // Form validation
        const startYearInput = document.getElementById('start-year');
        const endYearInput = document.getElementById('end-year');
        const ciksInput = document.getElementById('ciks');
        const submitButton = dataRetrievalForm.querySelector('button[type="submit"]');
        
        const validateForm = () => {
            const startYear = parseInt(startYearInput.value);
            const endYear = parseInt(endYearInput.value);
            const currentYear = new Date().getFullYear();
            let isValid = true;

            // Reset previous validation errors
            startYearInput.classList.remove('is-invalid');
            endYearInput.classList.remove('is-invalid');
            ciksInput.classList.remove('is-invalid');

            // Validate years
            if (isNaN(startYear) || startYear < 1900 || startYear > currentYear) {
                startYearInput.classList.add('is-invalid');
                isValid = false;
            }

            if (isNaN(endYear) || endYear < 1900 || endYear > currentYear) {
                endYearInput.classList.add('is-invalid');
                isValid = false;
            }

            if (startYear > endYear) {
                endYearInput.classList.add('is-invalid');
                isValid = false;
            }

            // Validate CIKs
            const ciks = ciksInput.value.split(',')
                .map(cik => cik.trim())
                .filter(cik => cik);
            
            if (ciks.length === 0) {
                ciksInput.classList.add('is-invalid');
                isValid = false;
            } else {
                // Optional: Add regex validation for CIK format
                const cikRegex = /^\d{10}$/;
                const invalidCiks = ciks.filter(cik => !cikRegex.test(cik));
                
                if (invalidCiks.length > 0) {
                    ciksInput.classList.add('is-invalid');
                    isValid = false;
                }
            }

            submitButton.disabled = !isValid;
            return isValid;
        };
        
        startYearInput.addEventListener('change', validateForm);
        endYearInput.addEventListener('change', validateForm);
        ciksInput.addEventListener('change', validateForm);
        
        dataRetrievalForm.addEventListener('submit', async (e) => {
            e.preventDefault();

            // Remove existing alerts and loading indicators
            const existingAlerts = dataRetrievalForm.querySelectorAll('.alert');
            existingAlerts.forEach(alert => alert.remove());

            const existingSpinner = dataRetrievalForm.querySelector('.spinner-border');
            if (existingSpinner) existingSpinner.remove();

            if (!validateForm()) {
                return;
            }
            
            const startYear = startYearInput.value;
            const endYear = endYearInput.value;
            const ciks = ciksInput.value.split(',')
                .map(cik => cik.trim())
                .filter(cik => cik);
            
            // Loading indicator with ARIA label for accessibility
            const loadingIndicator = document.createElement('div');
            loadingIndicator.classList.add('spinner-border', 'text-primary', 'mt-3');
            loadingIndicator.setAttribute('role', 'status');
            loadingIndicator.setAttribute('aria-label', 'Loading data');
            const loadingSpan = document.createElement('span');
            loadingSpan.classList.add('visually-hidden');
            loadingSpan.textContent = 'Loading...';
            loadingIndicator.appendChild(loadingSpan);
            
            dataRetrievalForm.appendChild(loadingIndicator);
            submitButton.disabled = true;
            
            try {
                const response = await fetch('/retrieve-data', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        startYear: startYear,
                        endYear: endYear,
                        ciks: ciks
                    })
                });
                
                const result = await response.json();
                
                if (result.status === 'success') {
                    // Store retrieved data in localStorage for display page
                    localStorage.setItem('retrievedFilings', JSON.stringify(result.filings));
                    
                    // Create success alert with ARIA label
                    const successAlert = document.createElement('div');
                    successAlert.classList.add('alert', 'alert-success', 'mt-3');
                    successAlert.setAttribute('role', 'alert');
                    successAlert.setAttribute('aria-live', 'polite');
                    successAlert.textContent = `Retrieved ${result.count} filings`;
                    dataRetrievalForm.appendChild(successAlert);
                    
                    // Redirect to display page after 2 seconds
                    setTimeout(() => {
                        window.location.href = '/display-data';
                    }, 2000);
                } else {
                    // Create error alert with ARIA label
                    const errorAlert = document.createElement('div');
                    errorAlert.classList.add('alert', 'alert-danger', 'mt-3');
                    errorAlert.setAttribute('role', 'alert');
                    errorAlert.setAttribute('aria-live', 'assertive');
                    errorAlert.textContent = result.error || 'An unexpected error occurred';
                    dataRetrievalForm.appendChild(errorAlert);
                }
            } catch (error) {
                console.error('Error:', error);
                
                // Create network error alert
                const networkErrorAlert = document.createElement('div');
                networkErrorAlert.classList.add('alert', 'alert-danger', 'mt-3');
                networkErrorAlert.setAttribute('role', 'alert');
                networkErrorAlert.setAttribute('aria-live', 'assertive');
                networkErrorAlert.textContent = 'Network error. Please try again.';
                dataRetrievalForm.appendChild(networkErrorAlert);
            } finally {
                // Re-enable submit button and remove loading indicator
                submitButton.disabled = false;
                const loadingIndicator = dataRetrievalForm.querySelector('.spinner-border');
                if (loadingIndicator) loadingIndicator.remove();
            }
        });
    }
});

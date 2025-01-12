// Form validation and handling
document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('emailForm');
    const signoffSelect = document.getElementById('signoff');
    const customSignoffInput = document.getElementById('customSignoff');
    const goalSelect = document.getElementById('goal');

    // Handle custom sign-off visibility
    signoffSelect.addEventListener('change', function() {
        customSignoffInput.style.display = this.value === 'custom' ? 'block' : 'none';
        if (this.value === 'custom') {
            customSignoffInput.required = true;
        } else {
            customSignoffInput.required = false;
            customSignoffInput.value = '';
        }
    });

    // Form submission handling
    form.addEventListener('submit', function(e) {
        e.preventDefault();
        
        // Basic validation
        const requiredFields = form.querySelectorAll('[required]');
        let isValid = true;

        requiredFields.forEach(field => {
            if (!field.value.trim()) {
                isValid = false;
                highlightError(field);
            } else {
                removeError(field);
            }
        });

        if (!isValid) {
            alert('Please fill in all required fields');
            return;
        }

        // Collect form data
        const formData = new FormData(form);
        const emailData = {};

        formData.forEach((value, key) => {
            emailData[key] = value;
        });

        // Send data to server
        fetch('/generate', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(emailData)
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Handle successful response
                window.location.href = '/preview?id=' + data.emailId;
            } else {
                // Handle error
                alert('Error generating email: ' + data.message);
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('An error occurred while generating the email');
        });
    });

    // Helper functions for form validation
    function highlightError(field) {
        field.classList.add('error');
        field.addEventListener('input', function() {
            if (field.value.trim()) {
                removeError(field);
            }
        });
    }

    function removeError(field) {
        field.classList.remove('error');
    }

    // Clear form helper
    window.clearForm = function() {
        form.reset();
        const errorFields = form.querySelectorAll('.error');
        errorFields.forEach(field => removeError(field));
        customSignoffInput.style.display = 'none';
    };
});

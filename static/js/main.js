// Simple form submission handler
document.getElementById('testRequirementForm').addEventListener('submit', function(e) {
    e.preventDefault();
    const requirement = document.getElementById('testRequirement').value;
    
    if(requirement.trim() === '') {
        alert('Please enter a test requirement.');
        return;
    }
    
    // Send to backend
    fetch('/submit_requirement', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: `requirement=${encodeURIComponent(requirement)}`
    })
    .then(response => response.json())
    .then(data => {
        alert('Test requirement submitted successfully');
        document.getElementById('testRequirement').value = '';
    })
    .catch(error => {
        console.error('Error:', error);
        alert('Error submitting test requirement');
    });
});

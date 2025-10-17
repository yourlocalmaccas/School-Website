function submitForm() {
    const email = document.getElementById('emailInput').value;
    const name = document.getElementById('nameInput').value;
    const phone = document.getElementById('phoneInput').value;
    
    const messageDiv = document.getElementById('message');

    fetch('http://localhost:5000/submit-form', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ email: email, name: name, phone: phone })
    })
    .then(response => response.json())
    .then(data => {
        messageDiv.textContent = data.message;
        
        if (data.status === 'success') {
            document.getElementById('emailInput').value = '';
            document.getElementById('nameInput').value = '';
            document.getElementById('phoneInput').value = '';
        }
    })
    .catch(error => console.error('Error:', error));
}
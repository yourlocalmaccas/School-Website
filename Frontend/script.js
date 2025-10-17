function submitEmail() {
    const email = document.getElementById('emailInput').value;
    
    fetch('http://localhost:5000/verify-email', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ email: email })
    })
    .then(response => response.json())
    .then(data => {
        document.getElementById('message').textContent = data.message;
    })
    .catch(error => console.error('Error:', error));
}
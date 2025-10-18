let currentStudentId = null;
let sports = [];

function submitForm() {
    const email = document.getElementById('emailInput').value;
    const name = document.getElementById('nameInput').value;
    const phone = document.getElementById('phoneInput').value;
    const year = document.getElementById('yearInput').value;
    
    const messageDiv = document.getElementById('message');

    fetch('http://localhost:5000/submit-form', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ email: email, name: name, phone: phone, year: year })
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            currentStudentId = data.student_id;
            loadSports();
            document.getElementById('contactForm').style.display = 'none';
        } else {
            messageDiv.textContent = data.message;
            messageDiv.style.color = 'red';
        }
    })
    .catch(error => {
        messageDiv.textContent = 'Error connecting to backend.';
        messageDiv.style.color = 'red';
        console.error('Error:', error);
    });
}

function loadSports() {
    fetch('http://localhost:5000/get-sports')
        .then(response => response.json())
        .then(data => {
            sports = data.sports;
            const availableSports = sports.filter(s => s.current_count < s.capacity);
            
            if (availableSports.length === 0) {
                document.getElementById('confirmMessage2').textContent = 'Welcome!';
                document.getElementById('sportsSection').style.display = 'none';
                document.getElementById('noSportsSection').style.display = 'block';
            } else {
                document.getElementById('confirmMessage').textContent = 'Welcome! Select a sport:';
                displaySports();
                document.getElementById('sportsSection').style.display = 'block';
                document.getElementById('noSportsSection').style.display = 'none';
            }
        })
        .catch(error => console.error('Error loading sports:', error));
}

function displaySports() {
    const select = document.getElementById('sportSelect');
    select.innerHTML = '<option value="">-- Select a sport --</option>';
    
    sports.forEach(sport => {
        const isFull = sport.current_count >= sport.capacity;
        const option = document.createElement('option');
        option.value = sport.id;
        option.textContent = isFull ? `${sport.name} (${sport.current_count}/${sport.capacity}) - FULL` : `${sport.name} (${sport.current_count}/${sport.capacity})`;
        option.disabled = isFull;
        select.appendChild(option);
    });
}

document.getElementById('sportSelect').addEventListener('change', function() {
    const sportId = this.value;
    if (!sportId) {
        document.getElementById('sportStatus').textContent = '';
        return;
    }
    
    const sport = sports.find(s => s.id == sportId);
    const isFull = sport.current_count >= sport.capacity;
    document.getElementById('sportStatus').textContent = isFull ? 'This sport is full.' : `Available spots: ${sport.capacity - sport.current_count}`;
    document.getElementById('sportStatus').style.color = isFull ? 'red' : 'green';
});

function submitSport() {
    const sportId = document.getElementById('sportSelect').value;
    const sportsMessage = document.getElementById('sportsMessage');

    if (!sportId) {
        sportsMessage.textContent = 'Please select a sport.';
        sportsMessage.style.color = 'red';
        return;
    }

    fetch('http://localhost:5000/submit-sport', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ student_id: currentStudentId, sport_id: sportId })
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            const sport = sports.find(s => s.id == sportId);
            document.getElementById('successMessage').textContent = `You have been registered for ${sport.name}!`;
            document.getElementById('sportsSection').style.display = 'none';
            document.getElementById('successSection').style.display = 'block';
        } else {
            sportsMessage.textContent = data.message;
            sportsMessage.style.color = 'red';
            loadSports();
        }
    })
    .catch(error => {
        sportsMessage.textContent = 'Error submitting sport.';
        sportsMessage.style.color = 'red';
        console.error('Error:', error);
    });
}

function saveWaitlist() {
    document.getElementById('successMessage').textContent = `Thank you! Your information has been saved. We will contact you when a sport becomes available.`;
    document.getElementById('noSportsSection').style.display = 'none';
    document.getElementById('successSection').style.display = 'block';
}

document.getElementById('emailInput').addEventListener('keypress', function(e) {
    if (e.key === 'Enter') submitForm();
});
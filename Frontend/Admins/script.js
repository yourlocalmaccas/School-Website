let allTerms = [];
let currentTerm = null;
let allSports = [];
let allStudents = [];
let deleteCodeValue = null;

function switchSection(sectionId) {
    document.querySelectorAll('.section').forEach(s => s.classList.remove('active'));
    document.querySelectorAll('.sidebar-item').forEach(s => s.classList.remove('active'));
    document.getElementById(sectionId).classList.add('active');
    event.target.classList.add('active');
}

function loadTerms() {
    fetch('http://localhost:5000/get-all-terms')
        .then(response => response.json())
        .then(data => {
            allTerms = data.terms;
            displayTerms();
            populateExportTerms();
            loadCurrentTerm();
        })
        .catch(error => console.error('Error loading terms:', error));
}

function displayTerms() {
    const select = document.getElementById('termSelect');
    select.innerHTML = '';
    allTerms.forEach(term => {
        const option = document.createElement('option');
        option.value = term.id;
        option.textContent = `${term.term_name} ${term.year}${term.is_active ? ' (Active)' : ''}`;
        select.appendChild(option);
    });
}

function populateExportTerms() {
    const select = document.getElementById('exportTermSelect');
    select.innerHTML = '';
    allTerms.forEach(term => {
        const option = document.createElement('option');
        option.value = term.id;
        option.textContent = `${term.term_name} ${term.year}`;
        select.appendChild(option);
    });
    if (allTerms.length > 0) {
        select.value = allTerms[0].id;
    }
}

function loadCurrentTerm() {
    fetch('http://localhost:5000/get-current-term')
        .then(response => response.json())
        .then(data => {
            currentTerm = data;
            document.getElementById('termSelect').value = data.term_id;
            loadAllData();
        })
        .catch(error => console.error('Error loading current term:', error));
}

function switchTerm() {
    const termId = document.getElementById('termSelect').value;
    if (termId) {
        fetch(`http://localhost:5000/set-active-term/${termId}`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
        })
        .then(response => response.json())
        .then(data => {
            loadCurrentTerm();
        })
        .catch(error => console.error('Error switching term:', error));
    }
}

function createTerm() {
    const termName = document.getElementById('termName').value.trim();
    const year = document.getElementById('termYear').value;
    
    if (!termName || !year) {
        alert('Enter term name and year');
        return;
    }

    fetch('http://localhost:5000/create-term', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ term_name: termName, year: parseInt(year) })
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            showMessage('termMessage', 'Term created!', 'success');
            document.getElementById('termName').value = '';
            document.getElementById('termYear').value = '';
            loadTerms();
        }
    })
    .catch(error => console.error('Error creating term:', error));
}

function loadAllData() {
    loadSports();
    loadSystemStatus();
    loadStudents();
}

function loadSports() {
    fetch(`http://localhost:5000/get-sports?term_id=${currentTerm.term_id}`)
        .then(response => response.json())
        .then(data => {
            allSports = data.sports;
            displaySports();
            displaySportRegistrations();
        })
        .catch(error => console.error('Error loading sports:', error));
}

function displaySports() {
    const sportsList = document.getElementById('sportsList');
    sportsList.innerHTML = '';
    
    allSports.forEach(sport => {
        const div = document.createElement('div');
        div.className = 'sport-section';
        div.innerHTML = `
            <strong>${sport.name}</strong>${sport.description ? ` - ${sport.description}` : ''}<br>
            ${sport.current_count}/${sport.capacity}<br>
            <input type="number" id="capacity-${sport.id}" value="${sport.capacity}" min="1" style="width: 80px;">
            <button class="btn-primary" onclick="updateSportCapacity(${sport.id})">Update</button>
            <button class="btn-warning" onclick="markSportFull(${sport.id})">Mark Full</button>
            <button class="btn-danger" onclick="deleteSport(${sport.id})">Delete</button>
        `;
        sportsList.appendChild(div);
    });
}

function displaySportRegistrations() {
    const section = document.getElementById('sportRegistrations');
    section.innerHTML = '';
    
    allSports.forEach(sport => {
        fetch(`http://localhost:5000/get-sport-registrations/${sport.id}`)
            .then(response => response.json())
            .then(data => {
                const div = document.createElement('div');
                div.className = 'sport-section';
                div.innerHTML = `<h3>${sport.name} (${data.students.length})</h3>`;
                
                data.students.forEach(student => {
                    const p = document.createElement('p');
                    p.innerHTML = `${student.name} (Yr ${student.year}) - <a href="mailto:${student.email}">${student.email}</a> - ${student.phone}`;
                    div.appendChild(p);
                });
                
                if (data.students.length === 0) {
                    div.innerHTML += '<p>No registrations</p>';
                }
                
                section.appendChild(div);
            });
    });
}

function loadStudents() {
    fetch(`http://localhost:5000/get-all-data?term_id=${currentTerm.term_id}`)
        .then(response => response.json())
        .then(data => {
            allStudents = data.students;
            setupStudentFilterDropdowns();
        })
        .catch(error => console.error('Error loading students:', error));
}

function setupStudentFilterDropdowns() {
    const filterTermSelect = document.getElementById('filterTermSelect');
    const filterSportSelect = document.getElementById('filterSportSelect');
    
    filterTermSelect.innerHTML = '';
    allTerms.forEach(term => {
        const option = document.createElement('option');
        option.value = term.id;
        option.textContent = `${term.term_name} ${term.year}`;
        filterTermSelect.appendChild(option);
    });
    if (allTerms.length > 0) {
        filterTermSelect.value = currentTerm.term_id;
    }
    
    filterSportSelect.innerHTML = '<option value="">All Sports</option>';
    allSports.forEach(sport => {
        const option = document.createElement('option');
        option.value = sport.id;
        option.textContent = sport.name;
        filterSportSelect.appendChild(option);
    });
    
    applyStudentFilters();
}

function applyStudentFilters() {
    const filterTerm = document.getElementById('filterTermSelect').value;
    const filterYear = document.getElementById('filterYearSelect').value;
    const filterSport = document.getElementById('filterSportSelect').value;
    
    const tbody = document.getElementById('studentsTableBody');
    tbody.innerHTML = '';
    
    fetch(`http://localhost:5000/get-all-data?term_id=${filterTerm}`)
        .then(response => response.json())
        .then(data => {
            let students = data.students || [];
            
            if (filterYear) {
                students = students.filter(s => s.year === filterYear);
            }
            
            if (filterSport) {
                fetch(`http://localhost:5000/get-sport-registrations/${filterSport}`)
                    .then(r => r.json())
                    .then(sportData => {
                        const registeredIds = sportData.students.map(s => s.id);
                        students = students.filter(s => registeredIds.includes(s.id));
                        displayStudentsTable(students, filterSport);
                    });
            } else {
                displayStudentsTable(students, null);
            }
        })
        .catch(error => console.error('Error applying filters:', error));
}

function displayStudentsTable(students, sportId) {
    const tbody = document.getElementById('studentsTableBody');
    tbody.innerHTML = '';
    
    if (students.length === 0) {
        const row = document.createElement('tr');
        row.innerHTML = '<td colspan="6" style="padding: 10px; text-align: center;">No students match the selected filters</td>';
        tbody.appendChild(row);
        return;
    }
    
    // Sort by last name alphabetically
    students.sort((a, b) => {
        const lastNameA = a.name.split(' ').pop().toLowerCase();
        const lastNameB = b.name.split(' ').pop().toLowerCase();
        return lastNameA.localeCompare(lastNameB);
    });
    
    students.forEach(student => {
        const row = document.createElement('tr');
        row.style.borderBottom = '1px solid #ecf0f1';
        
        let sportName = '';
        if (sportId) {
            const sport = allSports.find(s => s.id == sportId);
            sportName = sport ? sport.name : 'N/A';
        } else {
            sportName = '-';
        }
        
        row.innerHTML = `
            <td style="padding: 10px;">${student.name}</td>
            <td style="padding: 10px;"><a href="mailto:${student.email}">${student.email}</a></td>
            <td style="padding: 10px;">${student.phone}</td>
            <td style="padding: 10px;">Year ${student.year}</td>
            <td style="padding: 10px;">${sportName}</td>
            <td style="padding: 10px;"><button class="btn-delete" onclick="deleteStudent(${student.id})">Delete</button></td>
        `;
        tbody.appendChild(row);
    });
}

function loadWaitlist() {
    fetch(`http://localhost:5000/get-waitlist?term_id=${currentTerm.term_id}`)
        .then(response => response.json())
        .then(data => {
            const section = document.getElementById('waitlistList');
            section.innerHTML = '';
            
            if (data.waitlist.length === 0) {
                section.innerHTML = '<p>No waitlisted students.</p>';
                return;
            }
            
            data.waitlist.forEach(student => {
                const p = document.createElement('p');
                p.className = 'waitlist-item';
                p.innerHTML = `<span><strong>${student.name}</strong> (Yr ${student.year}) - <a href="mailto:${student.email}">${student.email}</a> - ${student.phone}</span> <button class="btn-delete" onclick="deleteStudent(${student.id})">Delete</button>`;
                section.appendChild(p);
            });
        })
        .catch(error => console.error('Error loading waitlist:', error));
}

function addSport() {
    const name = document.getElementById('newSportName').value.trim();
    const description = document.getElementById('newSportDescription').value.trim();
    const capacity = document.getElementById('newSportCapacity').value;

    if (!name) {
        alert('Enter a sport name');
        return;
    }

    fetch('http://localhost:5000/add-sport', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ name: name, description: description, capacity: parseInt(capacity), term_id: currentTerm.term_id })
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            document.getElementById('newSportName').value = '';
            document.getElementById('newSportDescription').value = '';
            loadSports();
        } else {
            alert(data.message);
        }
    })
    .catch(error => console.error('Error adding sport:', error));
}

function updateSportCapacity(sportId) {
    const newCapacity = document.getElementById('capacity-' + sportId).value;

    fetch(`http://localhost:5000/update-sport/${sportId}`, {
        method: 'PUT',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ capacity: parseInt(newCapacity) })
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            loadSports();
        } else {
            alert(data.message);
        }
    })
    .catch(error => console.error('Error updating sport:', error));
}

function markSportFull(sportId) {
    const sport = allSports.find(s => s.id === sportId);
    if (!sport) return;
    
    const newCapacity = sport.current_count;
    
    fetch(`http://localhost:5000/update-sport/${sportId}`, {
        method: 'PUT',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ capacity: newCapacity })
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            loadSports();
            alert(`${sport.name} marked as full`);
        }
    })
    .catch(error => console.error('Error marking full:', error));
}

function deleteSport(sportId) {
    if (!confirm('Delete this sport?')) return;

    fetch(`http://localhost:5000/delete-sport/${sportId}`, {
        method: 'DELETE',
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            loadSports();
        }
    })
    .catch(error => console.error('Error deleting sport:', error));
}

function deleteStudent(studentId) {
    if (!confirm('Delete this student?')) return;

    fetch(`http://localhost:5000/delete-student/${studentId}`, {
        method: 'DELETE',
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            loadAllData();
        }
    })
    .catch(error => console.error('Error deleting student:', error));
}

function loadSystemStatus() {
    fetch('http://localhost:5000/get-system-status')
        .then(response => response.json())
        .then(data => {
            const statusText = data.is_open ? 'OPEN' : 'CLOSED';
            const statusClass = data.is_open ? 'status-open' : 'status-closed';
            document.getElementById('statusText').textContent = statusText;
            document.getElementById('statusText').className = statusClass;
            document.getElementById('scheduleText').textContent = data.open_datetime || 'None';
        })
        .catch(error => console.error('Error loading system status:', error));
}

function scheduleOpen() {
    const date = document.getElementById('openDate').value;
    const time = document.getElementById('openTime').value;
    
    if (!date || !time) {
        alert('Please select both date and time');
        return;
    }

    const datetime = `${date}T${time}`;

    fetch('http://localhost:5000/set-system-status', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ is_open: false, open_datetime: datetime })
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            showMessage('systemMessage', `Scheduled for ${datetime}`, 'success');
            document.getElementById('openDate').value = '';
            document.getElementById('openTime').value = '';
            loadSystemStatus();
        }
    })
    .catch(error => console.error('Error scheduling:', error));
}

function openNow() {
    fetch('http://localhost:5000/set-system-status', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ is_open: true })
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            showMessage('systemMessage', 'Now OPEN!', 'success');
            loadSystemStatus();
        }
    })
    .catch(error => console.error('Error opening:', error));
}

function closeNow() {
    fetch('http://localhost:5000/set-system-status', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ is_open: false })
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            showMessage('systemMessage', 'Now CLOSED!', 'success');
            loadSystemStatus();
        }
    })
    .catch(error => console.error('Error closing:', error));
}

function clearSchedule() {
    fetch('http://localhost:5000/set-system-status', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ is_open: false, open_datetime: '' })
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            showMessage('systemMessage', 'Schedule cleared!', 'success');
            document.getElementById('openDate').value = '';
            document.getElementById('openTime').value = '';
            loadSystemStatus();
        }
    })
    .catch(error => console.error('Error clearing schedule:', error));
}

function startDeleteAll() {
    fetch('http://localhost:5000/generate-delete-code')
        .then(response => response.json())
        .then(data => {
            deleteCodeValue = data.code;
            document.getElementById('deleteCode').textContent = data.code;
            document.getElementById('deletePrompt').style.display = 'block';
        })
        .catch(error => console.error('Error generating code:', error));
}

function confirmDeleteAll() {
    const inputCode = document.getElementById('deleteCodeInput').value.toUpperCase();
    
    if (inputCode !== deleteCodeValue) {
        alert('Code does not match.');
        return;
    }

    if (!confirm('Delete ALL students in this term?')) return;

    fetch(`http://localhost:5000/delete-all-students?term_id=${currentTerm.term_id}`, {
        method: 'DELETE',
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            alert('All students deleted!');
            cancelDeleteAll();
            loadAllData();
        }
    })
    .catch(error => console.error('Error deleting all:', error));
}

function cancelDeleteAll() {
    document.getElementById('deletePrompt').style.display = 'none';
    document.getElementById('deleteCodeInput').value = '';
    deleteCodeValue = null;
}

function exportToCSV() {
    const exportTermId = document.getElementById('exportTermSelect').value;
    if (!exportTermId) {
        alert('Please select a term');
        return;
    }

    const selectedTerm = allTerms.find(t => t.id == exportTermId);

    fetch(`http://localhost:5000/get-all-data?term_id=${exportTermId}`)
        .then(response => response.json())
        .then(data => {
            let csvContent = 'data:text/csv;charset=utf-8,';
            
            const years = ['7', '8', '9', '10'];
            years.forEach(year => {
                csvContent += `\nYear ${year}\n`;
                csvContent += 'Name,Email,Phone\n';
                
                const yearStudents = data.students.filter(s => s.year === year);
                yearStudents.sort((a, b) => {
                    const lastNameA = a.name.split(' ').pop();
                    const lastNameB = b.name.split(' ').pop();
                    return lastNameA.localeCompare(lastNameB);
                });
                
                yearStudents.forEach(student => {
                    csvContent += `${student.name},${student.email},${student.phone}\n`;
                });
            });
            
            const link = document.createElement('a');
            link.setAttribute('href', encodeURI(csvContent));
            link.setAttribute('download', `sports_data_${selectedTerm.term_name}_${selectedTerm.year}.csv`);
            link.click();
        })
        .catch(error => console.error('Error exporting:', error));
}

function showMessage(elementId, text, type) {
    const el = document.getElementById(elementId);
    el.textContent = text;
    el.className = `message ${type}`;
    setTimeout(() => {
        el.className = 'message';
    }, 3000);
}

setInterval(() => {
    if (currentTerm) {
        loadSports();
        loadSystemStatus();
    }
}, 2000);

loadTerms();
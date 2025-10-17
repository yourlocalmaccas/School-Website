from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

saved_students = []

@app.route('/submit-form', methods=['POST', 'OPTIONS'])
def submit_form():
    if request.method == "OPTIONS":
        return '', 200
    
    data = request.get_json()
    email = data.get('email', '').strip()
    name = data.get('name', '').strip()
    phone = data.get('phone', '').strip()
    
    print(f"Received - Email: {email}, Name: {name}, Phone: {phone}")
    
    if not email:
        return jsonify({'status': 'error', 'message': 'Email cannot be empty.'}), 400
    
    if not email.endswith('@stmarks.nsw.edu.au'):
        return jsonify({'status': 'error', 'message': 'Email must end with @stmarks.nsw.edu.au'}), 400
    
    if not name:
        return jsonify({'status': 'error', 'message': 'Name cannot be empty.'}), 400
    
    if len(name) < 2:
        return jsonify({'status': 'error', 'message': 'Name must be at least 2 characters.'}), 400
    
    if not phone:
        return jsonify({'status': 'error', 'message': 'Phone cannot be empty.'}), 400
    
    if len(phone) != 10 or not phone.isdigit() or phone[0] != '0':
        return jsonify({'status': 'error', 'message': 'Phone must be 10 digits starting with 0.'}), 400
    
    # Check if email already exists
    for student in saved_students:
        if student['email'] == email:
            return jsonify({'status': 'exists', 'message': 'Email already entered.'}), 400
    
    # Save all the data together
    saved_students.append({
        'email': email,
        'name': name,
        'phone': phone
    })
    print(f"Saved students: {saved_students}")
    return jsonify({'status': 'success', 'message': f'Form submitted!'}), 200

@app.route('/get-all-data', methods=['GET'])
def get_all_data():
    return jsonify({'students': saved_students}), 200

if __name__ == '__main__':
    app.run(debug=True)
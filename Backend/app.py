from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
CORS(app)

#stupid database setup
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///students.db'
db = SQLAlchemy(app)

class Student(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(10), nullable=False)

with app.app_context():
    db.create_all()

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
    
    if Student.query.filter_by(email=email).first():
        return jsonify({'status': 'exists', 'message': 'Email already entered.'}), 400
    
    new_student = Student(email=email, name=name, phone=phone)
    db.session.add(new_student)
    db.session.commit()
    
    print(f"Student saved to database: {email}")
    return jsonify({'status': 'success', 'message': f'Form submitted!'}), 200

@app.route('/get-all-data', methods=['GET'])
def get_all_data():
    # bleh querys, what are they anyway?
    students = Student.query.all()
    student_list = [{'email': s.email, 'name': s.name, 'phone': s.phone} for s in students]
    return jsonify({'students': student_list}), 200

if __name__ == '__main__':
    app.run(debug=True)
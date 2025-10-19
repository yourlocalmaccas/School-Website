from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
import secrets
from datetime import datetime

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///sports_system.db'
db = SQLAlchemy(app)

class Term(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    term_name = db.Column(db.String(50), nullable=False)
    year = db.Column(db.Integer, nullable=False)
    is_active = db.Column(db.Boolean, default=True)

class Student(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(10), nullable=False)
    year = db.Column(db.String(2), nullable=False)
    term_id = db.Column(db.Integer, db.ForeignKey('term.id'), nullable=False)

class Sport(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    capacity = db.Column(db.Integer, nullable=False)
    current_count = db.Column(db.Integer, default=0)
    is_open = db.Column(db.Boolean, default=True)
    term_id = db.Column(db.Integer, db.ForeignKey('term.id'), nullable=False)

class StudentSport(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    sport_id = db.Column(db.Integer, db.ForeignKey('sport.id'), nullable=False)

class Waitlist(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    timestamp = db.Column(db.DateTime, default=db.func.now())
    has_sport = db.Column(db.Boolean, default=False)

class SystemStatus(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    is_open = db.Column(db.Boolean, default=False)
    open_datetime = db.Column(db.String(50), default='')
    term_id = db.Column(db.Integer, db.ForeignKey('term.id'), nullable=False)

with app.app_context():
    db.create_all()
    if Term.query.count() == 0:
        current_term = Term(term_name='Term 1', year=2025, is_active=True)
        db.session.add(current_term)
        db.session.commit()

@app.route('/get-current-term', methods=['GET'])
def get_current_term():
    term = Term.query.filter_by(is_active=True).first()
    if not term:
        term = Term.query.order_by(Term.id.desc()).first()
    return jsonify({'term_id': term.id, 'term_name': term.term_name, 'year': term.year}), 200

@app.route('/get-all-terms', methods=['GET'])
def get_all_terms():
    terms = Term.query.order_by(Term.year.desc(), Term.id.desc()).all()
    terms_list = [{'id': t.id, 'term_name': t.term_name, 'year': t.year, 'is_active': t.is_active} for t in terms]
    return jsonify({'terms': terms_list}), 200

@app.route('/create-term', methods=['POST', 'OPTIONS'])
def create_term():
    if request.method == "OPTIONS":
        return '', 200
    data = request.get_json()
    term_name = data.get('term_name', '').strip()
    year = data.get('year')
    
    if not term_name or not year:
        return jsonify({'status': 'error', 'message': 'Term name and year required.'}), 400
    
    new_term = Term(term_name=term_name, year=year, is_active=False)
    db.session.add(new_term)
    db.session.commit()
    return jsonify({'status': 'success', 'message': 'Term created.', 'term_id': new_term.id}), 200

@app.route('/set-active-term/<int:term_id>', methods=['POST', 'OPTIONS'])
def set_active_term(term_id):
    if request.method == "OPTIONS":
        return '', 200
    Term.query.update({'is_active': False})
    term = Term.query.get(term_id)
    if term:
        term.is_active = True
        db.session.commit()
    return jsonify({'status': 'success', 'message': 'Term activated.'}), 200

@app.route('/submit-form', methods=['POST', 'OPTIONS'])
def submit_form():
    if request.method == "OPTIONS":
        return '', 200
    
    data = request.get_json()
    email = data.get('email', '').strip()
    name = data.get('name', '').strip()
    phone = data.get('phone', '').strip()
    year = data.get('year', '').strip()
    
    if not email or not email.endswith('@stmarks.nsw.edu.au'):
        return jsonify({'status': 'error', 'message': 'Invalid email.'}), 400
    
    if not name or len(name) < 2:
        return jsonify({'status': 'error', 'message': 'Invalid name.'}), 400
    
    if not phone or len(phone) != 10 or not phone.isdigit() or phone[0] != '0':
        return jsonify({'status': 'error', 'message': 'Invalid phone.'}), 400
    
    if not year or year not in ['7', '8', '9', '10']:
        return jsonify({'status': 'error', 'message': 'Invalid year.'}), 400
    
    current_term = Term.query.filter_by(is_active=True).first()
    if not current_term:
        return jsonify({'status': 'error', 'message': 'No active term.'}), 400
    
    existing = Student.query.filter_by(email=email, term_id=current_term.id).first()
    if existing:
        return jsonify({'status': 'error', 'message': 'Already registered this term.'}), 400
    
    try:
        new_student = Student(email=email, name=name, phone=phone, year=year, term_id=current_term.id)
        db.session.add(new_student)
        db.session.commit()
        return jsonify({'status': 'success', 'message': 'Contact info saved!', 'student_id': new_student.id}), 200
    except:
        db.session.rollback()
        return jsonify({'status': 'error', 'message': 'Error saving data.'}), 400

@app.route('/get-sports', methods=['GET'])
def get_sports():
    term_id = request.args.get('term_id')
    if not term_id:
        current_term = Term.query.filter_by(is_active=True).first()
        term_id = current_term.id if current_term else None
    
    sports = Sport.query.filter_by(term_id=term_id).all()
    sports_list = [{'id': s.id, 'name': s.name, 'capacity': s.capacity, 'current_count': s.current_count, 'is_open': s.is_open} for s in sports]
    return jsonify({'sports': sports_list}), 200

@app.route('/submit-sport', methods=['POST', 'OPTIONS'])
def submit_sport():
    if request.method == "OPTIONS":
        return '', 200
    
    data = request.get_json()
    student_id = data.get('student_id')
    sport_id = data.get('sport_id')
    
    sport = Sport.query.get(sport_id)
    if not sport or sport.current_count >= sport.capacity or not sport.is_open:
        return jsonify({'status': 'error', 'message': 'Sport is unavailable.'}), 400
    
    sport_selection = StudentSport(student_id=student_id, sport_id=sport_id)
    sport.current_count += 1
    db.session.add(sport_selection)
    
    waitlist_entry = Waitlist.query.filter_by(student_id=student_id).first()
    if waitlist_entry:
        waitlist_entry.has_sport = True
    
    db.session.commit()
    
    return jsonify({'status': 'success', 'message': 'Sport submitted!'}), 200

@app.route('/get-all-data', methods=['GET'])
def get_all_data():
    term_id = request.args.get('term_id')
    if not term_id:
        current_term = Term.query.filter_by(is_active=True).first()
        term_id = current_term.id if current_term else None
    
    students = Student.query.filter_by(term_id=term_id).all()
    student_list = [{'id': s.id, 'email': s.email, 'name': s.name, 'phone': s.phone, 'year': s.year} for s in students]
    return jsonify({'students': student_list}), 200

@app.route('/get-students-by-year', methods=['GET'])
def get_students_by_year():
    term_id = request.args.get('term_id')
    year = request.args.get('year')
    
    if not term_id or not year:
        return jsonify({'error': 'term_id and year required'}), 400
    
    students = Student.query.filter_by(term_id=term_id, year=year).all()
    students_sorted = sorted(students, key=lambda s: s.name.split()[-1])
    student_list = [{'id': s.id, 'email': s.email, 'name': s.name, 'phone': s.phone, 'year': s.year} for s in students_sorted]
    return jsonify({'students': student_list}), 200

@app.route('/get-sport-registrations/<int:sport_id>', methods=['GET'])
def get_sport_registrations(sport_id):
    registrations = db.session.query(Student, StudentSport).join(StudentSport).filter(StudentSport.sport_id == sport_id).all()
    student_list = [{'id': s.id, 'name': s.name, 'email': s.email, 'year': s.year} for s, _ in registrations]
    return jsonify({'students': student_list}), 200

@app.route('/get-unregistered-students', methods=['GET'])
def get_unregistered_students():
    term_id = request.args.get('term_id')
    if not term_id:
        current_term = Term.query.filter_by(is_active=True).first()
        term_id = current_term.id if current_term else None
    
    all_students = Student.query.filter_by(term_id=term_id).all()
    registered_ids = db.session.query(StudentSport.student_id).distinct().all()
    registered_ids = [r[0] for r in registered_ids]
    
    unregistered = [s for s in all_students if s.id not in registered_ids]
    unregistered_sorted = sorted(unregistered, key=lambda s: s.name.split()[-1])
    student_list = [{'id': s.id, 'name': s.name, 'email': s.email, 'year': s.year} for s in unregistered_sorted]
    return jsonify({'students': student_list}), 200

@app.route('/delete-student/<int:student_id>', methods=['DELETE'])
def delete_student(student_id):
    student = Student.query.get(student_id)
    if not student:
        return jsonify({'status': 'error', 'message': 'Student not found.'}), 400
    
    selections = StudentSport.query.filter_by(student_id=student_id).all()
    for selection in selections:
        sport = Sport.query.get(selection.sport_id)
        sport.current_count -= 1
    
    Waitlist.query.filter_by(student_id=student_id).delete()
    db.session.delete(student)
    db.session.commit()
    return jsonify({'status': 'success', 'message': 'Student deleted.'}), 200

@app.route('/delete-all-students', methods=['DELETE'])
def delete_all_students():
    term_id = request.args.get('term_id')
    StudentSport.query.delete()
    students = Student.query.filter_by(term_id=term_id).all()
    for sport in Sport.query.filter_by(term_id=term_id).all():
        sport.current_count = 0
    for student in students:
        db.session.delete(student)
    db.session.commit()
    return jsonify({'status': 'success', 'message': 'All students deleted.'}), 200

@app.route('/add-sport', methods=['POST', 'OPTIONS'])
def add_sport():
    if request.method == "OPTIONS":
        return '', 200
    
    data = request.get_json()
    sport_name = data.get('name', '').strip()
    capacity = data.get('capacity', 20)
    term_id = data.get('term_id')
    
    if not sport_name or not term_id:
        return jsonify({'status': 'error', 'message': 'Sport name and term required.'}), 400
    
    new_sport = Sport(name=sport_name, capacity=capacity, is_open=True, term_id=term_id)
    db.session.add(new_sport)
    db.session.commit()
    return jsonify({'status': 'success', 'message': 'Sport added.'}), 200

@app.route('/update-sport/<int:sport_id>', methods=['PUT', 'OPTIONS'])
def update_sport(sport_id):
    if request.method == "OPTIONS":
        return '', 200
    
    data = request.get_json()
    sport = Sport.query.get(sport_id)
    if not sport:
        return jsonify({'status': 'error', 'message': 'Sport not found.'}), 400
    
    if 'capacity' in data:
        sport.capacity = data.get('capacity')
    if 'name' in data:
        sport.name = data.get('name')
    if 'is_open' in data:
        sport.is_open = data.get('is_open')
    
    db.session.commit()
    return jsonify({'status': 'success', 'message': 'Sport updated.'}), 200

@app.route('/delete-sport/<int:sport_id>', methods=['DELETE'])
def delete_sport(sport_id):
    sport = Sport.query.get(sport_id)
    if not sport:
        return jsonify({'status': 'error', 'message': 'Sport not found.'}), 400
    
    StudentSport.query.filter_by(sport_id=sport_id).delete()
    db.session.delete(sport)
    db.session.commit()
    return jsonify({'status': 'success', 'message': 'Sport deleted.'}), 200

@app.route('/get-system-status', methods=['GET'])
def get_system_status():
    current_term = Term.query.filter_by(is_active=True).first()
    if not current_term:
        return jsonify({'is_open': False, 'open_datetime': ''}), 200
    
    status = SystemStatus.query.filter_by(term_id=current_term.id).first()
    if not status:
        status = SystemStatus(is_open=False, open_datetime='', term_id=current_term.id)
        db.session.add(status)
        db.session.commit()
    
    if not status.is_open and status.open_datetime:
        try:
            scheduled = datetime.fromisoformat(status.open_datetime)
            now = datetime.now()
            if now >= scheduled:
                status.is_open = True
                db.session.commit()
        except:
            pass
    
    return jsonify({'is_open': status.is_open, 'open_datetime': status.open_datetime}), 200

@app.route('/set-system-status', methods=['POST', 'OPTIONS'])
def set_system_status():
    if request.method == "OPTIONS":
        return '', 200
    
    current_term = Term.query.filter_by(is_active=True).first()
    if not current_term:
        return jsonify({'status': 'error', 'message': 'No active term.'}), 400
    
    data = request.get_json()
    status = SystemStatus.query.filter_by(term_id=current_term.id).first()
    if not status:
        status = SystemStatus(is_open=data.get('is_open', False), open_datetime=data.get('open_datetime', ''), term_id=current_term.id)
        db.session.add(status)
    else:
        if 'is_open' in data:
            status.is_open = data.get('is_open')
        if 'open_datetime' in data:
            status.open_datetime = data.get('open_datetime')
    
    db.session.commit()
    return jsonify({'status': 'success', 'message': 'System status updated.'}), 200

@app.route('/generate-delete-code', methods=['GET'])
def generate_delete_code():
    code = secrets.token_hex(4).upper()
    return jsonify({'code': code}), 200

@app.route('/get-waitlist', methods=['GET'])
def get_waitlist():
    term_id = request.args.get('term_id')
    if not term_id:
        current_term = Term.query.filter_by(is_active=True).first()
        term_id = current_term.id if current_term else None
    
    waitlisted = db.session.query(Student, Waitlist).join(Waitlist).filter(Student.term_id == term_id, Waitlist.has_sport == False).all()
    waitlist_data = [{'id': s.id, 'email': s.email, 'name': s.name, 'phone': s.phone, 'year': s.year} for s, w in waitlisted]
    return jsonify({'waitlist': waitlist_data}), 200

@app.route('/add-to-waitlist/<int:student_id>', methods=['POST', 'OPTIONS'])
def add_to_waitlist(student_id):
    if request.method == "OPTIONS":
        return '', 200
    if not Waitlist.query.filter_by(student_id=student_id).first():
        waitlist_entry = Waitlist(student_id=student_id)
        db.session.add(waitlist_entry)
        db.session.commit()
    return jsonify({'status': 'success', 'message': 'Added to waitlist.'}), 200

if __name__ == '__main__':
    app.run(debug=True)
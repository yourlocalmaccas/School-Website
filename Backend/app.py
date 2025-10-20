from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
import secrets
from datetime import datetime
import logging
from flask import send_from_directory



app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///sports_system.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

@app.route('/')
def index():
    return send_from_directory('Frontend', 'index.html')

@app.route('/<path:path>')
def serve_static(path):
    return send_from_directory('Frontend', path)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
    description = db.Column(db.String(500), default='')
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
    try:
        db.create_all()
        if Term.query.count() == 0:
            current_term = Term(term_name='Term 1', year=2025, is_active=True)
            db.session.add(current_term)
            db.session.commit()
            logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Database initialization error: {str(e)}")

@app.errorhandler(404)
def not_found(error):
    return jsonify({'status': 'error', 'message': 'Endpoint not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    logger.error(f"Internal server error: {str(error)}")
    return jsonify({'status': 'error', 'message': 'Server error occurred'}), 500

@app.route('/get-current-term', methods=['GET'])
def get_current_term():
    try:
        term = Term.query.filter_by(is_active=True).first()
        if not term:
            term = Term.query.order_by(Term.id.desc()).first()
        
        if not term:
            return jsonify({'status': 'error', 'message': 'No terms found'}), 404
        
        return jsonify({'term_id': term.id, 'term_name': term.term_name, 'year': term.year}), 200
    except Exception as e:
        logger.error(f"Error fetching current term: {str(e)}")
        return jsonify({'status': 'error', 'message': 'Error fetching current term'}), 500

@app.route('/get-all-terms', methods=['GET'])
def get_all_terms():
    try:
        terms = Term.query.order_by(Term.year.desc(), Term.id.desc()).all()
        terms_list = [{'id': t.id, 'term_name': t.term_name, 'year': t.year, 'is_active': t.is_active} for t in terms]
        return jsonify({'terms': terms_list}), 200
    except Exception as e:
        logger.error(f"Error fetching all terms: {str(e)}")
        return jsonify({'status': 'error', 'message': 'Error fetching terms'}), 500

@app.route('/create-term', methods=['POST', 'OPTIONS'])
def create_term():
    if request.method == "OPTIONS":
        return '', 200
    
    try:
        data = request.get_json()
        if not data:
            return jsonify({'status': 'error', 'message': 'No data provided'}), 400
        
        term_name = data.get('term_name', '').strip()
        year = data.get('year')
        
        if not term_name or not year:
            return jsonify({'status': 'error', 'message': 'Term name and year required'}), 400
        
        try:
            year = int(year)
        except ValueError:
            return jsonify({'status': 'error', 'message': 'Year must be a number'}), 400
        
        new_term = Term(term_name=term_name, year=year, is_active=False)
        db.session.add(new_term)
        db.session.commit()
        return jsonify({'status': 'success', 'message': 'Term created', 'term_id': new_term.id}), 200
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error creating term: {str(e)}")
        return jsonify({'status': 'error', 'message': 'Error creating term'}), 500

@app.route('/set-active-term/<int:term_id>', methods=['POST', 'OPTIONS'])
def set_active_term(term_id):
    if request.method == "OPTIONS":
        return '', 200
    
    try:
        term = Term.query.get(term_id)
        if not term:
            return jsonify({'status': 'error', 'message': 'Term not found'}), 404
        
        Term.query.update({'is_active': False})
        term.is_active = True
        db.session.commit()
        return jsonify({'status': 'success', 'message': 'Term activated'}), 200
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error setting active term: {str(e)}")
        return jsonify({'status': 'error', 'message': 'Error setting active term'}), 500

@app.route('/submit-form', methods=['POST', 'OPTIONS'])
def submit_form():
    if request.method == "OPTIONS":
        return '', 200
    
    try:
        data = request.get_json()
        if not data:
            return jsonify({'status': 'error', 'message': 'No data provided'}), 400
        
        email = data.get('email', '').strip().lower()
        name = data.get('name', '').strip()
        phone = data.get('phone', '').strip()
        year = data.get('year', '').strip()
        
        if not email or not email.endswith('@stmarks.nsw.edu.au'):
            return jsonify({'status': 'error', 'message': 'Invalid school email address'}), 400
        
        if not name or len(name) < 2:
            return jsonify({'status': 'error', 'message': 'Name must be at least 2 characters'}), 400
        
        if not phone or len(phone) != 10 or not phone.isdigit() or phone[0] != '0':
            return jsonify({'status': 'error', 'message': 'Phone must be 10 digits starting with 0'}), 400
        
        if not year or year not in ['7', '8', '9', '10']:
            return jsonify({'status': 'error', 'message': 'Invalid year level'}), 400
        
        current_term = Term.query.filter_by(is_active=True).first()
        if not current_term:
            return jsonify({'status': 'error', 'message': 'No active term'}), 400
        
        existing = Student.query.filter_by(email=email, term_id=current_term.id).first()
        if existing:
            return jsonify({'status': 'error', 'message': 'Already registered this term'}), 400
        
        new_student = Student(email=email, name=name, phone=phone, year=year, term_id=current_term.id)
        db.session.add(new_student)
        db.session.commit()
        return jsonify({'status': 'success', 'message': 'Contact info saved', 'student_id': new_student.id}), 200
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error submitting form: {str(e)}")
        return jsonify({'status': 'error', 'message': 'Error saving data'}), 500

@app.route('/get-sports', methods=['GET'])
def get_sports():
    try:
        term_id = request.args.get('term_id')
        if not term_id:
            current_term = Term.query.filter_by(is_active=True).first()
            term_id = current_term.id if current_term else None
        
        if not term_id:
            return jsonify({'status': 'error', 'message': 'No term specified'}), 400
        
        sports = Sport.query.filter_by(term_id=term_id).all()
        sports_list = [{
            'id': s.id,
            'name': s.name,
            'description': s.description or '',
            'capacity': s.capacity,
            'current_count': s.current_count,
            'is_open': s.is_open
        } for s in sports]
        return jsonify({'sports': sports_list}), 200
    except Exception as e:
        logger.error(f"Error fetching sports: {str(e)}")
        return jsonify({'status': 'error', 'message': 'Error fetching sports'}), 500

@app.route('/submit-sport', methods=['POST', 'OPTIONS'])
def submit_sport():
    if request.method == "OPTIONS":
        return '', 200
    
    try:
        data = request.get_json()
        if not data:
            return jsonify({'status': 'error', 'message': 'No data provided'}), 400
        
        student_id = data.get('student_id')
        sport_id = data.get('sport_id')
        
        if not student_id or not sport_id:
            return jsonify({'status': 'error', 'message': 'Student and sport required'}), 400
        
        student = Student.query.get(student_id)
        if not student:
            return jsonify({'status': 'error', 'message': 'Student not found'}), 404
        
        sport = Sport.query.get(sport_id)
        if not sport:
            return jsonify({'status': 'error', 'message': 'Sport not found'}), 404
        
        if sport.current_count >= sport.capacity:
            return jsonify({'status': 'error', 'message': 'Sport is now full'}), 400
        
        if not sport.is_open:
            return jsonify({'status': 'error', 'message': 'Sport is closed'}), 400
        
        existing = StudentSport.query.filter_by(student_id=student_id, sport_id=sport_id).first()
        if existing:
            return jsonify({'status': 'error', 'message': 'Already registered for this sport'}), 400
        
        sport_selection = StudentSport(student_id=student_id, sport_id=sport_id)
        sport.current_count += 1
        db.session.add(sport_selection)
        
        waitlist_entry = Waitlist.query.filter_by(student_id=student_id).first()
        if waitlist_entry:
            waitlist_entry.has_sport = True
        
        db.session.commit()
        return jsonify({'status': 'success', 'message': 'Sport submitted'}), 200
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error submitting sport: {str(e)}")
        return jsonify({'status': 'error', 'message': 'Error submitting sport'}), 500

@app.route('/get-all-data', methods=['GET'])
def get_all_data():
    try:
        term_id = request.args.get('term_id')
        if not term_id:
            current_term = Term.query.filter_by(is_active=True).first()
            term_id = current_term.id if current_term else None
        
        if not term_id:
            return jsonify({'status': 'error', 'message': 'No term specified'}), 400
        
        students = Student.query.filter_by(term_id=term_id).all()
        student_list = [{'id': s.id, 'email': s.email, 'name': s.name, 'phone': s.phone, 'year': s.year} for s in students]
        return jsonify({'students': student_list}), 200
    except Exception as e:
        logger.error(f"Error fetching all data: {str(e)}")
        return jsonify({'status': 'error', 'message': 'Error fetching data'}), 500

@app.route('/get-sport-registrations/<int:sport_id>', methods=['GET'])
def get_sport_registrations(sport_id):
    try:
        sport = Sport.query.get(sport_id)
        if not sport:
            return jsonify({'status': 'error', 'message': 'Sport not found'}), 404
        
        registrations = db.session.query(Student, StudentSport).join(StudentSport).filter(StudentSport.sport_id == sport_id).all()
        student_list = [{'id': s.id, 'name': s.name, 'email': s.email, 'year': s.year} for s, _ in registrations]
        return jsonify({'students': student_list}), 200
    except Exception as e:
        logger.error(f"Error fetching sport registrations: {str(e)}")
        return jsonify({'status': 'error', 'message': 'Error fetching registrations'}), 500

@app.route('/delete-student/<int:student_id>', methods=['DELETE'])
def delete_student(student_id):
    try:
        student = Student.query.get(student_id)
        if not student:
            return jsonify({'status': 'error', 'message': 'Student not found'}), 404
        
        selections = StudentSport.query.filter_by(student_id=student_id).all()
        for selection in selections:
            sport = Sport.query.get(selection.sport_id)
            if sport:
                sport.current_count = max(0, sport.current_count - 1)
        
        StudentSport.query.filter_by(student_id=student_id).delete()
        Waitlist.query.filter_by(student_id=student_id).delete()
        db.session.delete(student)
        db.session.commit()
        return jsonify({'status': 'success', 'message': 'Student deleted'}), 200
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error deleting student: {str(e)}")
        return jsonify({'status': 'error', 'message': 'Error deleting student'}), 500

@app.route('/delete-all-students', methods=['DELETE'])
def delete_all_students():
    try:
        term_id = request.args.get('term_id')
        if not term_id:
            return jsonify({'status': 'error', 'message': 'Term required'}), 400
        
        StudentSport.query.delete()
        Waitlist.query.delete()
        students = Student.query.filter_by(term_id=term_id).all()
        for student in students:
            db.session.delete(student)
        for sport in Sport.query.filter_by(term_id=term_id).all():
            sport.current_count = 0
        db.session.commit()
        return jsonify({'status': 'success', 'message': 'All students deleted'}), 200
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error deleting all students: {str(e)}")
        return jsonify({'status': 'error', 'message': 'Error deleting students'}), 500

@app.route('/add-sport', methods=['POST', 'OPTIONS'])
def add_sport():
    if request.method == "OPTIONS":
        return '', 200
    
    try:
        data = request.get_json()
        if not data:
            return jsonify({'status': 'error', 'message': 'No data provided'}), 400
        
        sport_name = data.get('name', '').strip()
        description = data.get('description', '').strip()
        capacity = data.get('capacity', 20)
        term_id = data.get('term_id')
        
        if not sport_name or not term_id:
            return jsonify({'status': 'error', 'message': 'Sport name and term required'}), 400
        
        try:
            capacity = int(capacity)
            if capacity < 1:
                return jsonify({'status': 'error', 'message': 'Capacity must be at least 1'}), 400
        except ValueError:
            return jsonify({'status': 'error', 'message': 'Capacity must be a number'}), 400
        
        new_sport = Sport(name=sport_name, description=description, capacity=capacity, is_open=True, term_id=term_id)
        db.session.add(new_sport)
        db.session.commit()
        return jsonify({'status': 'success', 'message': 'Sport added', 'sport_id': new_sport.id}), 200
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error adding sport: {str(e)}")
        return jsonify({'status': 'error', 'message': 'Error adding sport'}), 500

@app.route('/update-sport/<int:sport_id>', methods=['PUT', 'OPTIONS'])
def update_sport(sport_id):
    if request.method == "OPTIONS":
        return '', 200
    
    try:
        data = request.get_json()
        if not data:
            return jsonify({'status': 'error', 'message': 'No data provided'}), 400
        
        sport = Sport.query.get(sport_id)
        if not sport:
            return jsonify({'status': 'error', 'message': 'Sport not found'}), 404
        
        if 'capacity' in data:
            try:
                capacity = int(data.get('capacity'))
                if capacity < sport.current_count:
                    return jsonify({'status': 'error', 'message': 'Capacity cannot be less than current registrations'}), 400
                sport.capacity = capacity
            except ValueError:
                return jsonify({'status': 'error', 'message': 'Capacity must be a number'}), 400
        
        if 'name' in data:
            sport.name = data.get('name', '').strip()
        
        if 'description' in data:
            sport.description = data.get('description', '').strip()
        
        if 'is_open' in data:
            sport.is_open = data.get('is_open')
        
        db.session.commit()
        return jsonify({'status': 'success', 'message': 'Sport updated'}), 200
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error updating sport: {str(e)}")
        return jsonify({'status': 'error', 'message': 'Error updating sport'}), 500

@app.route('/delete-sport/<int:sport_id>', methods=['DELETE'])
def delete_sport(sport_id):
    try:
        sport = Sport.query.get(sport_id)
        if not sport:
            return jsonify({'status': 'error', 'message': 'Sport not found'}), 404
        
        StudentSport.query.filter_by(sport_id=sport_id).delete()
        db.session.delete(sport)
        db.session.commit()
        return jsonify({'status': 'success', 'message': 'Sport deleted'}), 200
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error deleting sport: {str(e)}")
        return jsonify({'status': 'error', 'message': 'Error deleting sport'}), 500

@app.route('/get-system-status', methods=['GET'])
def get_system_status():
    try:
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
            except ValueError:
                logger.warning(f"Invalid datetime format: {status.open_datetime}")
        
        return jsonify({'is_open': status.is_open, 'open_datetime': status.open_datetime}), 200
    except Exception as e:
        logger.error(f"Error fetching system status: {str(e)}")
        return jsonify({'status': 'error', 'message': 'Error fetching status'}), 500

@app.route('/set-system-status', methods=['POST', 'OPTIONS'])
def set_system_status():
    if request.method == "OPTIONS":
        return '', 200
    
    try:
        current_term = Term.query.filter_by(is_active=True).first()
        if not current_term:
            return jsonify({'status': 'error', 'message': 'No active term'}), 400
        
        data = request.get_json()
        if not data:
            return jsonify({'status': 'error', 'message': 'No data provided'}), 400
        
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
        return jsonify({'status': 'success', 'message': 'System status updated'}), 200
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error setting system status: {str(e)}")
        return jsonify({'status': 'error', 'message': 'Error setting status'}), 500

@app.route('/generate-delete-code', methods=['GET'])
def generate_delete_code():
    try:
        code = secrets.token_hex(4).upper()
        return jsonify({'code': code}), 200
    except Exception as e:
        logger.error(f"Error generating delete code: {str(e)}")
        return jsonify({'status': 'error', 'message': 'Error generating code'}), 500

@app.route('/get-waitlist', methods=['GET'])
def get_waitlist():
    try:
        term_id = request.args.get('term_id')
        if not term_id:
            current_term = Term.query.filter_by(is_active=True).first()
            term_id = current_term.id if current_term else None
        
        if not term_id:
            return jsonify({'status': 'error', 'message': 'No term specified'}), 400
        
        waitlisted = db.session.query(Student, Waitlist).join(Waitlist).filter(
            Student.term_id == term_id,
            Waitlist.has_sport == False
        ).all()
        waitlist_data = [{'id': s.id, 'email': s.email, 'name': s.name, 'phone': s.phone, 'year': s.year} for s, w in waitlisted]
        return jsonify({'waitlist': waitlist_data}), 200
    except Exception as e:
        logger.error(f"Error fetching waitlist: {str(e)}")
        return jsonify({'status': 'error', 'message': 'Error fetching waitlist'}), 500

@app.route('/add-to-waitlist/<int:student_id>', methods=['POST', 'OPTIONS'])
def add_to_waitlist(student_id):
    if request.method == "OPTIONS":
        return '', 200
    
    try:
        student = Student.query.get(student_id)
        if not student:
            return jsonify({'status': 'error', 'message': 'Student not found'}), 404
        
        if not Waitlist.query.filter_by(student_id=student_id).first():
            waitlist_entry = Waitlist(student_id=student_id)
            db.session.add(waitlist_entry)
            db.session.commit()
        return jsonify({'status': 'success', 'message': 'Added to waitlist'}), 200
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error adding to waitlist: {str(e)}")
        return jsonify({'status': 'error', 'message': 'Error adding to waitlist'}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
     
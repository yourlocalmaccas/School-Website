from flask import Flask 
from flask_cors import CORS

app = Flask(__name__)
CORS(app)
saved_emails = []

@app.route('/verify_email', methods=['POST', 'OPTIONS'])
def verify_email():
    if request.method == "OPTIONS":
        return '', 200
    data = request.get_json()
    email = data.get('email', '').strip()
    print(f"Received email: {email}")
    if not email:
        return jsonify({'status': 'error', 'message': 'Email cannot be empty.'}), 400
    if email in saved_emails:
        return jsonify({'status': 'exists', 'message': 'Email already saved.'}), 400
    saved_emails.append(email)
    print(f"Saved emails: {saved_emails}")
    return jsonify({'status': 'success', 'message': f'Email {email} verified and saved!'}), 200



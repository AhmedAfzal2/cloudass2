from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv
import os
import requests
from google.cloud.sql.connector import Connector

load_dotenv()

CONN_NAME = os.getenv('CLOUD_SQL_CONNECTION_NAME')
DB_USER = os.getenv('DB_USER')
DB_PASS = os.getenv('DB_PASS')
DB_NAME = 'enrollments'

connector = Connector()

def connect_with_connector():
    return connector.connect(
        CONN_NAME,
        "pg8000",
        user=DB_USER,
        password=DB_PASS,
        db=DB_NAME,
    )

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = "postgresql+pg8000://"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'creator': connect_with_connector
}

db = SQLAlchemy(app)

class Enrollment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, nullable=False)
    course_id = db.Column(db.Integer, nullable=False)

    def to_dict(self):
        return {'id': self.id, 'student_id': self.student_id, 'course_id': self.course_id}

STUDENT_SERVICE_URL = os.getenv('STUDENT_SERVICE_URL')
COURSE_SERVICE_URL = os.getenv('COURSE_SERVICE_URL')

@app.route('/health')
def health():
    return jsonify({'status': 'ok'})

def verify_student(student_id):
    if not STUDENT_SERVICE_URL:
        return True
    try:
        r = requests.get(f"{STUDENT_SERVICE_URL}/students/{student_id}", timeout=3)
        return r.status_code == 200
    except Exception:
        return False

def verify_course(course_id):
    if not COURSE_SERVICE_URL:
        return True
    try:
        r = requests.get(f"{COURSE_SERVICE_URL}/courses/{course_id}", timeout=3)
        return r.status_code == 200
    except Exception:
        return False

@app.route('/enrollments', methods=['POST'])
def create_enrollment():
    data = request.get_json() or {}
    if not data.get('student_id') or not data.get('course_id'):
        return jsonify({'error': 'student_id and course_id required'}), 400
    sid = int(data['student_id'])
    cid = int(data['course_id'])
    if not verify_student(sid):
        return jsonify({'error': 'student not found or verification service unavailable'}), 400
    if not verify_course(cid):
        return jsonify({'error': 'course not found or verification service unavailable'}), 400
    e = Enrollment(student_id=sid, course_id=cid)
    db.session.add(e)
    db.session.commit()
    return jsonify(e.to_dict()), 201

@app.route('/enrollments', methods=['GET'])
def list_enrollments():
    enrolls = Enrollment.query.all()
    return jsonify([e.to_dict() for e in enrolls])

@app.route('/enrollments/student/<int:student_id>', methods=['GET'])
def enrollments_for_student(student_id):
    enrolls = Enrollment.query.filter_by(student_id=student_id).all()
    return jsonify([e.to_dict() for e in enrolls])

@app.route('/enrollments/<int:enrollment_id>', methods=['GET'])
def get_enrollment(enrollment_id):
    e = db.get_or_404(Enrollment, enrollment_id)
    return jsonify(e.to_dict())

@app.route('/enrollments/<int:enrollment_id>', methods=['PUT'])
def update_enrollment(enrollment_id):
    e = db.get_or_404(Enrollment, enrollment_id)
    data = request.get_json() or {}
    
    if 'student_id' in data:
        sid = int(data['student_id'])
        if not verify_student(sid):
             return jsonify({'error': 'student not found'}), 400
        e.student_id = sid
        
    if 'course_id' in data:
        cid = int(data['course_id'])
        if not verify_course(cid):
             return jsonify({'error': 'course not found'}), 400
        e.course_id = cid
        
    db.session.commit()
    return jsonify(e.to_dict())

@app.route('/enrollments/<int:enrollment_id>', methods=['DELETE'])
def delete_enrollment(enrollment_id):
    e = db.get_or_404(Enrollment, enrollment_id)
    db.session.delete(e)
    db.session.commit()
    return jsonify({'message': 'enrollment deleted'}), 200

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', 8082)))

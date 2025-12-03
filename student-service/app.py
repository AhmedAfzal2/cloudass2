from flask import Flask, request, jsonify, abort
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv
import os
from google.cloud.sql.connector import Connector

load_dotenv()

CONN_NAME = os.getenv('CLOUD_SQL_CONNECTION_NAME')
DB_USER = os.getenv('DB_USER')
DB_PASS = os.getenv('DB_PASS')
DB_NAME = 'students'
    
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

class Student(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False)
    email = db.Column(db.String(128), unique=True, nullable=False)

    def to_dict(self):
        return {'id': self.id, 'name': self.name, 'email': self.email}

@app.route('/health')
def health():
    return jsonify({'status': 'ok'})

@app.route('/students', methods=['POST'])
def create_student():
    data = request.get_json() or {}
    if not data.get('name') or not data.get('email'):
        return jsonify({'error': 'name and email required'}), 400
    if Student.query.filter_by(email=data['email']).first():
        return jsonify({'error': 'email already exists'}), 400
    s = Student(name=data['name'], email=data['email'])
    db.session.add(s)
    db.session.commit()
    return jsonify(s.to_dict()), 201

@app.route('/students', methods=['GET'])
def list_students():
    students = Student.query.all()
    return jsonify([s.to_dict() for s in students])

@app.route('/students/<int:student_id>', methods=['GET'])
def get_student(student_id):
    s = db.get_or_404(Student, student_id)
    return jsonify(s.to_dict())

@app.route('/students/<int:student_id>', methods=['PUT'])
def update_student(student_id):
    s = db.get_or_404(Student, student_id)
    data = request.get_json() or {}
    
    if 'name' in data:
        s.name = data['name']
    if 'email' in data:
        if data['email'] != s.email and Student.query.filter_by(email=data['email']).first():
             return jsonify({'error': 'email already exists'}), 400
        s.email = data['email']
        
    db.session.commit()
    return jsonify(s.to_dict())

@app.route('/students/<int:student_id>', methods=['DELETE'])
def delete_student(student_id):
    s = db.get_or_404(Student, student_id)
    db.session.delete(s)
    db.session.commit()
    return jsonify({'message': 'student deleted'}), 200

if __name__ == '__main__':
    # ensure DB exists for local dev
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', 8080)))

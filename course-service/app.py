from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv
import os
from google.cloud.sql.connector import Connector 

load_dotenv()

CONN_NAME = os.getenv('CLOUD_SQL_CONNECTION_NAME')
DB_USER = os.getenv('DB_USER')
DB_PASS = os.getenv('DB_PASS')
DB_NAME = 'courses'

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
# 👇 FIX: Changed from +psycopg2 to +pg8000
app.config['SQLALCHEMY_DATABASE_URI'] = "postgresql+pg8000://" 
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'creator': connect_with_connector
}

db = SQLAlchemy(app)

class Course(db.Model):

    id = db.Column(db.Integer, primary_key=True)

    title = db.Column(db.String(200), nullable=False)

    description = db.Column(db.Text, nullable=True)


    def to_dict(self):

        return {'id': self.id, 'title': self.title, 'description': self.description}


@app.route('/health')

def health():

    return jsonify({'status': 'ok'})


@app.route('/courses', methods=['POST'])

def create_course():

    data = request.get_json() or {}

    if not data.get('title'):

        return jsonify({'error': 'title required'}), 400

    c = Course(title=data['title'], description=data.get('description'))

    db.session.add(c)

    db.session.commit()

    return jsonify(c.to_dict()), 201


@app.route('/courses', methods=['GET'])

def list_courses():

    courses = Course.query.all()

    return jsonify([c.to_dict() for c in courses])


@app.route('/courses/<int:course_id>', methods=['GET'])

def get_course(course_id):

    c = db.get_or_404(Course, course_id)

    return jsonify(c.to_dict())


@app.route('/courses/<int:course_id>', methods=['PUT'])

def update_course(course_id):

    c = db.get_or_404(Course, course_id)

    data = request.get_json() or {}

   

    if 'title' in data:

        c.title = data['title']

    if 'description' in data:

        c.description = data['description']

       

    db.session.commit()

    return jsonify(c.to_dict())


@app.route('/courses/<int:course_id>', methods=['DELETE'])

def delete_course(course_id):

    c = db.get_or_404(Course, course_id)

    db.session.delete(c)

    db.session.commit()

    return jsonify({'message': 'course deleted'}), 200

if __name__ == '__main__':
    with app.app_context():
        # This will now use the pg8000 driver via the Connector
        db.create_all() 
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', 8081)))
import os
import requests
from flask import Flask, render_template, request, redirect, url_for, flash

app = Flask(__name__)
app.secret_key = 'secret'

# Configuration
STUDENT_SERVICE_URL = os.environ.get('STUDENT_SERVICE_URL', 'http://localhost:8080')
COURSE_SERVICE_URL = os.environ.get('COURSE_SERVICE_URL', 'http://localhost:8081')
ENROLLMENT_SERVICE_URL = os.environ.get('ENROLLMENT_SERVICE_URL', 'http://localhost:8082')

@app.route('/')
def index():
    return render_template('index.html')

# --- Student Routes ---
@app.route('/students')
def list_students():
    try:
        response = requests.get(f"{STUDENT_SERVICE_URL}/students")
        students = response.json() if response.status_code == 200 else []
    except requests.exceptions.RequestException as e:
        flash(f"Error connecting to Student Service: {e}", "danger")
        students = []
    return render_template('students.html', students=students)

@app.route('/students/add', methods=['POST'])
def add_student():
    name = request.form.get('name')
    email = request.form.get('email')
    try:
        requests.post(f"{STUDENT_SERVICE_URL}/students", json={'name': name, 'email': email})
        flash("Student added successfully", "success")
    except requests.exceptions.RequestException as e:
        flash(f"Error adding student: {e}", "danger")
    return redirect(url_for('list_students'))

@app.route('/students/delete/<int:id>')
def delete_student(id):
    try:
        requests.delete(f"{STUDENT_SERVICE_URL}/students/{id}")
        flash("Student deleted successfully", "success")
    except requests.exceptions.RequestException as e:
        flash(f"Error deleting student: {e}", "danger")
    return redirect(url_for('list_students'))

@app.route('/students/edit/<int:id>', methods=['GET', 'POST'])
def edit_student(id):
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        try:
            requests.put(f"{STUDENT_SERVICE_URL}/students/{id}", json={'name': name, 'email': email})
            flash("Student updated successfully", "success")
            return redirect(url_for('list_students'))
        except requests.exceptions.RequestException as e:
            flash(f"Error updating student: {e}", "danger")
    
    # GET request - fetch student details
    try:
        response = requests.get(f"{STUDENT_SERVICE_URL}/students/{id}")
        if response.status_code == 200:
            student = response.json()
            return render_template('edit_student.html', student=student)
        else:
            flash("Student not found", "danger")
            return redirect(url_for('list_students'))
    except requests.exceptions.RequestException as e:
        flash(f"Error fetching student details: {e}", "danger")
        return redirect(url_for('list_students'))

# --- Course Routes ---
@app.route('/courses')
def list_courses():
    try:
        response = requests.get(f"{COURSE_SERVICE_URL}/courses")
        courses = response.json() if response.status_code == 200 else []
    except requests.exceptions.RequestException as e:
        flash(f"Error connecting to Course Service: {e}", "danger")
        courses = []
    return render_template('courses.html', courses=courses)

@app.route('/courses/add', methods=['POST'])
def add_course():
    title = request.form.get('title')
    description = request.form.get('description')
    try:
        requests.post(f"{COURSE_SERVICE_URL}/courses", json={'title': title, 'description': description})
        flash("Course added successfully", "success")
    except requests.exceptions.RequestException as e:
        flash(f"Error adding course: {e}", "danger")
    return redirect(url_for('list_courses'))

@app.route('/courses/delete/<int:id>')
def delete_course(id):
    try:
        requests.delete(f"{COURSE_SERVICE_URL}/courses/{id}")
        flash("Course deleted successfully", "success")
    except requests.exceptions.RequestException as e:
        flash(f"Error deleting course: {e}", "danger")
    return redirect(url_for('list_courses'))

@app.route('/courses/edit/<int:id>', methods=['GET', 'POST'])
def edit_course(id):
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        try:
            requests.put(f"{COURSE_SERVICE_URL}/courses/{id}", json={'title': title, 'description': description})
            flash("Course updated successfully", "success")
            return redirect(url_for('list_courses'))
        except requests.exceptions.RequestException as e:
            flash(f"Error updating course: {e}", "danger")
    
    # GET request - fetch course details
    try:
        response = requests.get(f"{COURSE_SERVICE_URL}/courses/{id}")
        if response.status_code == 200:
            course = response.json()
            return render_template('edit_course.html', course=course)
        else:
            flash("Course not found", "danger")
            return redirect(url_for('list_courses'))
    except requests.exceptions.RequestException as e:
        flash(f"Error fetching course details: {e}", "danger")
        return redirect(url_for('list_courses'))

# --- Enrollment Routes ---
@app.route('/enrollments')
def list_enrollments():
    enrollments = []
    students = []
    courses = []
    
    try:
        # Fetch enrollments
        resp_enroll = requests.get(f"{ENROLLMENT_SERVICE_URL}/enrollments")
        enrollments = resp_enroll.json() if resp_enroll.status_code == 200 else []
        
        # Fetch students and courses for dropdowns and name resolution
        resp_stud = requests.get(f"{STUDENT_SERVICE_URL}/students")
        students = resp_stud.json() if resp_stud.status_code == 200 else []
        
        resp_course = requests.get(f"{COURSE_SERVICE_URL}/courses")
        courses = resp_course.json() if resp_course.status_code == 200 else []
        
        # Map IDs to names for display
        student_map = {s['id']: s['name'] for s in students}
        course_map = {c['id']: c['title'] for c in courses}
        
        for e in enrollments:
            e['student_name'] = student_map.get(e['student_id'], 'Unknown')
            e['course_name'] = course_map.get(e['course_id'], 'Unknown')
            
    except requests.exceptions.RequestException as e:
        flash(f"Error connecting to services: {e}", "danger")
        
    return render_template('enrollments.html', enrollments=enrollments, students=students, courses=courses)

@app.route('/enrollments/add', methods=['POST'])
def add_enrollment():
    student_id = request.form.get('student_id')
    course_id = request.form.get('course_id')
    try:
        requests.post(f"{ENROLLMENT_SERVICE_URL}/enrollments", json={'student_id': int(student_id), 'course_id': int(course_id)})
        flash("Enrollment added successfully", "success")
    except requests.exceptions.RequestException as e:
        flash(f"Error adding enrollment: {e}", "danger")
    return redirect(url_for('list_enrollments'))

@app.route('/enrollments/delete/<int:id>')
def delete_enrollment(id):
    try:
        requests.delete(f"{ENROLLMENT_SERVICE_URL}/enrollments/{id}")
        flash("Enrollment deleted successfully", "success")
    except requests.exceptions.RequestException as e:
        flash(f"Error deleting enrollment: {e}", "danger")
    return redirect(url_for('list_enrollments'))

@app.route('/enrollments/edit/<int:id>', methods=['GET', 'POST'])
def edit_enrollment(id):
    if request.method == 'POST':
        student_id = request.form.get('student_id')
        course_id = request.form.get('course_id')
        try:
            requests.put(f"{ENROLLMENT_SERVICE_URL}/enrollments/{id}", json={'student_id': int(student_id), 'course_id': int(course_id)})
            flash("Enrollment updated successfully", "success")
            return redirect(url_for('list_enrollments'))
        except requests.exceptions.RequestException as e:
            flash(f"Error updating enrollment: {e}", "danger")
    
    # GET request
    try:
        # Fetch enrollment
        resp_enroll = requests.get(f"{ENROLLMENT_SERVICE_URL}/enrollments/{id}")
        print(resp_enroll)
        if resp_enroll.status_code != 200:
            flash("Enrollment not found", "danger")
            return redirect(url_for('list_enrollments'))
        enrollment = resp_enroll.json()

        # Fetch students and courses for dropdowns
        resp_stud = requests.get(f"{STUDENT_SERVICE_URL}/students")
        students = resp_stud.json() if resp_stud.status_code == 200 else []
        
        resp_course = requests.get(f"{COURSE_SERVICE_URL}/courses")
        courses = resp_course.json() if resp_course.status_code == 200 else []

        return render_template('edit_enrollment.html', enrollment=enrollment, students=students, courses=courses)

    except requests.exceptions.RequestException as e:
        flash(f"Error fetching details: {e}", "danger")
        return redirect(url_for('list_enrollments'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8083, debug=True)

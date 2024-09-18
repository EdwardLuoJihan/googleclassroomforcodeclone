from flask import render_template, url_for, flash, redirect, request
from app import app, db, bcrypt
from models import User, Assignment, Submission, Class
from forms import RegistrationForm, LoginForm
from forms import AssignmentSubmissionForm, ClassCreationForm, AssignmentForm
from werkzeug.utils import secure_filename
import os
from flask_login import login_user, logout_user, current_user, login_required
from flask_bcrypt import Bcrypt
from flask import current_app
from flask import send_from_directory, abort

bcrypt = Bcrypt(app)

UPLOAD_FOLDER = './assignments/submissions/'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

@app.route("/reset")
def reset():
    try:
        # db.session.query(Assignment).delete()
        # db.session.commit()
        # # Delete all records from the users table
        # User.query.delete()
        # db.session.commit()
        # print("All users have been deleted.")
        # # Create the admin user
        admin = User(
            username='teacher',
            email='teacher@admin.com',
            role='teacher'
        )
        admin.set_password('teacher')
        # testuser = User(
        #     username='test',
        #     email='test@test.com',
        #     role='student'
        # )
        # testuser.set_password('test')

        db.session.add(admin)
        # db.session.add(testuser)
        db.session.commit()
        print("DONE")
    except:
        pass
    return redirect(url_for('index'))

@app.route("/")
@app.route("/index")
def index():
    return render_template('index.html')

@app.route("/register", methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    form = RegistrationForm()

    print(form.errors)

    if form.is_submitted():
        print("submitted")

    if form.validate():
        print("valid")

    print(form.errors)
    if form.validate_on_submit():
        print("SUBMITTED")
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user = User(username=form.username.data, email=form.email.data, password_hash=hashed_password, role='student')
        db.session.add(user)
        db.session.commit()

        # Handle class code if provided
        class_code = form.class_code.data
        if class_code:
            class_ = Class.query.filter_by(class_code=class_code).first()
            if class_:
                user.classes.append(class_)
                db.session.commit()
                flash(f'Joined class {class_.class_code} successfully!', 'success')
            else:
                flash('Invalid class code.', 'danger')

        flash('Your account has been created! You can now log in.', 'success')
        return redirect(url_for('login'))

    return render_template('register.html', form=form)

@app.route("/login", methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        print(user.username + "logged in")
        if user and bcrypt.check_password_hash(user.password_hash, form.password.data):
            login_user(user)
            return redirect(url_for('index'))
        else:
            flash('Login unsuccessful. Please check email and password.', 'danger')
    return render_template('login.html', form=form)

@app.route("/submit_assignment/<int:assignment_id>", methods=['GET', 'POST'])
@login_required
def submit_assignment(assignment_id):
    form = AssignmentSubmissionForm()
    assignment = Assignment.query.get_or_404(assignment_id)

    if form.validate_on_submit():
        # Save files securely
        html_file = save_file(form.html_file.data, 'html', current_user.id, assignment_id)
        css_file = save_file(form.css_file.data, 'css', current_user.id, assignment_id)
        js_file = save_file(form.js_file.data, 'js', current_user.id, assignment_id)

        # Create a new submission entry in the database
        submission = Submission(html_file=html_file, css_file=css_file, js_file=js_file, student_id=current_user.id, assignment_id=assignment.id)
        db.session.add(submission)
        db.session.commit()

        flash('Assignment submitted successfully!', 'success')
        return redirect(url_for('student_dashboard'))
    
    return render_template('assignment_detail.html', form=form, assignment=assignment)

def save_file(file, ext, student_id, assignment_id):
    filename = secure_filename(f"student_{student_id}_assignment_{assignment_id}.{ext}")
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(file_path)
    return file_path

@app.route("/view_submission/<int:submission_id>", methods=['GET', 'POST'])
@login_required
def view_submission(submission_id):
    submission = Submission.query.get_or_404(submission_id)

    # Ensure only the teacher can access this route
    if current_user.role != 'teacher':
        flash('Access denied.', 'danger')
        return redirect(url_for('index'))

    # Read the submitted files
    html_content = read_file(submission.html_file)
    css_content = read_file(submission.css_file)
    js_content = read_file(submission.js_file)


    if request.method == 'POST':
        # Teacher submitted a grade
        submission.grade = request.form['grade']
        submission.feedback = request.form['feedback']
        db.session.commit()
        flash('Grade submitted successfully!', 'success')

    return render_template('submission_view.html', submission=submission, html_content=html_content, css_content=css_content, js_content=js_content)

@app.route("/student_dashboard")
@login_required
def student_dashboard():
    if current_user.role != 'student':
        flash('Access denied.', 'danger')
        return redirect(url_for('index'))

    classes = current_user.classes
    return render_template('student_dashboard.html', classes=classes)

def read_file(file_path):
    with open(file_path, 'r') as f:
        return f.read()
    
@app.route("/create_class", methods=['GET', 'POST'])
@login_required
def create_class():
    if current_user.role != 'teacher':
        flash('Access denied.', 'danger')
        return redirect(url_for('index'))

    form = ClassCreationForm()
    if form.validate_on_submit():
        class_code = form.class_code.data
        new_class = Class(class_code=class_code, teacher_id=current_user.id)
        db.session.add(new_class)
        db.session.commit()
        flash('Class created successfully!', 'success')
        return redirect(url_for('teacher_dashboard'))

    return render_template('create_class.html', form=form)

@app.route('/create_assignment/<int:class_id>', methods=['GET', 'POST'])
@login_required
def create_assignment(class_id):
    
    # Fetch the class to which the assignment is being created
    class_ = Class.query.get_or_404(class_id)
    
    # Ensure the class belongs to the current user
    if current_user.role != 'teacher':
        flash('Access denied.', 'danger')
        return redirect(url_for('index'))
    
    form = AssignmentForm()
    
    if form.validate_on_submit():
        # Create a new assignment
        assignment = Assignment(
            title=form.name.data,
            description=form.description.data,
            class_id=class_id,
            deadline=form.due_date.data
        )
        
        db.session.add(assignment)
        db.session.commit()
        
        flash('Assignment created successfully!', 'success')
        return redirect(url_for('teacher_dashboard'))
    
    return render_template('create_assignment.html', form=form, class_=class_)

@app.route("/join_class", methods=['GET', 'POST'])
@login_required
def join_class():
    if current_user.role != 'student':
        flash('Access denied.', 'danger')
        return redirect(url_for('index'))

    class_code = request.form.get('class_code')
    if request.method == 'POST' and class_code:
        class_ = Class.query.filter_by(class_code=class_code).first()
        if class_:
            current_user.classes.append(class_)
            db.session.commit()
            flash(f'Joined class {class_.class_code} successfully!', 'success')
        else:
            flash('Invalid class code.', 'danger')

    return render_template('join_class.html')

@app.route("/teacher_dashboard")
@login_required
def teacher_dashboard():
    if current_user.role != 'teacher':
        flash('Access denied.', 'danger')
        return redirect(url_for('index'))

    classes = Class.query.all()
    print(current_user.username)
    return render_template('teacher_dashboard.html', classes=classes)

@app.route('/view_assignments/<int:class_id>')
@login_required
def view_assignments(class_id):
    class_ = Class.query.get_or_404(class_id)
    assignments = Assignment.query.filter_by(class_id=class_id).all()

    # Check if there are no assignments
    if not assignments:
        flash('No assignments found for this class.', 'info')

    return render_template('view_assignments.html', assignments=assignments, class_=class_)

@app.before_request
def restrict_teacher_access():
    if current_user.is_authenticated and current_user.role != 'teacher':
        if request.endpoint in ['create_class', 'view_submissions']:
            flash('Access denied.', 'danger')
            return redirect(url_for('index'))
        
@app.before_request
def restrict_student_access():
    if current_user.is_authenticated and current_user.role != 'student':
        if request.endpoint in ['submit_assignment', 'join_class']:
            flash('Access denied.', 'danger')
            return redirect(url_for('index'))

def allowed_file(filename):
    allowed_extensions = {'html', 'css', 'js'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions

def save_file(file, ext, student_id, assignment_id):
    if not allowed_file(file.filename):
        flash('Invalid file type.', 'danger')
        return None
    filename = secure_filename(f"student_{student_id}_assignment_{assignment_id}.{ext}")
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(file_path)
    return file_path

@app.route("/grade_assignment/<int:submission_id>", methods=['GET', 'POST'])
@login_required
def grade_assignment(submission_id):
    if current_user.role != 'teacher':
        flash('Access denied.', 'danger')
        return redirect(url_for('index'))

    submission = Submission.query.get_or_404(submission_id)
    if request.method == 'POST':
        grade = request.form.get('grade')
        feedback = request.form.get('feedback')

        submission.grade = grade
        submission.feedback = feedback
        db.session.commit()

        flash('Assignment graded successfully!', 'success')
        return redirect(url_for('teacher_dashboard'))

    return render_template('grade_assignment.html', submission=submission)

@app.route("/view_grades")
@login_required
def view_grades():
    if current_user.role != 'student':
        flash('Access denied.', 'danger')
        return redirect(url_for('index'))

    page = request.args.get('page', 1, type=int)
    submissions = Submission.query.filter_by(student_id=current_user.id).paginate(page, per_page=5)
    return render_template('view_grades.html', submissions=submissions)

@app.route("/view_files/<int:submission_id>")
@login_required
def view_assignment_files(submission_id):
    submission = Submission.query.get_or_404(submission_id)
    return render_template('view_files.html', submission=submission)

@app.route('/users')
def users():
    users = User.query.all()  # Query all users from the database
    return render_template('users.html', users=users)

@app.route('/test')
def test():
    user = User.query.first()  # Get the first user
    return f"User: {user.username if user else 'No users found'}"

@app.route('/logout')
def logout():
    if current_user.is_authenticated:
        logout_user()
        flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

@app.route('/profile')
@login_required
def profile():
    # Render profile page with user info
    return render_template('profile.html', user=current_user)

@app.route('/view_submissions/<int:assignment_id>')
@login_required
def view_submissions(assignment_id):
    assignment = Assignment.query.get_or_404(assignment_id)
    submissions = Submission.query.filter_by(assignment_id=assignment_id).all()

    total_submissions = len(submissions)
    print(submissions)
    print(total_submissions)

    return render_template('view_submissions.html', assignment=assignment, submissions=submissions, total_submissions=total_submissions)

@app.route('/student/view_submission/<int:assignment_id>')
@login_required
def student_view_submission(assignment_id):
    if current_user.role != 'student':
        flash('Access denied.', 'danger')
        return redirect(url_for('index'))

    # Fetch student's submissions for this assignment
    assignment = Assignment.query.get_or_404(assignment_id)
    submissions = Submission.query.filter_by(student_id=current_user.id, assignment_id=assignment_id).all()

    # Check if there are submissions
    if not submissions:
        flash('No submissions found for this assignment.', 'info')
    
    return render_template('student_view_submission.html', submissions=submissions, assignment=assignment)

import os

@app.route('/download/<path:filename>')
@login_required
def download_file(filename):
    # Extract just the filename part, ignoring any preceding paths
    filename_only = os.path.basename(filename)

    # Print the extracted filename for debugging
    print("Extracted filename: ", filename_only)

    # Check if the file exists in the upload folder
    if os.path.exists(os.path.join(current_app.config['UPLOAD_FOLDER'], filename_only)):
        return send_from_directory(current_app.config['UPLOAD_FOLDER'], filename_only, as_attachment=True)
    else:
        abort(404)  # Return 404 if the file does not exist

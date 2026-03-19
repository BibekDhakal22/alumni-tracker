import csv
import io
from flask import Response
import os
from werkzeug.utils import secure_filename
from database import db, Student, Notice
from flask import Flask, render_template, redirect, url_for, request, flash
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from database import db, Student
from database import db, Student, Notice, Message

app = Flask(__name__)
app.config['SECRET_KEY'] = 'alumni_secret_key_2024'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///alumni.db'
app.config['UPLOAD_FOLDER']   = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 2 * 1024 * 1024  # 2MB max
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return Student.query.get(int(user_id))

# ---------- Routes ----------

@app.route('/')
def home():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        student_id = request.form.get('student_id')
        phone      = request.form.get('phone')
        user = Student.query.filter_by(student_id=student_id).first()
        if user and user.check_password(phone):
            login_user(user)
            return redirect(url_for('dashboard'))
        flash('Invalid Student ID or phone number.')
    return render_template('login.html')

@app.route('/dashboard')
@login_required
def dashboard():
    recent_notices = Notice.query.order_by(
        Notice.is_pinned.desc(),
        Notice.created_at.desc()
    ).limit(3).all()
    return render_template('dashboard.html', user=current_user, notices=recent_notices)

@app.route('/edit-profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    if request.method == 'POST':
        current_user.full_name   = request.form.get('full_name')
        current_user.email       = request.form.get('email')
        current_user.phone       = request.form.get('phone')
        current_user.job_title   = request.form.get('job_title')
        current_user.company     = request.form.get('company')
        current_user.job_sector  = request.form.get('job_sector')
        current_user.higher_edu  = request.form.get('higher_edu')
        current_user.institution = request.form.get('institution')
        current_user.address     = request.form.get('address')
        current_user.batch_year  = request.form.get('batch_year')
        db.session.commit()
        flash('Profile updated successfully!')
        return redirect(url_for('dashboard'))
    return render_template('edit_profile.html', user=current_user)

@app.route('/admin')
@login_required
def admin():
    if not current_user.is_admin:
        flash('Access denied.')
        return redirect(url_for('dashboard'))
    search = request.args.get('search', '')
    sector = request.args.get('sector', '')
    batch  = request.args.get('batch', '')
    query  = Student.query.filter_by(is_admin=False)
    if search:
        query = query.filter(
            Student.full_name.ilike(f'%{search}%') |
            Student.student_id.ilike(f'%{search}%')
        )
    if sector:
        query = query.filter_by(job_sector=sector)
    if batch:
        query = query.filter_by(batch_year=batch)
    students = query.all()
    batches  = [s.batch_year for s in Student.query.filter_by(is_admin=False).all() if s.batch_year]
    batches  = sorted(set(batches))
    sectors  = ['IT / Software', 'Banking / Finance', 'Education / Teaching',
                'Government / Civil Service', 'Healthcare',
                'Business / Entrepreneurship', 'Higher Studies (Not working)', 'Other']
    return render_template('admin.html', students=students,
                           search=search, sector=sector,
                           batch=batch, batches=batches, sectors=sectors)

@app.route('/admin/add-student', methods=['GET', 'POST'])
@login_required
def add_student():
    if not current_user.is_admin:
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        student_id = request.form.get('student_id')
        if Student.query.filter_by(student_id=student_id).first():
            flash('Student ID already exists!')
            return redirect(url_for('add_student'))
        phone = request.form.get('phone')
        s = Student(
            student_id  = student_id,
            full_name   = request.form.get('full_name'),
            email       = request.form.get('email'),
            phone       = phone,
            batch_year  = request.form.get('batch_year'),
            job_title   = request.form.get('job_title'),
            company     = request.form.get('company'),
            job_sector  = request.form.get('job_sector'),
            higher_edu  = request.form.get('higher_edu'),
            institution = request.form.get('institution'),
            address     = request.form.get('address'),
        )
        s.set_password(phone)
        db.session.add(s)
        db.session.commit()
        flash(f'Alumni "{s.full_name}" added successfully!')
        return redirect(url_for('admin'))
    return render_template('add_student.html')

@app.route('/admin/delete/<int:student_id>', methods=['POST'])
@login_required
def delete_student(student_id):
    if not current_user.is_admin:
        return redirect(url_for('dashboard'))
    s = Student.query.get_or_404(student_id)
    db.session.delete(s)
    db.session.commit()
    flash(f'Alumni "{s.full_name}" deleted.')
    return redirect(url_for('admin'))

@app.route('/analytics')
@login_required
def analytics():
    if not current_user.is_admin:
        return redirect(url_for('dashboard'))
    students = Student.query.filter_by(is_admin=False).all()

    # Sector data
    sector_counts = {}
    for s in students:
        sec = s.job_sector or 'Not updated'
        sector_counts[sec] = sector_counts.get(sec, 0) + 1

    # Batch data
    batch_counts = {}
    for s in students:
        b = s.batch_year or 'Unknown'
        batch_counts[b] = batch_counts.get(b, 0) + 1
    batch_counts = dict(sorted(batch_counts.items()))

    # Summary
    employed     = sum(1 for s in students if s.job_sector and s.job_sector != 'Higher Studies (Not working)')
    higher_edu   = sum(1 for s in students if s.higher_edu)
    not_updated  = sum(1 for s in students if not s.job_sector)

    return render_template('analytics.html',
        total        = len(students),
        employed     = employed,
        higher_edu   = higher_edu,
        not_updated  = not_updated,
        sector_labels= list(sector_counts.keys()),
        sector_data  = list(sector_counts.values()),
        batch_labels = list(batch_counts.keys()),
        batch_data   = list(batch_counts.values()),
    )

@app.route('/admin/export')
@login_required
def export_csv():
    if not current_user.is_admin:
        return redirect(url_for('dashboard'))
    students = Student.query.filter_by(is_admin=False).all()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([s.student_id, s.full_name, s.email or '',
                 f"'{s.phone}",
                 s.batch_year or '', s.job_title or '', s.company or '',
                 s.job_sector or '', s.higher_edu or '',
                 s.institution or '', s.address or ''])
    for s in students:
        writer.writerow([s.student_id, s.full_name, s.email or '', s.phone,
                         s.batch_year or '', s.job_title or '', s.company or '',
                         s.job_sector or '', s.higher_edu or '',
                         s.institution or '', s.address or ''])
    output.seek(0)
    return Response(output, mimetype='text/csv',
                    headers={'Content-Disposition': 'attachment;filename=alumni_list.csv'})

@app.route('/admin/view/<int:student_id>')
@login_required
def view_student(student_id):
    if not current_user.is_admin:
        return redirect(url_for('dashboard'))
    student = Student.query.get_or_404(student_id)
    return render_template('view_student.html', student=student)                    

@app.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    if request.method == 'POST':
        current_phone = request.form.get('current_password')
        new_phone     = request.form.get('new_password')
        confirm_phone = request.form.get('confirm_password')
        if not current_user.check_password(current_phone):
            flash('Current password is incorrect.')
            return redirect(url_for('change_password'))
        if new_phone != confirm_phone:
            flash('New passwords do not match.')
            return redirect(url_for('change_password'))
        if len(new_phone) < 10:
            flash('Password must be at least 10 digits.')
            return redirect(url_for('change_password'))
        current_user.set_password(new_phone)
        current_user.phone = new_phone
        db.session.commit()
        flash('Password changed successfully!')
        return redirect(url_for('dashboard'))
    return render_template('change_password.html')

@app.route('/directory')
@login_required
def directory():
    search = request.args.get('search', '')
    sector = request.args.get('sector', '')
    batch  = request.args.get('batch', '')
    query  = Student.query.filter_by(is_admin=False)
    if search:
        query = query.filter(Student.full_name.ilike(f'%{search}%'))
    if sector:
        query = query.filter_by(job_sector=sector)
    if batch:
        query = query.filter_by(batch_year=batch)
    students = query.all()
    batches  = sorted(set(s.batch_year for s in Student.query.filter_by(is_admin=False).all() if s.batch_year))
    sectors  = ['IT / Software', 'Banking / Finance', 'Education / Teaching',
                'Government / Civil Service', 'Healthcare',
                'Business / Entrepreneurship', 'Higher Studies (Not working)', 'Other']
    return render_template('directory.html', students=students,
                           search=search, sector=sector,
                           batch=batch, batches=batches, sectors=sectors)    

@app.route('/notices')
@login_required
def notices():
    all_notices = Notice.query.order_by(
        Notice.is_pinned.desc(),
        Notice.created_at.desc()
    ).all()
    return render_template('notices.html', notices=all_notices)

@app.route('/admin/notice/add', methods=['GET', 'POST'])
@login_required
def add_notice():
    if not current_user.is_admin:
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        notice = Notice(
            title     = request.form.get('title'),
            content   = request.form.get('content'),
            is_pinned = bool(request.form.get('is_pinned'))
        )
        db.session.add(notice)
        db.session.commit()
        flash('Notice posted successfully!')
        return redirect(url_for('notices'))
    return render_template('add_notice.html')

@app.route('/admin/notice/delete/<int:notice_id>', methods=['POST'])
@login_required
def delete_notice(notice_id):
    if not current_user.is_admin:
        return redirect(url_for('dashboard'))
    notice = Notice.query.get_or_404(notice_id)
    db.session.delete(notice)
    db.session.commit()
    flash('Notice deleted.')
    return redirect(url_for('notices'))

@app.route('/admin/notice/pin/<int:notice_id>', methods=['POST'])
@login_required
def toggle_pin(notice_id):
    if not current_user.is_admin:
        return redirect(url_for('dashboard'))
    notice = Notice.query.get_or_404(notice_id)
    notice.is_pinned = not notice.is_pinned
    db.session.commit()
    return redirect(url_for('notices'))

@app.route('/admin/print-report')
@login_required
def print_report():
    if not current_user.is_admin:
        return redirect(url_for('dashboard'))
    students = Student.query.filter_by(is_admin=False).all()
    total    = len(students)
    employed = sum(1 for s in students if s.job_sector and
                   s.job_sector != 'Higher Studies (Not working)')
    higher   = sum(1 for s in students if s.higher_edu)
    from datetime import datetime
    return render_template('print_report.html',
                           students=students, total=total,
                           employed=employed, higher=higher,
                           now=datetime.now())

@app.route('/contact', methods=['GET', 'POST'])
@login_required
def contact():
    if request.method == 'POST':
        msg = Message(
            sender_id   = current_user.id,
            sender_name = current_user.full_name,
            subject     = request.form.get('subject'),
            content     = request.form.get('content')
        )
        db.session.add(msg)
        db.session.commit()
        flash('Your message has been sent to the admin!')
        return redirect(url_for('contact'))
    return render_template('contact.html')

@app.route('/admin/messages')
@login_required
def admin_messages():
    if not current_user.is_admin:
        return redirect(url_for('dashboard'))
    messages = Message.query.order_by(Message.created_at.desc()).all()
    return render_template('admin_messages.html', messages=messages)

@app.route('/admin/messages/read/<int:msg_id>', methods=['POST'])
@login_required
def mark_read(msg_id):
    if not current_user.is_admin:
        return redirect(url_for('dashboard'))
    msg = Message.query.get_or_404(msg_id)
    msg.is_read = True
    db.session.commit()
    return redirect(url_for('admin_messages'))

@app.route('/admin/messages/delete/<int:msg_id>', methods=['POST'])
@login_required
def delete_message(msg_id):
    if not current_user.is_admin:
        return redirect(url_for('dashboard'))
    msg = Message.query.get_or_404(msg_id)
    db.session.delete(msg)
    db.session.commit()
    flash('Message deleted.')
    return redirect(url_for('admin_messages'))

@app.route('/upload-photo', methods=['POST'])
@login_required
def upload_photo():
    if 'photo' not in request.files:
        flash('No file selected.')
        return redirect(url_for('dashboard'))
    file = request.files['photo']
    if file.filename == '':
        flash('No file selected.')
        return redirect(url_for('dashboard'))
    if file and allowed_file(file.filename):
        ext      = file.filename.rsplit('.', 1)[1].lower()
        filename = f"student_{current_user.id}.{ext}"
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        current_user.photo = filename
        db.session.commit()
        flash('Profile photo updated!')
    else:
        flash('Only PNG, JPG, GIF files allowed.')
    return redirect(url_for('dashboard'))

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

# ---------- Run ----------

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        if not Student.query.filter_by(student_id='admin').first():
            admin = Student(
                student_id = 'admin',
                full_name  = 'Admin User',
                phone      = '9800000000',
                batch_year = '2024',
                is_admin   = True
            )
            admin.set_password('9800000000')
            db.session.add(admin)
            db.session.commit()
            print('Test admin created: ID=admin, Password=9800000000')
    app.run(debug=True)
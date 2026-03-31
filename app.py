# =============================================================================
# APP.PY — Main Application File | Alumni Tracker System
# BCA Final Year Project | TU Affiliated College, Nepal
# =============================================================================
#
# PROJECT INFO:
#   Name    : Alumni Tracker System
#   Purpose : Track and manage BCA alumni information, employment and education
#   Tech    : Python 3, Flask, SQLite, HTML/CSS/JS, Chart.js, Groq AI
#   Author  : BCA Final Year Student, TU Affiliated College
#
# ROUTES SUMMARY:
#   /login                  — Login page
#   /dashboard              — Student dashboard
#   /edit-profile           — Edit own profile
#   /change-password        — Change password
#   /upload-photo           — Upload profile photo
#   /directory              — Browse all alumni
#   /notices                — Notice board
#   /contact                — Contact admin form
#   /events                 — Alumni events
#   /idcard                 — Digital alumni ID card
#   /admin                  — Admin panel (admin only)
#   /admin/add-student      — Add new alumni (admin only)
#   /admin/delete/<id>      — Delete alumni (admin only)
#   /admin/view/<id>        — View alumni profile (admin only)
#   /admin/export           — Export CSV (admin only)
#   /admin/print-report     — Print PDF report (admin only)
#   /admin/messages         — View messages (admin only)
#   /admin/notice/add       — Post notice (admin only)
#   /analytics              — Analytics dashboard (admin only)
#   /ai/chat                — AI chatbot
#   /ai/career-advice       — AI career advice
#   /ai/profile-suggestions — AI profile analysis
#   /ai/analytics-summary   — AI analytics summary (admin only)
#
# =============================================================================



from groq import Groq
from dotenv import load_dotenv
import os

load_dotenv()
ai_client = Groq(api_key=os.getenv('GROQ_API_KEY'))
AI_MODEL  = 'llama-3.3-70b-versatile'

import io
from flask import Response
import os
from werkzeug.utils import secure_filename
from database import db, Student, Notice
from flask import Flask, render_template, redirect, url_for, request, flash
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from database import db, Student
from database import db, Student, Notice, Message, Event, RSVP

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

# ───── AI ROUTES ─────

@app.route('/ai/chat')
@login_required
def ai_chat():
    return render_template('ai_chat.html', user=current_user)
@app.route('/ai/chat/message', methods=['POST'])
@login_required
def ai_chat_message():
    from flask import jsonify
    data        = request.json
    user_message = data.get('message', '')
    history      = data.get('history', [])
    if not user_message:
        return jsonify({'error': 'No message'}), 400
    try:
        messages = []
        for h in history:
            if h.get('role') in ['user', 'assistant', 'system']:
                messages.append({
                    "role": h['role'],
                    "content": h['content']
                })
        if not any(m['role'] == 'user' and m['content'] == user_message for m in messages):
            messages.append({"role": "user", "content": user_message})
        response = ai_client.chat.completions.create(
            model=AI_MODEL,
            messages=messages,
            max_tokens=400
        )
        return jsonify({'reply': response.choices[0].message.content})
    except Exception as e:
        return jsonify({'error': str(e)}), 500



@app.route('/ai/career-advice')
@login_required
def ai_career_advice():
    try:
        prompt = f"""You are a career advisor for BCA graduates in Nepal.
        Based on this alumni profile, give personalized career advice in a friendly tone.
        
        Name: {current_user.full_name}
        Batch Year: {current_user.batch_year or 'unknown'}
        Current Job Title: {current_user.job_title or 'not working'}
        Company: {current_user.company or 'none'}
        Job Sector: {current_user.job_sector or 'not specified'}
        Higher Education: {current_user.higher_edu or 'none'}
        Institution: {current_user.institution or 'none'}
        Address: {current_user.address or 'Nepal'}
        
        Give advice in these 3 sections with emojis:
        1. Current Status Assessment (2-3 sentences)
        2. Career Growth Suggestions (3-4 bullet points)
        3. Recommended Next Steps (2-3 actionable steps)
        
        Keep total response under 300 words. Be specific to Nepal's IT/tech job market."""
        response = ai_client.chat.completions.create(
            model=AI_MODEL,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=600
        )
        advice = response.choices[0].message.content
    except Exception as e:
        advice = f"Sorry, could not generate advice at this time. Error: {str(e)}"
    return render_template('ai_career.html', user=current_user, advice=advice)

@app.route('/ai/analytics-summary')
@login_required
def ai_analytics_summary():
    if not current_user.is_admin:
        return redirect(url_for('dashboard'))
    try:
        students = Student.query.filter_by(is_admin=False).all()
        total    = len(students)
        employed = sum(1 for s in students if s.job_sector and
                       s.job_sector != 'Higher Studies (Not working)')
        higher   = sum(1 for s in students if s.higher_edu)
        sectors  = {}
        for s in students:
            sec = s.job_sector or 'Not updated'
            sectors[sec] = sectors.get(sec, 0) + 1
        batches = {}
        for s in students:
            b = s.batch_year or 'Unknown'
            batches[b] = batches.get(b, 0) + 1

        prompt = f"""You are an analytics expert analyzing alumni data for a BCA college in Nepal.
        
        Alumni Statistics:
        - Total alumni registered: {total}
        - Employed: {employed} ({round(employed/total*100) if total else 0}%)
        - In higher education: {higher} ({round(higher/total*100) if total else 0}%)
        - Not updated: {total - employed - higher}
        - Sector breakdown: {sectors}
        - Batch distribution: {batches}
        
        Write a professional analytics summary report with:
        1. Overall Summary (2-3 sentences)
        2. Key Insights (3-4 bullet points with specific numbers)
        3. Trends Observed (2-3 points)
        4. Recommendations for the college (2-3 actionable suggestions)
        
        Keep it under 350 words. Use emojis for section headers."""
        response = ai_client.chat.completions.create(
            model=AI_MODEL,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=700
        )
        summary = response.choices[0].message.content
    except Exception as e:
        summary = f"Could not generate summary. Error: {str(e)}"
    return render_template('ai_analytics.html', user=current_user, summary=summary)

@app.route('/ai/profile-suggestions')
@login_required
def ai_profile_suggestions():
    try:
        prompt = f"""You are a professional profile advisor for BCA graduates in Nepal.
        
        Current profile:
        - Name: {current_user.full_name}
        - Batch: {current_user.batch_year or 'not set'}
        - Job Title: {current_user.job_title or 'empty'}
        - Company: {current_user.company or 'empty'}
        - Sector: {current_user.job_sector or 'empty'}
        - Higher Education: {current_user.higher_edu or 'empty'}
        - Institution: {current_user.institution or 'empty'}
        - Address: {current_user.address or 'empty'}
        - Email: {'provided' if current_user.email else 'missing'}
        
        Analyze this profile and return a JSON object with exactly this structure:
        {{
          "score": <number 0-100>,
          "missing_fields": ["list of empty important fields"],
          "suggestions": ["list of 3-4 specific improvement suggestions"],
          "strengths": ["list of 2-3 things already done well"],
          "job_title_suggestion": "<suggested better job title if current is empty or generic>",
          "sector_suggestion": "<suggested sector based on profile>"
        }}
        
        Return ONLY the JSON, no other text."""
        response = ai_client.chat.completions.create(
            model=AI_MODEL,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=500
        )
        import json
        raw = response.choices[0].message.content.strip()
        raw = raw.replace('```json', '').replace('```', '').strip()
        suggestions = json.loads(raw)
    except Exception as e:
        suggestions = {
            "score": 0,
            "missing_fields": ["Could not analyze profile"],
            "suggestions": [str(e)],
            "strengths": [],
            "job_title_suggestion": "",
            "sector_suggestion": ""
        }
    return render_template('ai_profile.html', user=current_user, data=suggestions)

@app.route('/events')
@login_required
def events():
    all_events = Event.query.order_by(Event.event_date.asc()).all()
    # Get current user's RSVPs
    user_rsvps = {r.event_id: r.status for r in
                  RSVP.query.filter_by(student_id=current_user.id).all()}
    # Get RSVP counts for each event
    rsvp_counts = {}
    for event in all_events:
        rsvp_counts[event.id] = {
            'going':     RSVP.query.filter_by(event_id=event.id, status='going').count(),
            'maybe':     RSVP.query.filter_by(event_id=event.id, status='maybe').count(),
            'not_going': RSVP.query.filter_by(event_id=event.id, status='not_going').count(),
        }
    return render_template('events.html',
        events=all_events,
        user_rsvps=user_rsvps,
        rsvp_counts=rsvp_counts
    )

@app.route('/admin/events/add', methods=['GET', 'POST'])
@login_required
def add_event():
    if not current_user.is_admin:
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        event = Event(
            title       = request.form.get('title'),
            description = request.form.get('description'),
            event_date  = request.form.get('event_date'),
            location    = request.form.get('location'),
            event_type  = request.form.get('event_type')
        )
        db.session.add(event)
        db.session.commit()
        flash('Event added successfully!')
        return redirect(url_for('events'))
    return render_template('add_event.html')

@app.route('/admin/events/delete/<int:event_id>', methods=['POST'])
@login_required
def delete_event(event_id):
    if not current_user.is_admin:
        return redirect(url_for('dashboard'))
    event = Event.query.get_or_404(event_id)
    db.session.delete(event)
    db.session.commit()
    flash('Event deleted.')
    return redirect(url_for('events'))

@app.route('/id-card')
@login_required
def id_card():
    return render_template('id_card.html', user=current_user)


@app.route('/events/rsvp/<int:event_id>', methods=['POST'])
@login_required
def rsvp_event(event_id):
    status = request.form.get('status')
    if status not in ['going', 'maybe', 'not_going']:
        flash('Invalid RSVP status.')
        return redirect(url_for('events'))

    # Check if already RSVP'd
    existing = RSVP.query.filter_by(
        event_id=event_id,
        student_id=current_user.id
    ).first()

    if existing:
        # Update existing RSVP
        existing.status = status
        db.session.commit()
        flash('Your RSVP has been updated!')
    else:
        # Create new RSVP
        rsvp = RSVP(
            event_id   = event_id,
            student_id = current_user.id,
            status     = status
        )
        db.session.add(rsvp)
        db.session.commit()
        flash('Your RSVP has been saved!')

    return redirect(url_for('events'))

@app.route('/admin/events/<int:event_id>/attendees')
@login_required
def event_attendees(event_id):
    if not current_user.is_admin:
        return redirect(url_for('dashboard'))
    event   = Event.query.get_or_404(event_id)
    going   = RSVP.query.filter_by(event_id=event_id, status='going').all()
    maybe   = RSVP.query.filter_by(event_id=event_id, status='maybe').all()
    not_going = RSVP.query.filter_by(event_id=event_id, status='not_going').all()

    # Get student details for each RSVP
    def get_student(rsvp):
        return Student.query.get(rsvp.student_id)

    return render_template('event_attendees.html',
        event=event,
        going=[get_student(r) for r in going],
        maybe=[get_student(r) for r in maybe],
        not_going=[get_student(r) for r in not_going]
    )

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
from flask import Flask, render_template, redirect, url_for, request, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from scraper import scrape_url
from advisor import generate_checklist
from functools import wraps
import os, json, smtplib
from email.mime.text import MIMEText

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///caradvisor.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

ADMIN_EMAIL = os.environ.get('ADMIN_EMAIL', 'olec.laude@gmail.com')
MAIL_USER = os.environ.get('MAIL_USER', 'olec.laude@gmail.com')
MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD', '')

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    status = db.Column(db.String(20), default='pending')  # pending, approved, rejected
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=db.func.now())
    advices = db.relationship('Advice', backref='user', lazy=True)

class Advice(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    url = db.Column(db.String(500))
    title = db.Column(db.String(200))
    vehicle_data = db.Column(db.Text)
    checklist_data = db.Column(db.Text)
    source = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=db.func.now())

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash('Kein Zugriff.')
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return decorated

def send_email(to, subject, body):
    try:
        msg = MIMEText(body, 'plain', 'utf-8')
        msg['Subject'] = subject
        msg['From'] = MAIL_USER
        msg['To'] = to
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(MAIL_USER, MAIL_PASSWORD)
            server.sendmail(MAIL_USER, to, msg.as_string())
    except Exception as e:
        print(f'Email error: {e}')

def ensure_admin():
    admin = User.query.filter_by(email=ADMIN_EMAIL).first()
    if admin and not admin.is_admin:
        admin.is_admin = True
        admin.status = 'approved'
        db.session.commit()

@app.route('/')
def index():
    if current_user.is_authenticated:
        if current_user.status == 'pending':
            return redirect(url_for('pending'))
        if current_user.status == 'rejected':
            logout_user()
            flash('Dein Konto wurde abgelehnt.')
            return redirect(url_for('login'))
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    if request.method == 'POST':
        email = request.form.get('email', '').lower().strip()
        password = request.form.get('password', '')
        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password_hash, password):
            if user.status == 'rejected':
                flash('Dein Konto wurde abgelehnt.')
            elif user.status == 'pending':
                login_user(user)
                return redirect(url_for('pending'))
            else:
                login_user(user)
                return redirect(url_for('dashboard'))
        else:
            flash('E-Mail oder Passwort falsch.')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    if request.method == 'POST':
        email = request.form.get('email', '').lower().strip()
        password = request.form.get('password', '')
        if len(password) < 6:
            flash('Passwort muss mindestens 6 Zeichen haben.')
        elif User.query.filter_by(email=email).first():
            flash('E-Mail bereits registriert.')
        else:
            is_admin = (email == ADMIN_EMAIL)
            status = 'approved' if is_admin else 'pending'
            user = User(email=email, password_hash=generate_password_hash(password), status=status, is_admin=is_admin)
            db.session.add(user)
            db.session.commit()
            login_user(user)
            if not is_admin:
                send_email(
                    ADMIN_EMAIL,
                    f'Car Advisor: Neue Registrierung - {email}',
                    f'Neue Registrierung auf Car Advisor:\n\nE-Mail: {email}\n\nJetzt freigeben oder ablehnen:\nhttps://car-advisor2-1.onrender.com/admin'
                )
            return redirect(url_for('index'))
    return render_template('register.html')

@app.route('/pending')
@login_required
def pending():
    if current_user.status == 'approved':
        return redirect(url_for('dashboard'))
    return render_template('pending.html')

@app.route('/dashboard')
@login_required
def dashboard():
    if current_user.status != 'approved':
        return redirect(url_for('pending'))
    advices = Advice.query.filter_by(user_id=current_user.id).order_by(Advice.created_at.desc()).all()
    return render_template('dashboard.html', advices=advices)

@app.route('/admin')
@login_required
@admin_required
def admin():
    users = User.query.order_by(User.created_at.desc()).all()
    return render_template('admin.html', users=users)

@app.route('/admin/approve/<int:user_id>')
@login_required
@admin_required
def approve_user(user_id):
    user = User.query.get_or_404(user_id)
    user.status = 'approved'
    db.session.commit()
    send_email(user.email, 'Car Advisor: Dein Konto wurde freigegeben!',
        'Hallo,\n\ndein Car Advisor Konto wurde freigegeben. Du kannst dich jetzt einloggen:\nhttps://car-advisor2-1.onrender.com/login\n\nViel Erfolg beim Autokauf!')
    flash(f'{user.email} wurde freigegeben.')
    return redirect(url_for('admin'))

@app.route('/admin/reject/<int:user_id>')
@login_required
@admin_required
def reject_user(user_id):
    user = User.query.get_or_404(user_id)
    user.status = 'rejected'
    db.session.commit()
    flash(f'{user.email} wurde abgelehnt.')
    return redirect(url_for('admin'))

@app.route('/admin/delete/<int:user_id>')
@login_required
@admin_required
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    if user.is_admin:
        flash('Admin kann nicht geloescht werden.')
        return redirect(url_for('admin'))
    Advice.query.filter_by(user_id=user.id).delete()
    db.session.delete(user)
    db.session.commit()
    flash(f'{user.email} wurde geloescht.')
    return redirect(url_for('admin'))

@app.route('/new', methods=['GET', 'POST'])
@login_required
def new_advice():
    if current_user.status != 'approved':
        return redirect(url_for('pending'))
    if request.method == 'POST':
        url = request.form.get('url', '').strip()
        if not url:
            flash('Bitte eine URL eingeben.')
            return render_template('new.html')
        vehicle_data, source = scrape_url(url)
        title = vehicle_data.get('title', 'Fahrzeug')[:200] if vehicle_data else 'Manuelle Eingabe'
        if not vehicle_data:
            source = 'unknown'
        advice = Advice(user_id=current_user.id, url=url, title=title, vehicle_data=json.dumps(vehicle_data or {}), source=source)
        db.session.add(advice)
        db.session.commit()
        return redirect(url_for('analyze', advice_id=advice.id) if vehicle_data else url_for('manual_input', advice_id=advice.id))
    return render_template('new.html')

@app.route('/analyze/<int:advice_id>')
@login_required
def analyze(advice_id):
    advice = Advice.query.filter_by(id=advice_id, user_id=current_user.id).first_or_404()
    vehicle_data = json.loads(advice.vehicle_data or '{}')
    checklist = None
    error = None
    try:
        checklist = generate_checklist(vehicle_data)
        advice.checklist_data = json.dumps(checklist)
        t = checklist.get('vehicle_summary', {}).get('title', '')
        if t:
            advice.title = t[:200]
        db.session.commit()
    except Exception as e:
        error = str(e)
    return render_template('advice.html', advice=advice, checklist=checklist, error=error)

@app.route('/advice/<int:advice_id>')
@login_required
def show_advice(advice_id):
    advice = Advice.query.filter_by(id=advice_id, user_id=current_user.id).first_or_404()
    checklist = json.loads(advice.checklist_data) if advice.checklist_data else None
    return render_template('advice.html', advice=advice, checklist=checklist, error=None)

@app.route('/manual/<int:advice_id>', methods=['GET', 'POST'])
@login_required
def manual_input(advice_id):
    advice = Advice.query.filter_by(id=advice_id, user_id=current_user.id).first_or_404()
    if request.method == 'POST':
        vd = {'title': request.form.get('title',''), 'make': request.form.get('make',''), 'model': request.form.get('model',''), 'year': request.form.get('year',''), 'mileage': request.form.get('mileage','') + ' km', 'price': request.form.get('price','') + ' EUR', 'fuel': request.form.get('fuel','')}
        advice.title = vd['title'] or (vd['make'] + ' ' + vd['model'])
        advice.vehicle_data = json.dumps(vd)
        advice.source = 'manual'
        db.session.commit()
        return redirect(url_for('analyze', advice_id=advice.id))
    return render_template('manual.html', advice=advice)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

with app.app_context():
    db.create_all()
    ensure_admin()

if __name__ == '__main__':
    app.run()

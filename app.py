from flask import Flask, render_template, redirect, url_for, request, jsonify, flash
from flask_login import LoginManager, login_user, login_required, logout_user, current_user, UserMixin
from flask_mail import Mail, Message
from flask_socketio import SocketIO, emit
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField, SelectField, TextAreaField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError
from werkzeug.security import generate_password_hash, check_password_hash
import json
import os
from helpers.helper import read_json, write_json
from openaiconfig.openaiservice import summarize_text
from config import Config

app = Flask(__name__, static_folder='assets/frontend')
app.config.from_object(Config)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

mail = Mail(app)
socketio = SocketIO(app)

# User model for Flask-Login
class User(UserMixin):
    def __init__(self, id, username, email, password_hash):
        self.id = id
        self.username = username
        self.email = email
        self.password_hash = password_hash

    @staticmethod
    def get(user_id):
        users = read_json('storage/UserAccounts.json')
        user = next((u for u in users if u['id'] == user_id), None)
        if user:
            return User(user['id'], user['username'], user['email'], user['password_hash'])
        return None

# Flask-Login user loader
@login_manager.user_loader
def load_user(user_id):
    return User.get(user_id)

# Registration Form using Flask-WTF
class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=2, max=20)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Sign Up')

    def validate_username(self, username):
        users = read_json('storage/UserAccounts.json')
        if any(u['username'] == username.data for u in users):
            raise ValidationError('Username already exists. Please choose a different one.')

    def validate_email(self, email):
        users = read_json('storage/UserAccounts.json')
        if any(u['email'] == email.data for u in users):
            raise ValidationError('Email already registered. Please choose a different one.')

# Login Form using Flask-WTF
class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember = BooleanField('Remember Me')
    submit = SubmitField('Login')

# Dashboard Filters Form
class FilterForm(FlaskForm):
    status = SelectField('Status', choices=[], validators=[Optional()])
    sponsor = StringField('Sponsor')
    topic = StringField('Topic')
    submit = SubmitField('Filter')

# Discussion Form
class DiscussionForm(FlaskForm):
    comment = TextAreaField('Comment', validators=[DataRequired()])
    submit = SubmitField('Post Comment')

# Route for home page
@app.route('/')
def home():
    return app.send_static_file('index.html')

# Route for user registration
@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        users = read_json('storage/UserAccounts.json')
        new_user = {
            'id': str(len(users) + 1),
            'username': form.username.data,
            'email': form.email.data,
            'password_hash': generate_password_hash(form.password.data)
        }
        users.append(new_user)
        write_json('storage/UserAccounts.json', users)
        flash('Your account has been created! You can now log in.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', form=form)

# Route for user login
@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        users = read_json('storage/UserAccounts.json')
        user = next((u for u in users if u['email'] == form.email.data), None)
        if user and check_password_hash(user['password_hash'], form.password.data):
            user_obj = User(user['id'], user['username'], user['email'], user['password_hash'])
            login_user(user_obj, remember=form.remember.data)
            return redirect(url_for('dashboard'))
        else:
            flash('Login Unsuccessful. Please check email and password.', 'danger')
    return render_template('login.html', form=form)

# Route for user logout
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))

# Route for dashboard data
@app.route('/dashboard')
@login_required
def dashboard():
    bills = read_json('storage/CanadaBillsEnhanced.json')
    return jsonify(bills)

# Route for filtering bills
@app.route('/filter_bills', methods=['GET'])
@login_required
def filter_bills():
    status = request.args.get('status')
    sponsor = request.args.get('sponsor')
    topic = request.args.get('topic')
    bills = read_json('storage/CanadaBillsEnhanced.json')
    if status:
        bills = [bill for bill in bills if bill['status'] == status]
    if sponsor:
        bills = [bill for bill in bills if sponsor.lower() in bill['sponsor'].lower()]
    if topic:
        bills = [bill for bill in bills if topic.lower() in bill['topic'].lower()]
    return jsonify(bills)

# Route for bill detail view
@app.route('/bill/<bill_id>')
@login_required
def bill_detail(bill_id):
    bills = read_json('storage/CanadaBillsEnhanced.json')
    bill = next((b for b in bills if b['id'] == bill_id), None)
    if bill:
        return jsonify(bill)
    return jsonify({'error': 'Bill not found'}), 404

# Route for subscribing to a bill
@app.route('/subscribe/<bill_id>', methods=['POST'])
@login_required
def subscribe_bill(bill_id):
    notification_settings = read_json('storage/NotificationSettings.json')
    user_id = current_user.id
    if not any(ns['user_id'] == user_id and ns['bill_id'] == bill_id for ns in notification_settings):
        notification_settings.append({'user_id': user_id, 'bill_id': bill_id})
        write_json('storage/NotificationSettings.json', notification_settings)
        flash('Subscribed to bill notifications.', 'success')
    else:
        flash('Already subscribed to this bill.', 'info')
    return redirect(url_for('bill_detail', bill_id=bill_id))

# Route for discussion threads
@app.route('/discussions/<bill_id>', methods=['GET', 'POST'])
@login_required
def discussions(bill_id):
    form = DiscussionForm()
    discussions = read_json('storage/DiscussionThreads.json')
    bill_discussions = [d for d in discussions if d['bill_id'] == bill_id]
    if form.validate_on_submit():
        new_comment = {
            'id': str(len(discussions) + 1),
            'bill_id': bill_id,
            'user_id': current_user.id,
            'comment': form.comment.data,
            'ai_summary': ''
        }
        discussions.append(new_comment)
        write_json('storage/DiscussionThreads.json', discussions)
        # Emit real-time notification to other users
        socketio.emit('new_comment', {'bill_id': bill_id, 'comment': form.comment.data}, broadcast=True)
        flash('Comment added to discussion.', 'success')
        return redirect(url_for('discussions', bill_id=bill_id))
    return render_template('discussions.html', discussions=bill_discussions, form=form)

# Route for AI summarization of discussions
@app.route('/summarize_discussion/<bill_id>', methods=['POST'])
@login_required
def summarize_discussion(bill_id):
    discussions = read_json('storage/DiscussionThreads.json')
    bill_discussions = [d for d in discussions if d['bill_id'] == bill_id]
    comments = "\n".join([d['comment'] for d in bill_discussions])
    summary = summarize_text(comments)
    summarized = read_json('storage/SummarizedBills.json')
    existing = next((s for s in summarized if s['bill_id'] == bill_id), None)
    if existing:
        existing['summary'] = summary
    else:
        summarized.append({'bill_id': bill_id, 'summary': summary})
    write_json('storage/SummarizedBills.json', summarized)
    flash('Discussion summarized by AI.', 'success')
    return jsonify({'summary': summary})

# Route to send test email
@app.route('/send_test_email')
@login_required
def send_test_email():
    msg = Message('Test Email', sender='noreply@mytegroup.com', recipients=[current_user.email])
    msg.body = 'This is a test email from the Legislative Bill Tracking Platform.'
    mail.send(msg)
    flash('Test email sent.', 'success')
    return redirect(url_for('dashboard'))

# Route to reset password
@app.route('/reset_password', methods=['GET', 'POST'])
@login_required
def reset_password():
    form = RegistrationForm()
    if request.method == 'POST':
        # Implement password reset logic here
        pass
    return render_template('reset_password.html', form=form)

# Serve frontend static files
@app.route('/<path:filename>')
def serve_static_files(filename):
    return app.send_static_file(filename)

# Real-time notifications with SocketIO
@socketio.on('connect')
def handle_connect():
    emit('message', {'data': 'Connected'})

@socketio.on('subscribe')
def handle_subscribe(data):
    bill_id = data.get('bill_id')
    # Handle subscription logic
    pass

@socketio.on('disconnect')
def handle_disconnect():
    emit('message', {'data': 'Disconnected'})

if __name__ == '__main__':
    socketio.run(app, debug=True)

# app.py
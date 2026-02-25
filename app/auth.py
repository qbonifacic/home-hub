import os

import bcrypt
from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import UserMixin, login_user, logout_user, login_required
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired

from . import login_manager, limiter

auth_bp = Blueprint('auth', __name__)

DEFAULT_PW = 'wolfpack2026'

USERS = {
    'dj': os.environ.get('DJ_PASSWORD', DEFAULT_PW),
    'angela': os.environ.get('ANGELA_PASSWORD', DEFAULT_PW),
}

_hashed = {
    name: bcrypt.hashpw(pw.encode(), bcrypt.gensalt())
    for name, pw in USERS.items()
}


class User(UserMixin):
    def __init__(self, username):
        self.id = username


@login_manager.user_loader
def load_user(user_id):
    if user_id in USERS:
        return User(user_id)
    return None


class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Sign In')


@auth_bp.route('/login', methods=['GET', 'POST'])
@limiter.limit('5 per 15 minutes', methods=['POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        username = form.username.data.lower().strip()
        password = form.password.data.encode()
        if username in _hashed and bcrypt.checkpw(password, _hashed[username]):
            login_user(User(username), remember=True)
            return redirect(request.args.get('next') or url_for('dashboard.index'))
        flash('Invalid credentials', 'danger')
    return render_template('login.html', form=form)


@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))

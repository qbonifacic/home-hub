from datetime import datetime

from flask import Blueprint, render_template, redirect, url_for, request
from flask_login import login_required
from flask_wtf import FlaskForm
from wtforms import StringField, DateField, SubmitField
from wtforms.validators import DataRequired

from .sheets import get_all_records, append_row, update_cell, delete_row, get_worksheet

reminders_bp = Blueprint('reminders', __name__)


class ReminderForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired()])
    due_date = DateField('Due Date', validators=[DataRequired()])
    submit = SubmitField('Add Reminder')


@reminders_bp.route('/reminders', methods=['GET', 'POST'])
@login_required
def index():
    form = ReminderForm()
    if form.validate_on_submit():
        now = datetime.now().strftime('%Y-%m-%d %H:%M')
        append_row('Reminders', [
            form.title.data,
            form.due_date.data.strftime('%Y-%m-%d'),
            'No',
            now,
        ])
        return redirect(url_for('reminders.index'))
    try:
        records = get_all_records('Reminders')
    except Exception:
        records = []
    return render_template('reminders.html', reminders=records, form=form)


@reminders_bp.route('/reminders/complete/<int:row_index>', methods=['POST'])
@login_required
def complete(row_index):
    try:
        update_cell('Reminders', row_index, 3, 'Yes')
    except Exception:
        pass
    return redirect(url_for('reminders.index'))


@reminders_bp.route('/reminders/delete/<int:row_index>', methods=['POST'])
@login_required
def delete(row_index):
    try:
        delete_row('Reminders', row_index)
    except Exception:
        pass
    return redirect(url_for('reminders.index'))

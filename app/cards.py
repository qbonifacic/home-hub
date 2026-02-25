import json
import os
from collections import defaultdict
from datetime import datetime

from flask import Blueprint, render_template, redirect, url_for, request
from flask_login import login_required
from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, TextAreaField, SubmitField
from wtforms.validators import DataRequired

cards_bp = Blueprint('cards', __name__)

CARDS_DIR = '/Users/qbot/.openclaw/workspace/butler/memory/cards'

CATEGORIES = [
    'communication', 'preference', 'project', 'routine',
    'health', 'finance', 'technical', 'general',
]


class CardForm(FlaskForm):
    category = SelectField('Category', choices=[(c, c.title()) for c in CATEGORIES])
    learning = TextAreaField('Learning', validators=[DataRequired()])
    confidence = SelectField('Confidence', choices=[
        ('high', 'High'), ('medium', 'Medium'), ('low', 'Low'),
    ])
    submit = SubmitField('Add Card')


def _load_cards():
    cards = []
    if not os.path.isdir(CARDS_DIR):
        return cards
    for fname in os.listdir(CARDS_DIR):
        if not fname.endswith('.json'):
            continue
        try:
            with open(os.path.join(CARDS_DIR, fname)) as f:
                card = json.load(f)
                card['filename'] = fname
                cards.append(card)
        except (json.JSONDecodeError, IOError):
            continue
    cards.sort(key=lambda c: c.get('recorded', ''), reverse=True)
    return cards


def _group_cards(cards):
    grouped = defaultdict(list)
    for c in cards:
        grouped[c.get('category', 'general')].append(c)
    return dict(grouped)


@cards_bp.route('/cards', methods=['GET', 'POST'])
@login_required
def index():
    form = CardForm()
    if form.validate_on_submit():
        now = datetime.now()
        card_id = f"card_{now.strftime('%Y%m%d_%H%M%S')}_{now.microsecond // 1000:03d}"
        card = {
            'id': card_id,
            'category': form.category.data,
            'learning': form.learning.data,
            'confidence': form.confidence.data,
            'recorded': now.isoformat(),
            'superseded_by': None,
        }
        os.makedirs(CARDS_DIR, exist_ok=True)
        with open(os.path.join(CARDS_DIR, f'{card_id}.json'), 'w') as f:
            json.dump(card, f, indent=2)
        return redirect(url_for('cards.index'))
    cards = _load_cards()
    grouped = _group_cards(cards)
    return render_template('cards.html', grouped=grouped, form=form)

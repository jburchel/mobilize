from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, current_app
from flask_login import login_required, current_user
from app.models.user import User
from app.models.task import Task
from app.models.church import Church
from app.models.person import Person
from app.models.pipeline import Pipeline, PipelineStage
from app.models.assignment import Assignment
from app import db
from sqlalchemy import func, desc
import datetime

# Create Blueprint
main_bp = Blueprint('main', __name__)

# Basic routes
@main_bp.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.dashboard'))
    return redirect(url_for('auth.login'))

@main_bp.route('/home')
@login_required
def home():
    return redirect(url_for('dashboard.dashboard'))

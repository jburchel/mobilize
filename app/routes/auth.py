from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, current_app
from flask_login import login_required, current_user, login_user, logout_user
from app.models.user import User
from app import db

# Create Blueprint
auth_bp = Blueprint('auth', __name__)

# Import the actual routes from the auth directory
from app.auth.routes import *

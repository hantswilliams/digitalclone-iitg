"""
Authentication routes for the application
"""
from flask import redirect, session, url_for, jsonify, current_app, request, render_template, flash
from flask_login import login_user, logout_user, current_user
from app.auth import auth_bp
from app.extensions import db, oauth, bcrypt
from app.models import User
from authlib.common.security import generate_token
from app.auth.forms import BasicLoginForm, RegisterForm
import json


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Show login options or handle basic login"""
    form = BasicLoginForm()
    
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user)
            session['user'] = {
                'user_id': user.user_id,
                'name': user.name,
                'email': user.email,
                'username': user.username
            }
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('views.index'))
        else:
            flash('Invalid username or password', 'danger')
    
    return render_template('auth/basic_login.html', form=form)


@auth_bp.route('/google')
def google_login():
    """Start Google OAuth flow"""
    # Check if Google OAuth is configured
    if not current_app.config.get('GOOGLE_CLIENT_ID') or not current_app.config.get('GOOGLE_CLIENT_SECRET'):
        return jsonify({'error': 'Google OAuth not configured'}), 500
    
    # Store a nonce in the session for CSRF protection
    session['nonce'] = generate_token()
    
    # Get the redirect URI for callback
    redirect_uri = url_for('auth.google_auth', _external=True)
    
    # Authorize redirect to Google
    return oauth.google.authorize_redirect(redirect_uri, nonce=session['nonce'])


@auth_bp.route('/google/callback')
def google_auth():
    """Handle Google OAuth callback"""
    try:
        # Get the token from Google
        token = oauth.google.authorize_access_token()
        
        # Parse the ID token to get user info
        user_data = oauth.google.parse_id_token(token, nonce=session['nonce'])
        
        # Store user in session
        session['user'] = user_data
        
        # Create or update user in database
        create_update_user(user_data)
        
        # Redirect to home page
        return redirect('/')
        
    except Exception as e:
        current_app.logger.error(f"Google auth error: {str(e)}")
        return jsonify({'error': 'Authentication failed'}), 400


@auth_bp.route('/logout')
def logout():
    """Logout user"""
    logout_user()
    session.pop('user', None)
    return redirect('/')


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """Handle user registration"""
    form = RegisterForm()
    
    if form.validate_on_submit():
        # Check if username or email already exists
        if User.query.filter_by(username=form.username.data).first():
            flash('Username already exists', 'danger')
            return render_template('auth/register.html', form=form)
        
        if User.query.filter_by(email=form.email.data).first():
            flash('Email already registered', 'danger')
            return render_template('auth/register.html', form=form)
        
        # Create new user
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user = User(
            username=form.username.data,
            email=form.email.data,
            password=hashed_password,
            name=form.name.data,
            user_id=generate_token()  # Generate a unique user_id
        )
        
        try:
            db.session.add(user)
            db.session.commit()
            flash('Registration successful! Please login.', 'success')
            return redirect(url_for('auth.login'))
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error registering user: {str(e)}")
            flash('An error occurred during registration', 'danger')
    
    return render_template('auth/register.html', form=form)


@auth_bp.route('/me')
def me():
    """Get current user info"""
    if 'user' not in session:
        return jsonify({'authenticated': False}), 401
    
    return jsonify({
        'authenticated': True,
        'user': session['user']
    })


def create_update_user(user_data):
    """
    Create or update user in database from OAuth data
    
    Args:
        user_data (dict): User data from OAuth provider
    """
    try:
        user_id = user_data.get('sub')
        email = user_data.get('email')
        
        if not user_id or not email:
            current_app.logger.error("Missing user ID or email in OAuth data")
            return
        
        # Check if user exists
        user = User.query.filter_by(user_id=user_id).first()
        
        if user:
            # Update existing user
            user.email = email
            user.name = user_data.get('name')
            user.profile = user_data.get('picture')
        else:
            # Create new user
            user = User(
                user_id=user_id,
                email=email,
                name=user_data.get('name'),
                profile=user_data.get('picture'),
                permissions='user'  # Default permission
            )
            db.session.add(user)
        
        db.session.commit()
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error creating/updating user: {str(e)}")

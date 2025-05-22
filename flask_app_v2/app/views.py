"""
View routes for the application
"""
import os
import datetime
from werkzeug.utils import secure_filename
from flask import Blueprint, render_template, redirect, url_for, session, request, current_app
from flask_login import login_required
from app.models import Project, Text, Photo, Audio, Video, PowerPoint, User
from app.forms import TextForm, PhotoForm, AudioGenerationForm, VideoGenerationForm, ProjectForm
from app.extensions import db
from app.utils.flash import flash, error_flash, success_flash
from app.errors import APIError
from app.api.routes import api_bp

views_bp = Blueprint('views', __name__)


@views_bp.route('/')
def index():
    """Homepage"""
    return render_template('index.html')


@views_bp.route('/dashboard')
@login_required
def dashboard():
    """User dashboard"""
    user_id = session['user'].get('sub')
    user = User.query.filter_by(user_id=user_id).first()
    
    # Get counts for each media type
    text_count = Text.query.filter_by(user_id=user_id).count()
    photo_count = Photo.query.filter_by(user_id=user_id).count()
    audio_count = Audio.query.filter_by(user_id=user_id).count()
    video_count = Video.query.filter_by(user_id=user_id).count()
    presentation_count = PowerPoint.query.filter_by(user_id=user_id).count()
    
    # Get projects
    projects = Project.query.filter_by(user_id=user_id).order_by(Project.updated_at.desc()).limit(5).all()
    
    # Get recent media
    recent_videos = Video.query.filter_by(user_id=user_id).order_by(Video.created_at.desc()).limit(3).all()
    recent_audios = Audio.query.filter_by(user_id=user_id).order_by(Audio.created_at.desc()).limit(3).all()
    
    return render_template(
        'dashboard.html',
        user=user,
        text_count=text_count,
        photo_count=photo_count,
        audio_count=audio_count,
        video_count=video_count,
        presentation_count=presentation_count,
        projects=projects,
        recent_videos=recent_videos,
        recent_audios=recent_audios
    )


@views_bp.route('/projects')
@login_required
def projects():
    """List all projects for the current user"""
    user_id = session['user'].get('sub')
    user = User.query.filter_by(user_id=user_id).first()
    if not user:
        error_flash('User not found')
        return redirect(url_for('views.index'))
    
    projects = user.projects
    return render_template('projects/index.html', projects=projects)


@views_bp.route('/projects/new', methods=['GET', 'POST'], endpoint='create_project')
@login_required
def create_project():
    """Create a new project"""
    form = ProjectForm()
    if form.validate_on_submit():
        user_id = session['user'].get('sub')
        project = Project(
            user_id=user_id,
            name=form.title.data,
            description=form.description.data
        )

        if form.thumbnail.data:
            try:
                # Save the thumbnail
                filename = secure_filename(form.thumbnail.data.filename)
                file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], 'thumbnails', filename)
                os.makedirs(os.path.dirname(file_path), exist_ok=True)
                form.thumbnail.data.save(file_path)
                project.thumbnail = f'/uploads/thumbnails/{filename}'
            except Exception as e:
                error_flash(f'Error uploading thumbnail: {str(e)}')

        db.session.add(project)
        db.session.commit()
        success_flash('Project created successfully')
        return redirect(url_for('views.projects'))
    
    return render_template('projects/create.html', form=form)


@views_bp.route('/projects/<int:project_id>')
@login_required
def project_details(project_id):
    """Project details page"""
    user_id = session['user'].get('sub')
    
    project = Project.query.filter_by(id=project_id, user_id=user_id).first_or_404()
    
    return render_template('project_details.html', project=project)


@views_bp.route('/projects/<int:project_id>/edit', methods=['GET', 'POST'])
@login_required
def project_edit(project_id):
    """Edit an existing project"""
    user_id = session['user'].get('sub')
    
    # Check if project exists and belongs to current user
    project = Project.query.filter_by(id=project_id, user_id=user_id).first_or_404()
    
    form = ProjectForm(obj=project)
    
    if form.validate_on_submit():
        try:
            # Update project with form data
            form.populate_obj(project)
            project.updated_at = datetime.datetime.now()
            
            db.session.commit()
            
            flash('Project updated successfully!', 'success')
            return redirect(url_for('views.project_details', project_id=project.id))
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error updating project: {str(e)}")
            flash('An error occurred while updating the project', 'error')
    
    return render_template('project_form.html', form=form, title="Edit Project", project=project)


@views_bp.route('/projects/<int:project_id>/delete', methods=['POST'])
@login_required
def delete_project(project_id):
    """Delete a project"""
    user_id = session['user'].get('sub')
    
    # Check if project exists and belongs to current user
    project = Project.query.filter_by(id=project_id, user_id=user_id).first_or_404()
    
    try:
        db.session.delete(project)
        db.session.commit()
        
        flash('Project deleted successfully!', 'success')
        return redirect(url_for('views.projects'))
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error deleting project: {str(e)}")
        flash('An error occurred while deleting the project', 'error')
        return redirect(url_for('views.project_details', project_id=project_id))


@views_bp.route('/texts')
@login_required
def texts():
    """List user texts"""
    user_id = session['user'].get('sub')
    
    # Get all texts for this user
    user_texts = Text.query.filter_by(user_id=user_id).order_by(Text.created_at.desc()).all()
    
    return render_template('texts.html', texts=user_texts)


@views_bp.route('/texts/new', methods=['GET', 'POST'])
@login_required
def create_text():
    """Create a new text"""
    form = TextForm()
    
    if form.validate_on_submit():
        user_id = session['user'].get('sub')
        
        try:
            # Create new text
            text = Text(
                user_id=user_id,
                text_content=form.text_content.data
            )
            
            db.session.add(text)
            db.session.commit()
            
            flash('Text created successfully!', 'success')
            return redirect(url_for('views.text_detail', text_id=text.id))
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error creating text: {str(e)}")
            flash('An error occurred while creating the text', 'error')
    
    return render_template('text_form.html', form=form, title="Create New Text")


@views_bp.route('/texts/<int:text_id>')
@login_required
def text_detail(text_id):
    """Text detail page"""
    user_id = session['user'].get('sub')
    
    text = Text.query.filter_by(id=text_id, user_id=user_id).first_or_404()
    
    # Get associated audios
    audios = Audio.query.filter_by(text_id=text_id).all()
    
    return render_template('text_detail.html', text=text, audios=audios)


@views_bp.route('/photos')
@login_required
def photos():
    """List user photos"""
    user_id = session['user'].get('sub')
    
    # Get all photos for this user
    user_photos = Photo.query.filter_by(user_id=user_id).order_by(Photo.created_at.desc()).all()
    
    return render_template('photos.html', photos=user_photos)


@views_bp.route('/photos/upload', methods=['GET', 'POST'])
@login_required
def upload_photo():
    """Upload a new photo"""
    form = PhotoForm()
    
    if form.validate_on_submit():
        user_id = session['user'].get('sub')
        
        try:
            # Save file locally first
            file = form.file.data
            filename = secure_filename(file.filename)
            file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)
            
            # Upload to S3
            from app.services.storage_service import StorageService
            storage_service = StorageService()
            s3_filename = storage_service.upload_image(filename, file_path)
            
            if not s3_filename:
                raise APIError('Failed to upload image to storage')
            
            # Create photo record
            photo_url = f"https://{current_app.config['S3_BUCKET_NAME']}.s3.amazonaws.com/{s3_filename}"
            photo = Photo(
                user_id=user_id,
                photo_url=photo_url,
                photo_description=form.description.data
            )
            
            db.session.add(photo)
            db.session.commit()
            
            # Clean up local file
            os.remove(file_path)
            
            flash('Photo uploaded successfully!', 'success')
            return redirect(url_for('views.photos'))
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error uploading photo: {str(e)}")
            flash('An error occurred while uploading the photo', 'error')
    
    return render_template('photo_form.html', form=form, title="Upload New Photo")


@views_bp.route('/generate-audio/<int:text_id>', methods=['GET', 'POST'])
@login_required
def generate_audio(text_id):
    """Generate audio from text"""
    user_id = session['user'].get('sub')
    
    # Check if text exists and belongs to current user
    text = Text.query.filter_by(id=text_id, user_id=user_id).first_or_404()
    
    form = AudioGenerationForm()
    form.text_id.data = text_id  # Pre-fill text_id
    
    if form.validate_on_submit():
        try:
            # Start async task for audio generation
            from app.tasks.audio_tasks import generate_audio_task
            task = generate_audio_task.delay(
                form.text_id.data,
                form.voice.data,
                form.provider.data or 'playht',
                user_id
            )
            
            flash('Audio generation started. You will be notified when it completes.', 'success')
            return redirect(url_for('views.task_status', task_id=task.id, return_to=request.referrer))
            
        except Exception as e:
            current_app.logger.error(f"Error starting audio generation task: {str(e)}")
            flash('An error occurred while starting audio generation', 'error')
    
    # Get available voices
    voices = [
        {'id': 'en-US-JennyNeural', 'name': 'Jenny (Female)'},
        {'id': 'en-US-GuyNeural', 'name': 'Guy (Male)'},
        {'id': 'en-US-SaraNeural', 'name': 'Sara (Female)'},
        {'id': 'en-US-ChristopherNeural', 'name': 'Christopher (Male)'}
    ]
    
    return render_template(
        'audio_generation.html',
        form=form,
        text=text,
        voices=voices
    )


@views_bp.route('/generate-video/<int:audio_id>', methods=['GET', 'POST'])
@login_required
def generate_video(audio_id):
    """Generate video from audio and photo"""
    user_id = session['user'].get('sub')
    
    # Check if audio exists and belongs to current user
    audio = Audio.query.filter_by(id=audio_id, user_id=user_id).first_or_404()
    
    form = VideoGenerationForm()
    form.audio_id.data = audio_id  # Pre-fill audio_id
    
    if form.validate_on_submit():
        try:
            # Start async task for video generation
            from app.tasks.video_tasks import generate_video_task
            
            # Extract optional parameters from form
            kwargs = {
                'preprocess': form.preprocess.data,
                'still_mode': form.still_mode.data,
                'use_enhancer': form.use_enhancer.data,
                'pose_style': form.pose_style.data,
                'size': form.size.data,
                'expression_scale': form.expression_scale.data
            }
            
            task = generate_video_task.delay(
                form.photo_id.data,
                form.audio_id.data,
                form.provider.data or 'sadtalker',
                user_id,
                **kwargs
            )
            
            flash('Video generation started. You will be notified when it completes.', 'success')
            return redirect(url_for('views.task_status', task_id=task.id, return_to=request.referrer))
            
        except Exception as e:
            current_app.logger.error(f"Error starting video generation task: {str(e)}")
            flash('An error occurred while starting video generation', 'error')
    
    # Get user's photos for selection
    photos = Photo.query.filter_by(user_id=user_id).all()
    
    return render_template(
        'video_generation.html',
        form=form,
        audio=audio,
        photos=photos
    )


@views_bp.route('/task-status/<task_id>')
@login_required
def task_status(task_id):
    """Show task status page"""
    return_to = request.args.get('return_to', url_for('views.dashboard'))
    
    return render_template(
        'task_status.html',
        task_id=task_id,
        return_to=return_to
    )

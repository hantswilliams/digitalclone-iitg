"""
View routes for the application
"""
import os
import datetime
from werkzeug.utils import secure_filename
from flask import Blueprint, render_template, redirect, url_for, session, request, current_app, jsonify, send_from_directory, abort
from flask_login import login_required, current_user
from app.models import Project, Text, Photo, Audio, Video, PowerPoint, User, ClonedVoice
from app.forms import TextForm, PhotoForm, AudioGenerationForm, VideoGenerationForm, ProjectForm, VoiceCloneForm
from app.extensions import db
from app.utils.flash import flash, error_flash, success_flash
from app.errors import APIError
from app.api.routes import api_bp

views_bp = Blueprint('views', __name__)


# Route to serve uploaded files
@views_bp.route('/uploads/<path:filename>')
def uploaded_file(filename):
    """Serve uploaded files from the uploads directory"""
    try:
        upload_folder = current_app.config['UPLOAD_FOLDER']
        return send_from_directory(upload_folder, filename)
    except Exception as e:
        current_app.logger.error(f"Error serving uploaded file {filename}: {str(e)}")
        abort(404)


@views_bp.route('/')
def index():
    """Homepage"""
    # If user is already logged in, redirect to dashboard
    if current_user.is_authenticated:
        return redirect(url_for('views.dashboard'))
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
    
    # Get all projects for this user from the database
    projects = Project.query.filter_by(user_id=user_id).all()
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


@views_bp.route('/projects/<int:project_id>/add-text', methods=['POST'])
@login_required
def add_text_to_project(project_id):
    """Add text to a project"""
    user_id = session['user'].get('sub')
    
    # Check if project exists and belongs to current user
    project = Project.query.filter_by(id=project_id, user_id=user_id).first_or_404()
    
    # Get the text content from the form
    text_content = request.form.get('text_content')
    
    if not text_content:
        error_flash('Text content is required')
        return redirect(url_for('views.project_details', project_id=project_id))
    
    try:
        # Create new text
        text = Text(
            user_id=user_id,
            text_content=text_content
        )
        
        # Add text to database first
        db.session.add(text)
        db.session.flush()  # This assigns an ID to the text object
        
        # Associate the text with the project using the many-to-many relationship
        project.texts.append(text)
        
        db.session.commit()
        
        success_flash('Text added to project successfully')
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error adding text to project: {str(e)}")
        error_flash('Error adding text to project')
    
    return redirect(url_for('views.project_details', project_id=project_id))


@views_bp.route('/projects/<int:project_id>/upload-photo', methods=['POST'])
@login_required
def upload_photo_to_project(project_id):
    """Upload photo to a project"""
    user_id = session['user'].get('sub')
    
    # Check if project exists and belongs to current user
    project = Project.query.filter_by(id=project_id, user_id=user_id).first_or_404()
    
    # Check if file was uploaded
    if 'file' not in request.files:
        error_flash('No file uploaded')
        return redirect(url_for('views.project_details', project_id=project_id))
    
    file = request.files['file']
    if file.filename == '':
        error_flash('No file selected')
        return redirect(url_for('views.project_details', project_id=project_id))
    
    if not file or not file.content_type.startswith('image/'):
        error_flash('Only image files are allowed')
        return redirect(url_for('views.project_details', project_id=project_id))
    
    try:
        # Save the file
        filename = secure_filename(file.filename)
        timestamp = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
        new_filename = f"{timestamp}_{filename}"
        
        # Create storage path
        file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], 'photos', new_filename)
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        file.save(file_path)
        
        # Create photo record
        photo = Photo(
            user_id=user_id,
            photo_url=f'/uploads/photos/{new_filename}',
            photo_description=request.form.get('description', '')
        )
        
        db.session.add(photo)
        db.session.flush()  # This assigns an ID to the photo object
        
        # Associate the photo with the project using the many-to-many relationship
        project.photos.append(photo)
        
        db.session.commit()
        
        success_flash('Photo uploaded successfully')
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error uploading photo: {str(e)}")
        error_flash(f'Error uploading photo: {str(e)}')
    
    return redirect(url_for('views.project_details', project_id=project_id))


@views_bp.route('/projects/<int:project_id>/create-presentation', methods=['POST'])
@login_required
def create_presentation(project_id):
    """Create presentation from project videos"""
    user_id = session['user'].get('sub')
    
    # Check if project exists and belongs to current user
    project = Project.query.filter_by(id=project_id, user_id=user_id).first_or_404()
    
    title = request.form.get('title')
    video_ids = request.form.getlist('videos[]')
    
    if not title:
        error_flash('Title is required')
        return redirect(url_for('views.project_details', project_id=project_id))
    
    if not video_ids:
        error_flash('No videos selected')
        return redirect(url_for('views.project_details', project_id=project_id))
    
    try:
        # Get the videos
        videos = Video.query.filter(Video.id.in_(video_ids), Video.user_id == user_id).all()
        
        if not videos:
            error_flash('No valid videos found')
            return redirect(url_for('views.project_details', project_id=project_id))
        
        # Start async task for presentation creation
        from app.tasks.presentation_tasks import create_presentation_task
        
        # Prepare slide data
        slides_data = []
        for video in videos:
            slides_data.append({
                'title': f"Video {video.id}",
                'content': video.video_text,
                'video_url': video.video_url
            })
        
        task = create_presentation_task.delay(
            title,
            slides_data,
            user_id
        )
        
        # Create PowerPoint entry
        ppt = PowerPoint(
            user_id=user_id,
            title=title,
            ppt_url=f"/pending/{task.id}",  # Will be updated when task completes
            status="processing"
        )
        
        db.session.add(ppt)
        db.session.flush()  # This assigns an ID to the ppt object
        
        # Associate the presentation with the project using the many-to-many relationship
        project.powerpoints.append(ppt)
        
        db.session.commit()
        
        success_flash('Presentation creation started. You will be notified when it completes.')
        return redirect(url_for('views.task_status', task_id=task.id, return_to=url_for('views.project_details', project_id=project_id)))
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error creating presentation: {str(e)}")
        error_flash(f'Error creating presentation: {str(e)}')
    
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


@views_bp.route('/texts/<int:text_id>/generate-audio')
@login_required
def text_generate_audio(text_id):
    """Generate audio from text"""
    user_id = session['user'].get('sub')
    
    # Check if text exists and belongs to current user
    text = Text.query.filter_by(id=text_id, user_id=user_id).first_or_404()
    
    # Redirect to audio generation form
    return redirect(url_for('views.audio_generation', text_id=text_id))


@views_bp.route('/audio-generation/<int:text_id>', methods=['GET', 'POST'])
@login_required
def audio_generation(text_id):
    """Audio generation form"""
    user_id = session['user'].get('sub')
    
    # Check if text exists and belongs to current user
    text = Text.query.filter_by(id=text_id, user_id=user_id).first_or_404()
    
    form = AudioGenerationForm()
    
    if form.validate_on_submit():
        try:
            # Start async task for audio generation
            from app.tasks.audio_tasks import generate_audio_task
            
            task = generate_audio_task.delay(
                text_id,
                form.voice.data,
                user_id
            )
            
            success_flash('Audio generation started. You will be notified when it completes.')
            return redirect(url_for('views.task_status', task_id=task.id, return_to=request.referrer))
            
        except Exception as e:
            current_app.logger.error(f"Error starting audio generation task: {str(e)}")
            error_flash(f'Error starting audio generation: {str(e)}')
    
    return render_template(
        'audio/generate.html',
        form=form,
        text=text
    )


@views_bp.route('/audios/<int:audio_id>/generate-video')
@login_required
def generate_video(audio_id):
    """Generate video from audio"""
    user_id = session['user'].get('sub')
    
    # Check if audio exists and belongs to current user
    audio = Audio.query.filter_by(id=audio_id, user_id=user_id).first_or_404()
    
    # Redirect to video generation form
    return redirect(url_for('views.video_generation', audio_id=audio_id))


@views_bp.route('/presentations/<int:ppt_id>/create-scorm')
@login_required
def create_scorm(ppt_id):
    """Create SCORM package from presentation"""
    user_id = session['user'].get('sub')
    
    # Check if presentation exists and belongs to current user
    ppt = PowerPoint.query.filter_by(id=ppt_id, user_id=user_id).first_or_404()
    
    try:
        # Start async task for SCORM creation
        from app.tasks.presentation_tasks import create_scorm_task
        
        task = create_scorm_task.delay(ppt_id, user_id)
        
        success_flash('SCORM package creation started. You will be notified when it completes.')
        return redirect(url_for('views.task_status', task_id=task.id, return_to=request.referrer))
        
    except Exception as e:
        current_app.logger.error(f"Error starting SCORM creation task: {str(e)}")
        error_flash(f'Error starting SCORM creation: {str(e)}')
    
    return redirect(url_for('views.project_details', project_id=ppt.project_id))


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
            if form.voice_type.data == 'cloned':
                # Use cloned voice
                task = generate_audio_task.delay(
                    form.text_id.data,
                    form.voice.data,
                    form.provider.data,
                    user_id,
                    use_cloned_voice=True
                )
            else:
                # Use default voice
                task = generate_audio_task.delay(
                    form.text_id.data,
                    form.voice.data,
                    form.provider.data,
                    user_id,
                    use_cloned_voice=False
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
        'audio/generate.html',
        form=form,
        text=text,
        voices=voices
    )


@views_bp.route('/generate-video/<int:audio_id>', methods=['GET', 'POST'])
@login_required
def video_generate_video(audio_id):
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


@views_bp.route('/voices')
@login_required
def voice_list():
    """List user's cloned voices"""
    user_id = session['user'].get('sub')
    
    # Get user's cloned voices from database
    voices = ClonedVoice.query.filter_by(user_id=user_id).order_by(ClonedVoice.created_at.desc()).all()
    
    return render_template('voices/index.html', voices=voices)


@views_bp.route('/voices/create', methods=['GET', 'POST'])
@login_required
def create_voice():
    """Create a new cloned voice"""
    user_id = session['user'].get('sub')
    form = VoiceCloneForm()
    
    if form.validate_on_submit():
        try:
            # Create temp directory for audio files if it doesn't exist
            voice_samples_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], 'voice_samples', user_id)
            os.makedirs(voice_samples_dir, exist_ok=True)
            
            # Save uploaded audio files
            audio_files = []
            for audio_file in form.audio_files.data:
                if audio_file:
                    filename = secure_filename(audio_file.filename)
                    filepath = os.path.join(voice_samples_dir, filename)
                    audio_file.save(filepath)
                    audio_files.append(filepath)
            
            if not audio_files:
                flash('No audio files were uploaded', 'error')
                return render_template('voices/create.html', form=form)
            
            # Start async task for voice cloning
            from app.tasks.voice_tasks import clone_voice_task
            task = clone_voice_task.delay(
                audio_files,
                form.voice_name.data,
                form.voice_type.data,
                form.provider.data,
                user_id
            )
            
            flash('Voice cloning started. You will be notified when it completes.', 'success')
            return redirect(url_for('views.task_status', task_id=task.id, return_to=url_for('views.voice_list')))
            
        except Exception as e:
            current_app.logger.error(f"Error in create_voice: {str(e)}")
            flash('An error occurred while creating the voice clone', 'error')
    
    return render_template('voices/create.html', form=form)


@views_bp.route('/voices/<int:voice_id>/delete', methods=['POST'])
@login_required
def delete_voice(voice_id):
    """Delete a cloned voice"""
    user_id = session['user'].get('sub')
    
    # Get voice and verify ownership
    voice = ClonedVoice.query.filter_by(id=voice_id, user_id=user_id).first_or_404()
    
    try:
        db.session.delete(voice)
        db.session.commit()
        return jsonify({'success': True})
        
    except Exception as e:
        current_app.logger.error(f"Error deleting voice {voice_id}: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@views_bp.route('/voices/<int:voice_id>/use')
@login_required
def use_voice(voice_id):
    """Use a cloned voice for text-to-speech"""
    user_id = session['user'].get('sub')
    
    # Get voice and verify ownership
    voice = ClonedVoice.query.filter_by(id=voice_id, user_id=user_id).first_or_404()
    
    # Redirect to text list with voice preselected
    return redirect(url_for('views.text_list', voice_id=voice_id))

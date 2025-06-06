from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy import func, desc
from datetime import datetime, timedelta
from app.models.job import Job
from app.extensions import db

analytics_bp = Blueprint('analytics', __name__)

def serialize_metadata(metadata):
    """Helper function to safely serialize job metadata"""
    if metadata is None:
        return None
    
    # If it's already a dict, return it
    if isinstance(metadata, dict):
        return metadata
    
    # If it's a string, try to parse as JSON
    if isinstance(metadata, str):
        try:
            import json
            return json.loads(metadata)
        except:
            return {'raw': metadata}
    
    # For any other type (like SQLAlchemy objects), convert to string
    try:
        return str(metadata)
    except:
        return None

def get_status_value(status):
    """Safely get the string value from job status enum"""
    if hasattr(status, 'value'):
        return status.value
    return str(status)

def get_job_duration(job):
    """Calculate job duration in seconds"""
    if job.actual_start_time and job.actual_end_time:
        return (job.actual_end_time - job.actual_start_time).total_seconds()
    elif job.completed_at and job.created_at:
        return (job.completed_at - job.created_at).total_seconds()
    return None

@analytics_bp.route('/dashboard', methods=['GET'])
@jwt_required()
def get_dashboard_analytics():
    """Get analytics dashboard data for all jobs"""
    try:
        # Get time range filter (default to 'all')
        time_range = request.args.get('time_range', 'all')
        
        # Build base query
        query = Job.query
        
        # Apply time filter
        if time_range != 'all':
            if time_range == '7d':
                cutoff_date = datetime.utcnow() - timedelta(days=7)
            elif time_range == '30d':
                cutoff_date = datetime.utcnow() - timedelta(days=30)
            elif time_range == '90d':
                cutoff_date = datetime.utcnow() - timedelta(days=90)
            else:
                cutoff_date = datetime.utcnow() - timedelta(days=7)  # default
            
            query = query.filter(Job.created_at >= cutoff_date)
        
        # Get all jobs for analysis
        jobs = query.all()
        
        # Calculate summary statistics
        total_jobs = len(jobs)
        completed_jobs = len([j for j in jobs if get_status_value(j.status) == 'completed'])
        failed_jobs = len([j for j in jobs if get_status_value(j.status) == 'failed'])
        in_progress_jobs = len([j for j in jobs if get_status_value(j.status) in ['pending', 'processing']])
        
        success_rate = (completed_jobs / total_jobs * 100) if total_jobs > 0 else 0
        
        # Calculate average processing time for completed jobs
        completed_with_times = [j for j in jobs if get_status_value(j.status) == 'completed' and j.completed_at and j.created_at]
        avg_processing_time = 0
        if completed_with_times:
            total_time = sum([(j.completed_at - j.created_at).total_seconds() for j in completed_with_times])
            avg_processing_time = total_time / len(completed_with_times)
        
        # Job breakdown by status
        status_breakdown = {
            'completed': completed_jobs,
            'failed': failed_jobs,
            'pending': len([j for j in jobs if get_status_value(j.status) == 'pending']),
            'processing': len([j for j in jobs if get_status_value(j.status) == 'processing']),
            'cancelled': len([j for j in jobs if get_status_value(j.status) == 'cancelled'])
        }
        
        # Model usage breakdown from service_metadata
        model_usage = {}
        job_performance_table = []
        
        for job in jobs:
            # Get job duration
            duration = get_job_duration(job)
            
            # Process service_metadata for model information
            service_metadata = serialize_metadata(job.service_metadata)
            
            # Create job performance entry for tabular display
            job_entry = {
                'id': job.id,  # Frontend expects 'id', not 'job_id'
                'title': job.title,
                'status': get_status_value(job.status),
                'job_type': job.job_type.value if hasattr(job.job_type, 'value') else str(job.job_type),
                'created_at': job.created_at.isoformat() if job.created_at else None,
                'completed_at': job.completed_at.isoformat() if job.completed_at else None,
                'duration': duration,  # Frontend expects 'duration', not 'duration_seconds'
                'duration_formatted': f"{int(duration // 60)}m {int(duration % 60)}s" if duration else "N/A",
                'llm_model': 'N/A',     # Frontend expects these specific keys
                'tts_model': 'N/A',
                'video_model': 'N/A',
                'models_used': {},
                'model_details': {}
            }
            
            if isinstance(service_metadata, dict):
                # Extract model information from service_metadata
                for service_name, service_info in service_metadata.items():
                    if isinstance(service_info, dict):
                        model_name = service_info.get('model_name', 'unknown')
                        model_type = service_info.get('model_type', 'unknown')
                        
                        # Map service names to frontend model fields
                        if service_name.lower() == 'indextts':
                            job_entry['tts_model'] = model_name
                        elif service_name.lower() == 'kdtalker':
                            job_entry['video_model'] = model_name
                        elif 'llm' in service_name.lower() or 'language' in service_name.lower():
                            job_entry['llm_model'] = model_name
                        
                        # Add to job entry
                        job_entry['models_used'][service_name] = model_name
                        job_entry['model_details'][service_name] = {
                            'model_name': model_name,
                            'model_type': model_type,
                            'huggingface_url': service_info.get('huggingface_url'),
                            'library_name': service_info.get('library_name'),
                            'license': service_info.get('license'),
                            'model_size': service_info.get('model_size'),
                            'tags': service_info.get('tags', [])
                        }
                        
                        # Count for overall usage (organize by model type for frontend)
                        if service_name.lower() == 'indextts':
                            model_type_key = 'tts'
                        elif service_name.lower() == 'kdtalker':
                            model_type_key = 'video'
                        else:
                            model_type_key = service_name.lower()
                            
                        if model_type_key not in model_usage:
                            model_usage[model_type_key] = {}
                        if model_name not in model_usage[model_type_key]:
                            model_usage[model_type_key][model_name] = 0
                        model_usage[model_type_key][model_name] += 1
            
            job_performance_table.append(job_entry)
        
        # Daily performance (last 30 days)
        daily_performance = []
        for i in range(30):
            date = datetime.utcnow() - timedelta(days=i)
            date_start = date.replace(hour=0, minute=0, second=0, microsecond=0)
            date_end = date_start + timedelta(days=1)
            
            day_jobs = [j for j in jobs if date_start <= j.created_at < date_end]
            day_completed = len([j for j in day_jobs if get_status_value(j.status) == 'completed'])
            day_failed = len([j for j in day_jobs if get_status_value(j.status) == 'failed'])
            
            daily_performance.append({
                'date': date_start.strftime('%Y-%m-%d'),
                'total_jobs': len(day_jobs),
                'completed': day_completed,
                'failed': day_failed,
                'success_rate': (day_completed / len(day_jobs) * 100) if len(day_jobs) > 0 else 0
            })
        
        # Recent jobs (last 10)
        recent_jobs = []
        for job in sorted(jobs, key=lambda x: x.created_at, reverse=True)[:10]:
            processing_time = get_job_duration(job)
            
            recent_jobs.append({
                'id': job.id,
                'title': job.title,
                'status': get_status_value(job.status),
                'created_at': job.created_at.isoformat() if job.created_at else None,
                'completed_at': job.completed_at.isoformat() if job.completed_at else None,
                'processing_time': processing_time,
                'service_metadata': serialize_metadata(job.service_metadata)
            })
        
        # Benchmark comparison data
        benchmark_data = {
            'avg_processing_time': avg_processing_time,
            'success_rate': success_rate,
            'total_jobs': total_jobs,
            'models_used': {
                'service_count': len(model_usage),
                'total_model_types': sum(len(models) for models in model_usage.values())
            }
        }
        
        return jsonify({
            'summary': {
                'total_jobs': total_jobs,
                'completed_jobs': completed_jobs,
                'failed_jobs': failed_jobs,
                'in_progress_jobs': in_progress_jobs,
                'success_rate': round(success_rate, 2),
                'avg_processing_time': round(avg_processing_time, 2)
            },
            'status_breakdown': status_breakdown,
            'model_usage': model_usage,
            'job_performance_table': job_performance_table,
            'daily_performance': daily_performance,
            'recent_jobs': recent_jobs,
            'benchmark_data': benchmark_data,
            'time_range': time_range
        })
        
    except Exception as e:
        import traceback
        print(f"Analytics endpoint error: {str(e)}")
        traceback.print_exc()
        return jsonify({'error': 'Internal server error', 'details': str(e)}), 500

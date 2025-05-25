"""
MinIO/S3 storage service for file operations
"""
import os
import logging
from datetime import timedelta
from urllib.parse import urljoin
import minio
from minio.error import S3Error
from flask import current_app

logger = logging.getLogger(__name__)


class StorageService:
    """MinIO/S3 storage service for file operations"""
    
    def __init__(self, app=None):
        self.client = None
        if app:
            self.init_app(app)
    
    def init_app(self, app):
        """Initialize MinIO client with Flask app"""
        try:
            self.client = minio.Minio(
                endpoint=app.config.get('MINIO_ENDPOINT'),
                access_key=app.config.get('MINIO_ACCESS_KEY'),
                secret_key=app.config.get('MINIO_SECRET_KEY'),
                secure=app.config.get('MINIO_SECURE', False)
            )
            
            # Ensure bucket exists
            bucket_name = app.config.get('MINIO_BUCKET_NAME')
            if not self.client.bucket_exists(bucket_name):
                logger.info(f"Creating bucket: {bucket_name}")
                self.client.make_bucket(bucket_name)
                
                # Set bucket policy for public read access to certain prefixes
                policy = {
                    "Version": "2012-10-17",
                    "Statement": [
                        {
                            "Effect": "Allow",
                            "Principal": {"AWS": "*"},
                            "Action": "s3:GetObject",
                            "Resource": f"arn:aws:s3:::{bucket_name}/public/*"
                        }
                    ]
                }
                
                # Note: Setting bucket policy requires admin privileges
                # For development, we'll handle this through signed URLs
                
            logger.info("MinIO client initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize MinIO client: {str(e)}")
            raise
    
    def upload_file(self, file_data, object_name, bucket_name=None, content_type=None):
        """
        Upload file to MinIO bucket
        
        Args:
            file_data: File-like object or bytes
            object_name: Object name in bucket (path)
            bucket_name: Bucket name (defaults to configured bucket)
            content_type: MIME type of the file
            
        Returns:
            dict: Upload result with metadata
        """
        if not bucket_name:
            bucket_name = current_app.config.get('MINIO_BUCKET_NAME')
        
        try:
            # Get file size
            if hasattr(file_data, 'seek') and hasattr(file_data, 'tell'):
                # File-like object
                file_data.seek(0, 2)  # Seek to end
                file_size = file_data.tell()
                file_data.seek(0)  # Reset to beginning
            else:
                # Bytes
                file_size = len(file_data)
            
            # Upload file
            result = self.client.put_object(
                bucket_name=bucket_name,
                object_name=object_name,
                data=file_data,
                length=file_size,
                content_type=content_type
            )
            
            logger.info(f"File uploaded successfully: {object_name}")
            
            return {
                'success': True,
                'bucket_name': bucket_name,
                'object_name': object_name,
                'file_size': file_size,
                'etag': result.etag,
                'version_id': result.version_id
            }
            
        except S3Error as e:
            logger.error(f"MinIO upload error: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'error_code': e.code
            }
        except Exception as e:
            logger.error(f"Upload error: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def download_file(self, object_name, bucket_name=None):
        """
        Download file from MinIO bucket
        
        Args:
            object_name: Object name in bucket
            bucket_name: Bucket name (defaults to configured bucket)
            
        Returns:
            bytes: File data or None if error
        """
        if not bucket_name:
            bucket_name = current_app.config.get('MINIO_BUCKET_NAME')
        
        try:
            response = self.client.get_object(bucket_name, object_name)
            data = response.data
            response.close()
            response.release_conn()
            return data
            
        except S3Error as e:
            logger.error(f"MinIO download error: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Download error: {str(e)}")
            return None
    
    def delete_file(self, object_name, bucket_name=None):
        """
        Delete file from MinIO bucket
        
        Args:
            object_name: Object name in bucket
            bucket_name: Bucket name (defaults to configured bucket)
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not bucket_name:
            bucket_name = current_app.config.get('MINIO_BUCKET_NAME')
        
        try:
            self.client.remove_object(bucket_name, object_name)
            logger.info(f"File deleted successfully: {object_name}")
            return True
            
        except S3Error as e:
            logger.error(f"MinIO delete error: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Delete error: {str(e)}")
            return False
    
    def get_presigned_url(self, object_name, bucket_name=None, expires=timedelta(hours=1), method='GET'):
        """
        Generate presigned URL for file access
        
        Args:
            object_name: Object name in bucket
            bucket_name: Bucket name (defaults to configured bucket)
            expires: URL expiration time
            method: HTTP method ('GET' for download, 'PUT' for upload)
            
        Returns:
            str: Presigned URL or None if error
        """
        if not bucket_name:
            bucket_name = current_app.config.get('MINIO_BUCKET_NAME')
        
        try:
            if method.upper() == 'PUT':
                url = self.client.presigned_put_object(bucket_name, object_name, expires=expires)
            else:
                url = self.client.presigned_get_object(bucket_name, object_name, expires=expires)
                
            return url
            
        except S3Error as e:
            logger.error(f"MinIO presigned URL error: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Presigned URL error: {str(e)}")
            return None
    
    def list_objects(self, prefix=None, bucket_name=None):
        """
        List objects in bucket
        
        Args:
            prefix: Object name prefix to filter by
            bucket_name: Bucket name (defaults to configured bucket)
            
        Returns:
            list: List of object information
        """
        if not bucket_name:
            bucket_name = current_app.config.get('MINIO_BUCKET_NAME')
        
        try:
            objects = []
            for obj in self.client.list_objects(bucket_name, prefix=prefix):
                objects.append({
                    'object_name': obj.object_name,
                    'size': obj.size,
                    'last_modified': obj.last_modified,
                    'etag': obj.etag,
                    'content_type': obj.content_type
                })
            
            return objects
            
        except S3Error as e:
            logger.error(f"MinIO list error: {str(e)}")
            return []
        except Exception as e:
            logger.error(f"List error: {str(e)}")
            return []
    
    def get_object_info(self, object_name, bucket_name=None):
        """
        Get object metadata
        
        Args:
            object_name: Object name in bucket
            bucket_name: Bucket name (defaults to configured bucket)
            
        Returns:
            dict: Object metadata or None if error
        """
        if not bucket_name:
            bucket_name = current_app.config.get('MINIO_BUCKET_NAME')
        
        try:
            stat = self.client.stat_object(bucket_name, object_name)
            return {
                'object_name': stat.object_name,
                'size': stat.size,
                'last_modified': stat.last_modified,
                'etag': stat.etag,
                'content_type': stat.content_type,
                'metadata': stat.metadata
            }
            
        except S3Error as e:
            logger.error(f"MinIO stat error: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Stat error: {str(e)}")
            return None
    
    def file_exists(self, object_name, bucket_name=None):
        """
        Check if file exists in bucket
        
        Args:
            object_name: Object name in bucket
            bucket_name: Bucket name (defaults to configured bucket)
            
        Returns:
            bool: True if file exists, False otherwise
        """
        return self.get_object_info(object_name, bucket_name) is not None


# Global storage service instance
storage_service = StorageService()

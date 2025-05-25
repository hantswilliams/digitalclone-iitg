#!/usr/bin/env python3
"""
Development script to start the Flask application
"""
import os
import sys
from pathlib import Path

# Add the backend directory to the Python path
backend_dir = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_dir))

from app import create_app
from app.config import DevelopmentConfig


def main():
    """Main function to start the development server"""
    # Create Flask app with development config
    app = create_app(DevelopmentConfig)
    
    # Get host and port from environment or use defaults
    host = os.environ.get('FLASK_HOST', '0.0.0.0')
    port = int(os.environ.get('FLASK_PORT', 5000))
    debug = os.environ.get('FLASK_DEBUG', 'true').lower() == 'true'
    
    print("🚀 Starting Voice-Clone Talking-Head Lecturer API")
    print(f"🌐 Server: http://{host}:{port}")
    print(f"🐛 Debug mode: {debug}")
    print(f"⚙️  Environment: {app.config['FLASK_ENV']}")
    print("\n📋 Available endpoints:")
    print("  🔐 Authentication:")
    print("    GET  /health                    - Health check")
    print("    POST /api/auth/register         - User registration")
    print("    POST /api/auth/login            - User login")
    print("    POST /api/auth/refresh          - Token refresh")
    print("    POST /api/auth/logout           - User logout")
    print("    GET  /api/auth/profile          - Get user profile")
    print("    PUT  /api/auth/profile          - Update user profile")
    print("    POST /api/auth/change-password  - Change password")
    print("    POST /api/auth/verify-token     - Verify token")
    print("  📁 Asset Management:")
    print("    GET  /api/assets/               - List user assets")
    print("    POST /api/assets/upload         - Upload asset file")
    print("    POST /api/assets/presigned-upload - Get presigned upload URL")
    print("    GET  /api/assets/<id>           - Get asset details")
    print("    GET  /api/assets/<id>/download  - Get download URL")
    print("    POST /api/assets/<id>/confirm-upload - Confirm presigned upload")
    print("    DELETE /api/assets/<id>         - Delete asset")
    print("\n🧪 Testing:")
    print("  python scripts/test_auth.py     - Test authentication")
    print("  python scripts/test_assets.py   - Test asset management")
    print("📚 View API docs at: http://localhost:5000 (coming soon)")
    print("\n⏹️  Press Ctrl+C to stop the server\n")
    
    try:
        app.run(host=host, port=port, debug=debug)
    except KeyboardInterrupt:
        print("\n\n👋 Server stopped by user")
    except Exception as e:
        print(f"\n❌ Server error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Simple Celery + Redis Integration Test
Tests Stage 4 - Celery + Redis functionality
"""

import os
import sys
import time
import redis
from celery import Celery

# Add the current directory to the path so we can import our app
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_redis_connection():
    """Test Redis connectivity"""
    print("🔗 Testing Redis Connection...")
    
    try:
        redis_client = redis.from_url('redis://localhost:6379/0')
        response = redis_client.ping()
        if response:
            print("✅ Redis connection successful")
            
            # Test basic operations
            redis_client.set('test_key', 'test_value', ex=60)
            value = redis_client.get('test_key')
            if value == b'test_value':
                print("✅ Redis read/write operations working")
            else:
                print("❌ Redis read/write operations failed")
                
            redis_client.delete('test_key')
            return True
        else:
            print("❌ Redis connection failed")
            return False
    except Exception as e:
        print(f"❌ Redis connection error: {e}")
        return False

def test_celery_config():
    """Test Celery configuration"""
    print("\n⚙️  Testing Celery Configuration...")
    
    try:
        # Create Celery instance
        celery_app = Celery(
            'voice_clone_test',
            broker='redis://localhost:6379/0',
            backend='redis://localhost:6379/0'
        )
        
        # Configure Celery
        celery_app.conf.update(
            task_serializer='json',
            accept_content=['json'],
            result_serializer='json',
            timezone='UTC',
            enable_utc=True,
        )
        
        print("✅ Celery configured successfully")
        print(f"   Broker: {celery_app.conf.broker_url}")
        print(f"   Backend: {celery_app.conf.result_backend}")
        
        return celery_app
    except Exception as e:
        print(f"❌ Celery configuration error: {e}")
        return None

def create_test_task(celery_app):
    """Create a simple test task"""
    print("\n📝 Creating Test Task...")
    
    @celery_app.task(bind=True)
    def echo_test_task(self, message="Hello from Celery!"):
        """Simple echo task for testing"""
        print(f"Task {self.request.id} started with message: {message}")
        
        # Simulate some work
        for i in range(5):
            time.sleep(0.5)
            self.update_state(
                state='PROGRESS',
                meta={'progress': i * 20, 'step': f'Processing step {i+1}/5'}
            )
            print(f"Task {self.request.id}: Step {i+1}/5 completed")
        
        result = {
            'message': f"Echo: {message}",
            'task_id': self.request.id,
            'steps_completed': 5,
            'status': 'completed'
        }
        
        print(f"Task {self.request.id} completed successfully")
        return result
    
    print("✅ Test task created")
    return echo_test_task

def test_task_execution(celery_app, echo_task):
    """Test task execution (without worker)"""
    print("\n🚀 Testing Task Queue (requires running worker)...")
    
    try:
        # Try to queue a task
        result = echo_task.delay("Test message from integration test")
        
        print(f"✅ Task queued successfully")
        print(f"   Task ID: {result.id}")
        print(f"   Task State: {result.state}")
        
        # Check if task is in pending state (normal when no worker is running)
        if result.state == 'PENDING':
            print("⚠️  Task is pending - this is normal if no Celery worker is running")
            print("   To run a worker, use: celery -A app.tasks.celery_app worker --loglevel=info")
        
        return True
        
    except Exception as e:
        print(f"❌ Task queueing error: {e}")
        return False

def test_worker_inspection():
    """Test worker inspection (if workers are running)"""
    print("\n👥 Testing Worker Inspection...")
    
    try:
        celery_app = Celery(
            'voice_clone_test',
            broker='redis://localhost:6379/0',
            backend='redis://localhost:6379/0'
        )
        
        inspect = celery_app.control.inspect()
        active_workers = inspect.active()
        
        if active_workers:
            print(f"✅ Found {len(active_workers)} active workers:")
            for worker_name in active_workers.keys():
                print(f"   - {worker_name}")
        else:
            print("⚠️  No active workers found")
            print("   This is normal if no Celery workers are running")
        
        return True
        
    except Exception as e:
        print(f"❌ Worker inspection error: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 Stage 4 - Celery + Redis Integration Test")
    print("=" * 50)
    
    # Test Redis
    redis_ok = test_redis_connection()
    
    # Test Celery configuration
    celery_app = test_celery_config()
    
    if celery_app:
        # Create test task
        echo_task = create_test_task(celery_app)
        
        # Test task queueing
        task_ok = test_task_execution(celery_app, echo_task)
        
        # Test worker inspection
        worker_ok = test_worker_inspection()
    else:
        task_ok = False
        worker_ok = False
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 Test Summary:")
    print(f"   Redis Connection: {'✅ PASS' if redis_ok else '❌ FAIL'}")
    print(f"   Celery Config: {'✅ PASS' if celery_app else '❌ FAIL'}")
    print(f"   Task Queueing: {'✅ PASS' if task_ok else '❌ FAIL'}")
    print(f"   Worker Inspection: {'✅ PASS' if worker_ok else '❌ FAIL'}")
    
    if redis_ok and celery_app and task_ok:
        print("\n🎯 Stage 4 - Celery + Redis Integration: ✅ READY")
        print("   Next steps:")
        print("   1. Start a Celery worker: celery -A app.tasks.celery_app worker --loglevel=info")
        print("   2. Test worker endpoints via Flask API")
        print("   3. Move to Stage 5 - Zyphra service wrapper")
    else:
        print("\n❌ Some tests failed. Please fix the issues before proceeding.")

if __name__ == "__main__":
    main()

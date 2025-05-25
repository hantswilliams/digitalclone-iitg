#!/usr/bin/env python3
"""
Simple test script to verify authentication endpoints
"""
import requests
import json
import sys
from datetime import datetime


class AuthTester:
    def __init__(self, base_url="http://localhost:5000"):
        self.base_url = base_url
        self.session = requests.Session()
        self.access_token = None
        self.refresh_token = None
    
    def test_registration(self):
        """Test user registration"""
        print("🧪 Testing user registration...")
        
        user_data = {
            "email": f"test_{datetime.now().strftime('%Y%m%d_%H%M%S')}@example.com",
            "username": f"testuser_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "password": "TestPass123",
            "confirm_password": "TestPass123",
            "first_name": "Test",
            "last_name": "User",
            "department": "Computer Science",
            "title": "Test Professor",
            "role": "faculty"
        }
        
        try:
            response = self.session.post(
                f"{self.base_url}/api/auth/register",
                json=user_data,
                headers={'Content-Type': 'application/json'}
            )
            
            if response.status_code == 201:
                data = response.json()
                self.access_token = data.get('access_token')
                self.refresh_token = data.get('refresh_token')
                print(f"✅ Registration successful! User ID: {data['user']['id']}")
                return True, user_data['email']
            else:
                print(f"❌ Registration failed: {response.status_code} - {response.text}")
                return False, None
                
        except Exception as e:
            print(f"❌ Registration error: {str(e)}")
            return False, None
    
    def test_login(self, email, password="TestPass123"):
        """Test user login"""
        print("🧪 Testing user login...")
        
        login_data = {
            "email": email,
            "password": password,
            "remember_me": False
        }
        
        try:
            response = self.session.post(
                f"{self.base_url}/api/auth/login",
                json=login_data,
                headers={'Content-Type': 'application/json'}
            )
            
            if response.status_code == 200:
                data = response.json()
                self.access_token = data.get('access_token')
                self.refresh_token = data.get('refresh_token')
                print(f"✅ Login successful! Token expires in: {data.get('expires_in')} seconds")
                return True
            else:
                print(f"❌ Login failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Login error: {str(e)}")
            return False
    
    def test_profile(self):
        """Test getting user profile"""
        print("🧪 Testing profile retrieval...")
        
        if not self.access_token:
            print("❌ No access token available")
            return False
        
        try:
            response = self.session.get(
                f"{self.base_url}/api/auth/profile",
                headers={
                    'Authorization': f'Bearer {self.access_token}',
                    'Content-Type': 'application/json'
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Profile retrieved! Username: {data['username']}, Role: {data['role']}")
                return True
            else:
                print(f"❌ Profile retrieval failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Profile error: {str(e)}")
            return False
    
    def test_token_refresh(self):
        """Test token refresh"""
        print("🧪 Testing token refresh...")
        
        if not self.refresh_token:
            print("❌ No refresh token available")
            return False
        
        try:
            response = self.session.post(
                f"{self.base_url}/api/auth/refresh",
                headers={
                    'Authorization': f'Bearer {self.refresh_token}',
                    'Content-Type': 'application/json'
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                self.access_token = data.get('access_token')
                print(f"✅ Token refresh successful! New token expires in: {data.get('expires_in')} seconds")
                return True
            else:
                print(f"❌ Token refresh failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Token refresh error: {str(e)}")
            return False
    
    def test_logout(self):
        """Test user logout"""
        print("🧪 Testing user logout...")
        
        if not self.access_token:
            print("❌ No access token available")
            return False
        
        try:
            response = self.session.post(
                f"{self.base_url}/api/auth/logout",
                headers={
                    'Authorization': f'Bearer {self.access_token}',
                    'Content-Type': 'application/json'
                }
            )
            
            if response.status_code == 200:
                print("✅ Logout successful!")
                self.access_token = None
                self.refresh_token = None
                return True
            else:
                print(f"❌ Logout failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Logout error: {str(e)}")
            return False
    
    def test_health_check(self):
        """Test health check endpoint"""
        print("🧪 Testing health check...")
        
        try:
            response = self.session.get(f"{self.base_url}/health")
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Health check passed! Service: {data.get('service')}")
                return True
            else:
                print(f"❌ Health check failed: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Health check error: {str(e)}")
            return False
    
    def run_all_tests(self):
        """Run all authentication tests"""
        print("🚀 Starting authentication tests...\n")
        
        # Test health check first
        if not self.test_health_check():
            print("❌ Server appears to be down. Stopping tests.")
            return False
        
        print()
        
        # Test registration
        success, email = self.test_registration()
        if not success:
            print("❌ Registration failed. Stopping tests.")
            return False
        
        print()
        
        # Test profile with registration token
        self.test_profile()
        
        print()
        
        # Test logout
        self.test_logout()
        
        print()
        
        # Test login with created user
        if not self.test_login(email):
            print("❌ Login failed. Stopping tests.")
            return False
        
        print()
        
        # Test token refresh
        self.test_token_refresh()
        
        print()
        
        # Final profile test
        self.test_profile()
        
        print()
        
        # Final logout
        self.test_logout()
        
        print("\n🎉 All tests completed!")
        return True


if __name__ == "__main__":
    base_url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:5000"
    
    tester = AuthTester(base_url)
    success = tester.run_all_tests()
    
    sys.exit(0 if success else 1)

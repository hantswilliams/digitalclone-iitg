#!/usr/bin/env python3
"""
Comprehensive test script for asset management endpoints
"""
import requests
import json
import sys
import os
import tempfile
from datetime import datetime
from pathlib import Path


class AssetTester:
    def __init__(self, base_url="http://localhost:5001"):
        self.base_url = base_url
        self.session = requests.Session()
        self.access_token = None
        self.refresh_token = None
        self.test_assets = []
    
    def set_auth_token(self, token):
        """Set authentication token"""
        self.access_token = token
        self.session.headers.update({'Authorization': f'Bearer {token}'})
    
    def register_and_login(self):
        """Register and login a test user"""
        print("🔐 Setting up test user...")
        
        # Registration
        user_data = {
            "email": f"assettest_{datetime.now().strftime('%Y%m%d_%H%M%S')}@example.com",
            "username": f"assetuser_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "password": "TestPass123",
            "confirm_password": "TestPass123",
            "first_name": "Asset",
            "last_name": "Tester",
            "department": "Computer Science",
            "title": "Test User",
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
                self.set_auth_token(self.access_token)
                print(f"✅ Test user created and logged in!")
                return True
            else:
                print(f"❌ User setup failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Error during setup: {str(e)}")
            return False
    
    def create_test_files(self):
        """Create temporary test files for upload"""
        test_files = {}
        
        # Create test image file (PNG)
        try:
            import PIL.Image
            img = PIL.Image.new('RGB', (100, 100), color='red')
            img_file = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
            img.save(img_file.name, 'PNG')
            test_files['portrait'] = {
                'path': img_file.name,
                'mime_type': 'image/png',
                'asset_type': 'portrait'
            }
        except ImportError:
            # Create a simple binary file as fallback
            img_file = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
            img_file.write(b'\x89PNG\r\n\x1a\n' + b'test_image_data' * 100)
            img_file.close()
            test_files['portrait'] = {
                'path': img_file.name,
                'mime_type': 'image/png',
                'asset_type': 'portrait'
            }
        
        # Create test audio file (WAV)
        audio_file = tempfile.NamedTemporaryFile(suffix='.wav', delete=False)
        # Simple WAV header + data
        wav_header = b'RIFF' + b'\x24\x08\x00\x00' + b'WAVE' + b'fmt ' + b'\x10\x00\x00\x00'
        wav_header += b'\x01\x00\x01\x00\x44\xac\x00\x00\x88\x58\x01\x00\x02\x00\x10\x00'
        wav_header += b'data' + b'\x00\x08\x00\x00'
        wav_data = b'\x00\x00' * 1024  # Silent audio data
        audio_file.write(wav_header + wav_data)
        audio_file.close()
        test_files['voice_sample'] = {
            'path': audio_file.name,
            'mime_type': 'audio/wav',
            'asset_type': 'voice_sample'
        }
        
        # Create test script file
        script_file = tempfile.NamedTemporaryFile(suffix='.txt', delete=False, mode='w')
        script_file.write("This is a test script for the talking head lecturer.\n")
        script_file.write("It contains sample text that will be converted to speech.\n")
        script_file.close()
        test_files['script'] = {
            'path': script_file.name,
            'mime_type': 'text/plain',
            'asset_type': 'script'
        }
        
        return test_files
    
    def cleanup_test_files(self, test_files):
        """Clean up temporary test files"""
        for file_info in test_files.values():
            try:
                os.unlink(file_info['path'])
            except OSError:
                pass
    
    def test_list_assets_empty(self):
        """Test listing assets when none exist"""
        print("📋 Testing empty asset list...")
        
        try:
            response = self.session.get(f"{self.base_url}/api/assets/")
            
            if response.status_code == 200:
                data = response.json()
                assert 'assets' in data
                assert 'pagination' in data
                assert len(data['assets']) == 0
                print(f"✅ Empty asset list retrieved successfully")
                return True
            else:
                print(f"❌ List assets failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Error listing assets: {str(e)}")
            return False
    
    def test_upload_asset(self, file_info):
        """Test asset upload"""
        asset_type = file_info['asset_type']
        file_path = file_info['path']
        
        print(f"📤 Testing {asset_type} upload...")
        
        try:
            with open(file_path, 'rb') as f:
                files = {'file': (os.path.basename(file_path), f, file_info['mime_type'])}
                data = {
                    'asset_type': asset_type,
                    'description': f'Test {asset_type} file'
                }
                
                response = self.session.post(
                    f"{self.base_url}/api/assets/upload",
                    files=files,
                    data=data
                )
            
            if response.status_code == 201:
                result = response.json()
                asset = result['asset']
                self.test_assets.append(asset['id'])
                print(f"✅ {asset_type} uploaded successfully! Asset ID: {asset['id']}")
                print(f"   Filename: {asset['filename']}")
                print(f"   File size: {asset['file_size']} bytes")
                print(f"   Status: {asset['status']}")
                return True, asset['id']
            else:
                print(f"❌ {asset_type} upload failed: {response.status_code} - {response.text}")
                return False, None
                
        except Exception as e:
            print(f"❌ Error uploading {asset_type}: {str(e)}")
            return False, None
    
    def test_presigned_upload(self, file_info):
        """Test presigned URL upload"""
        asset_type = file_info['asset_type']
        file_path = file_info['path']
        file_size = os.path.getsize(file_path)
        
        print(f"🔗 Testing presigned upload for {asset_type}...")
        
        try:
            # Step 1: Request presigned URL
            request_data = {
                'filename': os.path.basename(file_path),
                'asset_type': asset_type,
                'file_size': file_size,
                'content_type': file_info['mime_type']
            }
            
            response = self.session.post(
                f"{self.base_url}/api/assets/presigned-upload",
                json=request_data,
                headers={'Content-Type': 'application/json'}
            )
            
            if response.status_code != 200:
                print(f"❌ Presigned URL request failed: {response.status_code} - {response.text}")
                return False, None
            
            presigned_data = response.json()
            upload_url = presigned_data['upload_url']
            asset_id = presigned_data['asset_id']
            
            print(f"   Got presigned URL for asset {asset_id}")
            
            # Step 2: Upload file to presigned URL
            with open(file_path, 'rb') as f:
                upload_response = requests.put(
                    upload_url,
                    data=f,
                    headers={'Content-Type': file_info['mime_type']}
                )
            
            if upload_response.status_code not in [200, 204]:
                print(f"❌ File upload to presigned URL failed: {upload_response.status_code}")
                return False, None
            
            print(f"   File uploaded to storage successfully")
            
            # Step 3: Confirm upload
            confirm_response = self.session.post(
                f"{self.base_url}/api/assets/{asset_id}/confirm-upload"
            )
            
            if confirm_response.status_code == 200:
                result = confirm_response.json()
                asset = result['asset']
                self.test_assets.append(asset['id'])
                print(f"✅ Presigned upload confirmed! Asset ID: {asset['id']}")
                return True, asset['id']
            else:
                print(f"❌ Upload confirmation failed: {confirm_response.status_code} - {confirm_response.text}")
                return False, None
                
        except Exception as e:
            print(f"❌ Error in presigned upload: {str(e)}")
            return False, None
    
    def test_get_asset(self, asset_id):
        """Test getting asset details"""
        print(f"📄 Testing get asset {asset_id}...")
        
        try:
            response = self.session.get(f"{self.base_url}/api/assets/{asset_id}")
            
            if response.status_code == 200:
                data = response.json()
                asset = data['asset']
                print(f"✅ Asset details retrieved successfully")
                print(f"   ID: {asset['id']}")
                print(f"   Filename: {asset['filename']}")
                print(f"   Type: {asset['asset_type']}")
                print(f"   Status: {asset['status']}")
                if 'download_url' in asset:
                    print(f"   Download URL available: {'Yes' if asset['download_url'] else 'No'}")
                return True
            else:
                print(f"❌ Get asset failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Error getting asset: {str(e)}")
            return False
    
    def test_download_asset(self, asset_id):
        """Test getting download URL for asset"""
        print(f"⬇️ Testing download URL for asset {asset_id}...")
        
        try:
            response = self.session.get(f"{self.base_url}/api/assets/{asset_id}/download")
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Download URL generated successfully")
                print(f"   Filename: {data['filename']}")
                print(f"   Expires in: {data['expires_in']} seconds")
                return True
            else:
                print(f"❌ Download URL failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Error getting download URL: {str(e)}")
            return False
    
    def test_list_assets_with_data(self):
        """Test listing assets when some exist"""
        print("📋 Testing asset list with data...")
        
        try:
            response = self.session.get(f"{self.base_url}/api/assets/")
            
            if response.status_code == 200:
                data = response.json()
                assets = data['assets']
                pagination = data['pagination']
                
                print(f"✅ Asset list retrieved successfully")
                print(f"   Total assets: {pagination['total']}")
                print(f"   Current page: {pagination['page']}")
                
                for asset in assets:
                    print(f"   - {asset['filename']} ({asset['asset_type']}) - {asset['status']}")
                
                return True
            else:
                print(f"❌ List assets failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Error listing assets: {str(e)}")
            return False
    
    def test_list_assets_filtered(self):
        """Test listing assets with filters"""
        print("📋 Testing filtered asset list...")
        
        try:
            # Test filtering by asset type
            response = self.session.get(f"{self.base_url}/api/assets/?asset_type=portrait")
            
            if response.status_code == 200:
                data = response.json()
                assets = data['assets']
                
                # Check that all returned assets are portraits
                for asset in assets:
                    if asset['asset_type'] != 'portrait':
                        print(f"❌ Filter failed: found non-portrait asset {asset['id']}")
                        return False
                
                print(f"✅ Asset filtering works correctly")
                print(f"   Found {len(assets)} portrait assets")
                return True
            else:
                print(f"❌ Filtered list failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Error in filtered listing: {str(e)}")
            return False
    
    def test_delete_asset(self, asset_id):
        """Test deleting an asset"""
        print(f"🗑️ Testing delete asset {asset_id}...")
        
        try:
            response = self.session.delete(f"{self.base_url}/api/assets/{asset_id}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Asset deleted successfully")
                
                # Remove from our tracking list
                if asset_id in self.test_assets:
                    self.test_assets.remove(asset_id)
                
                return True
            else:
                print(f"❌ Delete asset failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Error deleting asset: {str(e)}")
            return False
    
    def test_get_deleted_asset(self, asset_id):
        """Test trying to get a deleted asset"""
        print(f"👻 Testing access to deleted asset {asset_id}...")
        
        try:
            response = self.session.get(f"{self.base_url}/api/assets/{asset_id}")
            
            if response.status_code == 404:
                print(f"✅ Deleted asset correctly returns 404")
                return True
            else:
                print(f"❌ Deleted asset still accessible: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Error checking deleted asset: {str(e)}")
            return False
    
    def run_all_tests(self):
        """Run all asset management tests"""
        print("🚀 Starting Asset Management API Tests")
        print("=" * 50)
        
        # Setup
        if not self.register_and_login():
            return False
        
        test_files = self.create_test_files()
        results = []
        
        try:
            # Test 1: Empty asset list
            results.append(self.test_list_assets_empty())
            
            # Test 2: Upload assets (traditional upload)
            uploaded_assets = []
            for asset_type, file_info in test_files.items():
                success, asset_id = self.test_upload_asset(file_info)
                results.append(success)
                if success:
                    uploaded_assets.append(asset_id)
            
            # Test 3: Get asset details
            for asset_id in uploaded_assets[:2]:  # Test first 2 assets
                results.append(self.test_get_asset(asset_id))
                results.append(self.test_download_asset(asset_id))
            
            # Test 4: Presigned upload
            if len(test_files) > 0:
                file_info = list(test_files.values())[0]  # Use first file type
                success, asset_id = self.test_presigned_upload(file_info)
                results.append(success)
                if success:
                    uploaded_assets.append(asset_id)
            
            # Test 5: List assets with data
            results.append(self.test_list_assets_with_data())
            
            # Test 6: Filtered listing
            results.append(self.test_list_assets_filtered())
            
            # Test 7: Delete assets
            if uploaded_assets:
                asset_to_delete = uploaded_assets[0]
                results.append(self.test_delete_asset(asset_to_delete))
                results.append(self.test_get_deleted_asset(asset_to_delete))
            
            # Cleanup remaining assets
            for asset_id in self.test_assets:
                self.test_delete_asset(asset_id)
            
        finally:
            self.cleanup_test_files(test_files)
        
        # Results summary
        print("\n" + "=" * 50)
        print("📊 Test Results Summary")
        print("=" * 50)
        
        passed = sum(results)
        total = len(results)
        
        print(f"Passed: {passed}/{total}")
        print(f"Success Rate: {(passed/total)*100:.1f}%")
        
        if passed == total:
            print("🎉 All tests passed!")
            return True
        else:
            print(f"⚠️ {total-passed} tests failed")
            return False


def main():
    """Main test runner"""
    if len(sys.argv) > 1:
        base_url = sys.argv[1]
    else:
        base_url = "http://localhost:5001"
    
    print(f"Testing asset endpoints at: {base_url}")
    
    tester = AssetTester(base_url)
    success = tester.run_all_tests()
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()

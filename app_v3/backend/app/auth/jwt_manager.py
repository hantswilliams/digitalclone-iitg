"""
JWT token management and blocklist functionality
"""
from datetime import datetime, timezone, timedelta
from ..extensions import redis_client
import threading


class JWTBlocklist:
    """Manage JWT token blocklist using Redis or in-memory fallback"""
    
    # In-memory fallback storage (for development without Redis)
    _memory_store = {}
    _lock = threading.Lock()
    
    @classmethod
    def _get_store_key(cls, key_type, identifier):
        """Generate consistent store keys"""
        return f"{key_type}:{identifier}"
    
    @classmethod
    def _is_expired(cls, expires_at):
        """Check if a timestamp has expired"""
        if isinstance(expires_at, datetime):
            return datetime.now(timezone.utc) > expires_at
        return False
    
    @classmethod
    def _clean_expired_tokens(cls):
        """Clean expired tokens from memory store"""
        current_time = datetime.now(timezone.utc)
        expired_keys = []
        
        for key, data in cls._memory_store.items():
            if isinstance(data, dict) and 'expires_at' in data:
                if current_time > data['expires_at']:
                    expired_keys.append(key)
        
        for key in expired_keys:
            del cls._memory_store[key]
    
    @staticmethod
    def add_token_to_blocklist(jti, expires_at):
        """Add a JWT token to the blocklist"""
        # Calculate TTL in seconds until token expires
        if isinstance(expires_at, datetime):
            ttl = int((expires_at - datetime.now(timezone.utc)).total_seconds())
        else:
            ttl = expires_at
            expires_at = datetime.now(timezone.utc).timestamp() + ttl
        
        # Only store if TTL is positive (token hasn't expired yet)
        if ttl > 0:
            if redis_client:
                try:
                    redis_client.setex(f"blocked_token:{jti}", ttl, "1")
                    return
                except Exception:
                    pass
            
            # Fallback to memory store
            with JWTBlocklist._lock:
                JWTBlocklist._clean_expired_tokens()
                key = JWTBlocklist._get_store_key("blocked_token", jti)
                JWTBlocklist._memory_store[key] = {
                    'value': "1",
                    'expires_at': expires_at if isinstance(expires_at, datetime) else datetime.fromtimestamp(expires_at, timezone.utc)
                }
    
    @staticmethod
    def is_token_revoked(jti):
        """Check if a JWT token is in the blocklist"""
        if redis_client:
            try:
                return redis_client.exists(f"blocked_token:{jti}") > 0
            except Exception:
                pass
        
        # Fallback to memory store
        with JWTBlocklist._lock:
            JWTBlocklist._clean_expired_tokens()
            key = JWTBlocklist._get_store_key("blocked_token", jti)
            data = JWTBlocklist._memory_store.get(key)
            return data is not None and not JWTBlocklist._is_expired(data.get('expires_at'))
    
    @staticmethod
    def revoke_all_user_tokens(user_id):
        """Revoke all tokens for a specific user (for security purposes)"""
        expires_at = datetime.now(timezone.utc) + timedelta(days=30)
        
        if redis_client:
            try:
                redis_client.setex(f"user_revoked:{user_id}", 86400 * 30, "1")  # 30 days
                return
            except Exception:
                pass
        
        # Fallback to memory store
        with JWTBlocklist._lock:
            key = JWTBlocklist._get_store_key("user_revoked", user_id)
            JWTBlocklist._memory_store[key] = {
                'value': "1",
                'expires_at': expires_at
            }
    
    @staticmethod
    def is_user_tokens_revoked(user_id):
        """Check if all tokens for a user have been revoked"""
        if redis_client:
            try:
                return redis_client.exists(f"user_revoked:{user_id}") > 0
            except Exception:
                pass
        
        # Fallback to memory store
        with JWTBlocklist._lock:
            JWTBlocklist._clean_expired_tokens()
            key = JWTBlocklist._get_store_key("user_revoked", user_id)
            data = JWTBlocklist._memory_store.get(key)
            return data is not None and not JWTBlocklist._is_expired(data.get('expires_at'))
    
    @staticmethod
    def clear_user_token_revocation(user_id):
        """Clear the user token revocation flag"""
        if redis_client:
            try:
                redis_client.delete(f"user_revoked:{user_id}")
                return
            except Exception:
                pass
        
        # Fallback to memory store
        with JWTBlocklist._lock:
            key = JWTBlocklist._get_store_key("user_revoked", user_id)
            if key in JWTBlocklist._memory_store:
                del JWTBlocklist._memory_store[key]

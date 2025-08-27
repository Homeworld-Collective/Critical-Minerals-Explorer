from http.server import BaseHTTPRequestHandler
import json
import os
import time
from datetime import datetime, timedelta
from urllib.parse import parse_qs, urlparse

# Try to import Vercel KV, fall back to dict if not available
HAS_KV = False
kv = None

try:
    from vercel import kv
    HAS_KV = True
except ImportError:
    print("Warning: Vercel KV not available, using in-memory storage")

class handler(BaseHTTPRequestHandler):
    # Configuration
    MAX_COMMENTS_PER_HOUR = int(os.getenv('MAX_COMMENTS_PER_HOUR', '3'))
    COMMENT_MAX_LENGTH = int(os.getenv('COMMENT_MAX_LENGTH', '500'))
    ADMIN_SECRET = os.getenv('ADMIN_SECRET', 'your_secure_admin_secret_here')
    
    # In-memory storage fallback (for development)
    _memory_storage = {}
    
    def do_GET(self):
        self.send_cors_headers()
        
        # Parse query parameters
        parsed_path = urlparse(self.path)
        query_params = parse_qs(parsed_path.query)
        
        try:
            metal = query_params.get('metal', [None])[0]
            if not metal:
                self.send_json_response({'error': 'Metal parameter is required'}, 400)
                return
            
            # Load comments
            comments = self.load_comments()
            
            # Filter by metal and only return approved comments
            metal_comments = [
                comment for comment in comments.get(metal.lower(), [])
                if comment.get('approved', False)
            ]
            
            self.send_json_response(metal_comments)
            
        except Exception as e:
            print(f"Error handling GET comments: {e}")
            self.send_json_response({'error': 'Internal server error'}, 500)
    
    def do_POST(self):
        self.send_cors_headers()
        
        try:
            # Read request body
            content_length = int(self.headers.get('content-length', 0))
            post_data = self.rfile.read(content_length)
            
            try:
                comment_data = json.loads(post_data.decode('utf-8'))
            except json.JSONDecodeError:
                self.send_json_response({'error': 'Invalid JSON'}, 400)
                return
            
            # Validate comment data
            if not self.validate_comment(comment_data):
                self.send_json_response({'error': 'Invalid comment data'}, 400)
                return
            
            # Sanitize comment
            sanitized_comment = self.sanitize_comment(comment_data)
            
            # Get client IP
            client_ip = self.get_client_ip()
            sanitized_comment['ip'] = client_ip
            
            # Load existing comments
            comments = self.load_comments()
            metal = sanitized_comment['metalName']
            
            if metal not in comments:
                comments[metal] = []
            
            # Check rate limiting
            if self.check_rate_limit(comments[metal], client_ip):
                self.send_json_response(
                    {'error': f'Too many comments. Please wait before commenting again. (Limit: {self.MAX_COMMENTS_PER_HOUR} per hour)'}, 
                    429
                )
                return
            
            # Add comment
            comments[metal].append(sanitized_comment)
            
            # Save comments
            self.save_comments(comments)
            
            self.send_json_response({
                'success': True,
                'message': 'Comment submitted successfully! It will appear after moderation.',
                'id': sanitized_comment['id']
            }, 201)
            
        except Exception as e:
            print(f"Error handling POST comment: {e}")
            self.send_json_response({'error': 'Internal server error'}, 500)
    
    def do_OPTIONS(self):
        self.send_cors_headers()
        self.send_response(200)
        self.end_headers()
    
    def send_cors_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
    
    def validate_comment(self, comment):
        required = ['selectedText', 'comment', 'metalName', 'context']
        return all(
            field in comment and 
            str(comment[field]).strip() 
            for field in required
        )
    
    def sanitize_comment(self, comment):
        return {
            'id': int(time.time() * 1000) + int(time.time() * 1000000) % 1000,
            'selectedText': str(comment['selectedText']).strip()[:self.COMMENT_MAX_LENGTH],
            'comment': str(comment['comment']).strip()[:self.COMMENT_MAX_LENGTH],
            'metalName': str(comment['metalName']).lower().strip(),
            'context': {
                'sectionTitle': str(comment.get('context', {}).get('sectionTitle', 'Unknown Section')).strip()[:200],
                'selectedText': str(comment['selectedText']).strip()[:self.COMMENT_MAX_LENGTH]
            },
            'timestamp': datetime.now().isoformat(),
            'approved': False,
            'ip': None
        }
    
    def get_client_ip(self):
        # Try to get real IP from headers
        forwarded = self.headers.get('x-forwarded-for')
        if forwarded:
            return forwarded.split(',')[0].strip()
        return getattr(self, 'client_address', ['unknown'])[0]
    
    def check_rate_limit(self, metal_comments, client_ip):
        if not client_ip:
            return False
        
        # Count comments from this IP in the last hour
        one_hour_ago = datetime.now() - timedelta(hours=1)
        recent_comments = [
            c for c in metal_comments 
            if c.get('ip') == client_ip and 
               datetime.fromisoformat(c.get('timestamp', '1970-01-01')) > one_hour_ago
        ]
        
        return len(recent_comments) >= self.MAX_COMMENTS_PER_HOUR
    
    def load_comments(self):
        try:
            if HAS_KV:
                # Use Vercel KV in production
                return kv.get('comments') or {}
            else:
                # Use in-memory storage for development
                return self._memory_storage
        except Exception as e:
            print(f"Error loading comments: {e}")
            return {}
    
    def save_comments(self, comments):
        try:
            if HAS_KV:
                # Use Vercel KV in production
                kv.set('comments', comments)
            else:
                # Use in-memory storage for development
                self._memory_storage = comments
        except Exception as e:
            print(f"Error saving comments: {e}")
    
    def send_json_response(self, data, status_code=200):
        self.send_response(status_code)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode('utf-8'))
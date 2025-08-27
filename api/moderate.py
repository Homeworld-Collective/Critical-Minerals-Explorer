from http.server import BaseHTTPRequestHandler
import json
import os
from urllib.parse import parse_qs, urlparse

# Try to import Vercel KV, fall back to dict if not available
try:
    from vercel_kv import kv
    HAS_KV = True
except ImportError:
    HAS_KV = False
    print("Warning: Vercel KV not available, using in-memory storage")

class handler(BaseHTTPRequestHandler):
    ADMIN_SECRET = os.getenv('ADMIN_SECRET', 'your_secure_admin_secret_here')
    
    # In-memory storage fallback (for development)
    _memory_storage = {}
    
    def do_GET(self):
        self.send_cors_headers()
        
        try:
            if not self.check_admin_auth():
                self.send_json_response({'error': 'Unauthorized'}, 401)
                return
            
            # Load all comments
            comments = self.load_comments()
            
            # Get all unapproved comments from all metals
            pending_comments = []
            for metal, metal_comments in comments.items():
                for comment in metal_comments:
                    if not comment.get('approved', False):
                        pending_comments.append(comment)
            
            # Sort by timestamp (newest first)
            pending_comments.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
            
            self.send_json_response(pending_comments)
            
        except Exception as e:
            print(f"Error handling GET moderate: {e}")
            self.send_json_response({'error': 'Internal server error'}, 500)
    
    def do_POST(self):
        self.send_cors_headers()
        
        try:
            if not self.check_admin_auth():
                self.send_json_response({'error': 'Unauthorized'}, 401)
                return
            
            # Read request body
            content_length = int(self.headers.get('content-length', 0))
            post_data = self.rfile.read(content_length)
            
            try:
                mod_data = json.loads(post_data.decode('utf-8'))
            except json.JSONDecodeError:
                self.send_json_response({'error': 'Invalid JSON'}, 400)
                return
            
            comment_id = mod_data.get('commentId')
            metal_name = mod_data.get('metalName')
            action = mod_data.get('action')  # 'approve' or 'reject'
            
            if not all([comment_id, metal_name, action]):
                self.send_json_response({'error': 'Missing required fields'}, 400)
                return
            
            if action not in ['approve', 'reject']:
                self.send_json_response({'error': 'Invalid action'}, 400)
                return
            
            # Load comments
            comments = self.load_comments()
            
            if metal_name not in comments:
                self.send_json_response({'error': 'Metal not found'}, 404)
                return
            
            # Find and modify the comment
            comment_found = False
            for i, comment in enumerate(comments[metal_name]):
                if str(comment.get('id')) == str(comment_id):
                    if action == 'approve':
                        comments[metal_name][i]['approved'] = True
                    else:  # reject
                        comments[metal_name].pop(i)  # Remove rejected comments
                    comment_found = True
                    break
            
            if not comment_found:
                self.send_json_response({'error': 'Comment not found'}, 404)
                return
            
            # Save updated comments
            self.save_comments(comments)
            
            self.send_json_response({
                'success': True,
                'message': f'Comment {action}d successfully'
            })
            
        except Exception as e:
            print(f"Error handling POST moderate: {e}")
            self.send_json_response({'error': 'Internal server error'}, 500)
    
    def do_OPTIONS(self):
        self.send_cors_headers()
        self.send_response(200)
        self.end_headers()
    
    def send_cors_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
    
    def check_admin_auth(self):
        """Check if the request has valid admin authorization"""
        auth_header = self.headers.get('authorization', '')
        if not auth_header.startswith('Bearer '):
            return False
        
        provided_secret = auth_header[7:]  # Remove 'Bearer ' prefix
        return provided_secret == self.ADMIN_SECRET
    
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
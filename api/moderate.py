from http.server import BaseHTTPRequestHandler
import json
import os

# Configuration
ADMIN_SECRET = os.getenv('ADMIN_SECRET', 'your_secure_admin_secret_here')

# Try to import requests for Upstash REST API
HAS_REDIS = False
try:
    import requests
    REDIS_URL = os.getenv('KV_REST_API_URL')
    REDIS_TOKEN = os.getenv('KV_REST_API_TOKEN')
    
    if REDIS_URL and REDIS_TOKEN:
        HAS_REDIS = True
        print(f"Using Upstash Redis at {REDIS_URL}")
    else:
        print("Redis credentials not found in environment")
except ImportError:
    print("Warning: requests not available, using in-memory storage")

# In-memory storage fallback
_memory_storage = {}

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path.startswith('/api/comments/moderate'):
            # Check admin auth
            auth_header = self.headers.get('Authorization', '')
            if not auth_header.startswith('Bearer '):
                self.send_response(401)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({'error': 'Unauthorized'}).encode())
                return
            
            provided_secret = auth_header[7:]  # Remove 'Bearer ' prefix
            if provided_secret != ADMIN_SECRET:
                self.send_response(401)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({'error': 'Unauthorized'}).encode())
                return
            
            # Load all comments
            comments = load_comments()
            
            # Get all unapproved comments from all metals
            pending_comments = []
            for metal, metal_comments in comments.items():
                for comment in metal_comments:
                    if not comment.get('approved', False):
                        pending_comments.append(comment)
            
            # Sort by timestamp (newest first)
            pending_comments.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
            
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(pending_comments).encode())
    
    def do_POST(self):
        if self.path.startswith('/api/comments/moderate'):
            # Check admin auth
            auth_header = self.headers.get('Authorization', '')
            if not auth_header.startswith('Bearer '):
                self.send_response(401)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({'error': 'Unauthorized'}).encode())
                return
            
            provided_secret = auth_header[7:]  # Remove 'Bearer ' prefix
            if provided_secret != ADMIN_SECRET:
                self.send_response(401)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({'error': 'Unauthorized'}).encode())
                return
            
            # Read request body
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            
            try:
                mod_data = json.loads(post_data.decode('utf-8'))
            except json.JSONDecodeError:
                self.send_response(400)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({'error': 'Invalid JSON'}).encode())
                return
            
            comment_id = mod_data.get('commentId')
            metal_name = mod_data.get('metalName')
            action = mod_data.get('action')  # 'approve' or 'reject'
            
            if not all([comment_id, metal_name, action]):
                self.send_response(400)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({'error': 'Missing required fields'}).encode())
                return
            
            if action not in ['approve', 'reject']:
                self.send_response(400)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({'error': 'Invalid action'}).encode())
                return
            
            # Load comments
            comments = load_comments()
            
            if metal_name not in comments:
                self.send_response(404)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({'error': 'Metal not found'}).encode())
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
                self.send_response(404)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({'error': 'Comment not found'}).encode())
                return
            
            # Save updated comments
            save_comments(comments)
            
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({
                'success': True,
                'message': f'Comment {action}d successfully'
            }).encode())
    
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        self.end_headers()

def load_comments():
    """Load comments from Upstash Redis or memory"""
    global _memory_storage
    
    try:
        if HAS_REDIS:
            import requests
            url = f"{os.getenv('KV_REST_API_URL')}/get/comments"
            headers = {
                'Authorization': f"Bearer {os.getenv('KV_REST_API_TOKEN')}"
            }
            
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                data = response.json()
                result = data.get('result')
                if result:
                    return json.loads(result)
            return {}
        else:
            # Use in-memory storage for development
            return _memory_storage
    except Exception as e:
        print(f"Error loading comments: {e}")
        return {}

def save_comments(comments):
    """Save comments to Upstash Redis or memory"""
    global _memory_storage
    
    try:
        if HAS_REDIS:
            import requests
            url = f"{os.getenv('KV_REST_API_URL')}/set/comments"
            headers = {
                'Authorization': f"Bearer {os.getenv('KV_REST_API_TOKEN')}",
                'Content-Type': 'application/json'
            }
            
            # Send the JSON string directly as the body to Upstash
            response = requests.post(url, 
                                   data=json.dumps(comments),
                                   headers=headers)
            if response.status_code != 200:
                print(f"Failed to save comments: {response.text}")
        else:
            # Use in-memory storage for development
            _memory_storage = comments
    except Exception as e:
        print(f"Error saving comments: {e}")
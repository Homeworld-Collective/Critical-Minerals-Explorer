from http.server import BaseHTTPRequestHandler
import json
import os
import time
from datetime import datetime, timedelta

# Configuration
MAX_COMMENTS_PER_HOUR = int(os.getenv('MAX_COMMENTS_PER_HOUR', '3'))
COMMENT_MAX_LENGTH = int(os.getenv('COMMENT_MAX_LENGTH', '500'))

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
        if self.path.startswith('/api/comments'):
            # Parse query parameters
            from urllib.parse import urlparse, parse_qs
            parsed_path = urlparse(self.path)
            query_params = parse_qs(parsed_path.query)
            metal = query_params.get('metal', [None])[0]
            
            if not metal:
                self.send_response(400)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({'error': 'Metal parameter is required'}).encode())
                return
            
            # Load comments
            comments = load_comments()
            
            # Filter by metal and only return approved comments
            metal_comments = [
                comment for comment in comments.get(metal.lower(), [])
                if comment.get('approved', False)
            ]
            
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(metal_comments).encode())
    
    def do_POST(self):
        if self.path.startswith('/api/comments'):
            # Read request body
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            
            try:
                comment_data = json.loads(post_data.decode('utf-8'))
            except json.JSONDecodeError:
                self.send_response(400)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({'error': 'Invalid JSON'}).encode())
                return
            
            # Validate comment data
            if not validate_comment(comment_data):
                self.send_response(400)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({'error': 'Invalid comment data'}).encode())
                return
            
            # Sanitize comment
            sanitized_comment = sanitize_comment(comment_data)
            
            # Get client IP
            client_ip = self.headers.get('X-Forwarded-For', '').split(',')[0].strip() or 'unknown'
            sanitized_comment['ip'] = client_ip
            
            # Load existing comments
            comments = load_comments()
            metal = sanitized_comment['metalName']
            
            if metal not in comments:
                comments[metal] = []
            
            # Check rate limiting
            if check_rate_limit(comments[metal], client_ip):
                self.send_response(429)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({
                    'error': f'Too many comments. Please wait before commenting again. (Limit: {MAX_COMMENTS_PER_HOUR} per hour)'
                }).encode())
                return
            
            # Add comment
            comments[metal].append(sanitized_comment)
            
            # Save comments
            save_comments(comments)
            
            self.send_response(201)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({
                'success': True,
                'message': 'Comment submitted successfully! It will appear after moderation.',
                'id': sanitized_comment['id']
            }).encode())
    
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        self.end_headers()

def validate_comment(comment):
    required = ['selectedText', 'comment', 'metalName', 'context']
    return all(
        field in comment and 
        str(comment[field]).strip() 
        for field in required
    )

def sanitize_comment(comment):
    return {
        'id': int(time.time() * 1000) + int(time.time() * 1000000) % 1000,
        'selectedText': str(comment['selectedText']).strip()[:COMMENT_MAX_LENGTH],
        'comment': str(comment['comment']).strip()[:COMMENT_MAX_LENGTH],
        'metalName': str(comment['metalName']).lower().strip(),
        'context': {
            'sectionTitle': str(comment.get('context', {}).get('sectionTitle', 'Unknown Section')).strip()[:200],
            'selectedText': str(comment['selectedText']).strip()[:COMMENT_MAX_LENGTH]
        },
        'timestamp': datetime.now().isoformat(),
        'approved': False,
        'ip': None
    }

def check_rate_limit(metal_comments, client_ip):
    if not client_ip or client_ip == 'unknown':
        return False
    
    # Count comments from this IP in the last hour
    one_hour_ago = datetime.now() - timedelta(hours=1)
    recent_comments = [
        c for c in metal_comments 
        if c.get('ip') == client_ip and 
           datetime.fromisoformat(c.get('timestamp', '1970-01-01')) > one_hour_ago
    ]
    
    return len(recent_comments) >= MAX_COMMENTS_PER_HOUR

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
            
            # Upstash REST API expects an array format for SET command: [value]
            response = requests.post(url, json=[json.dumps(comments)], headers=headers)
            if response.status_code != 200:
                print(f"Failed to save comments: {response.text}")
        else:
            # Use in-memory storage for development
            _memory_storage = comments
    except Exception as e:
        print(f"Error saving comments: {e}")
#!/usr/bin/env python3
"""
Simple HTTP server for the Critical Mineral Explorer website.
This serves the website locally and handles CORS issues and comment API.
"""

import http.server
import socketserver
import os
import webbrowser
import json
import urllib.parse
import time
from pathlib import Path
from datetime import datetime, timedelta

# Try to import requests for Upstash Redis
try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    print("Warning: requests library not available. Install with: pip install requests")
    print("Will use local JSON storage only.")
    HAS_REQUESTS = False

# Load environment variables from .env file
def load_env_file():
    env_path = Path(__file__).parent / '.env'
    if env_path.exists():
        with open(env_path) as f:
            for line in f:
                if line.strip() and not line.startswith('#'):
                    key, value = line.strip().split('=', 1)
                    # Remove quotes if present
                    value = value.strip('"\'')
                    os.environ[key] = value

# Load .env file
load_env_file()

class CORSHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    # Configuration
    MAX_COMMENTS_PER_HOUR = 3
    COMMENT_MAX_LENGTH = 500
    
    def __init__(self, *args, **kwargs):
        # Load admin secret from environment
        self.admin_secret = os.getenv('ADMIN_SECRET', 'your_secure_admin_secret_here')
        print(f"Admin secret loaded: {self.admin_secret[:20]}...") # Debug print
        super().__init__(*args, **kwargs)
    
    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', '*')
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()
    
    def do_GET(self):
        # Handle API requests
        if self.path.startswith('/api/comments/moderate'):
            self.handle_get_moderate()
        elif self.path.startswith('/api/comments'):
            self.handle_get_comments()
        else:
            # Serve static files
            super().do_GET()
    
    def do_POST(self):
        # Handle API requests
        if self.path.startswith('/api/comments/moderate'):
            self.handle_post_moderate()
        elif self.path.startswith('/api/comments'):
            self.handle_post_comment()
        else:
            self.send_error(404)
    
    def handle_get_comments(self):
        try:
            # Parse query parameters
            parsed_path = urllib.parse.urlparse(self.path)
            query_params = urllib.parse.parse_qs(parsed_path.query)
            
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
    
    def handle_post_comment(self):
        try:
            # Read request body
            content_length = int(self.headers.get('Content-Length', 0))
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
        forwarded = self.headers.get('X-Forwarded-For')
        if forwarded:
            return forwarded.split(',')[0].strip()
        return self.client_address[0]
    
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
        """Load comments from Upstash Redis (same as production)"""
        try:
            if HAS_REQUESTS:
                redis_url = os.getenv('KV_REST_API_URL')
                redis_token = os.getenv('KV_REST_API_TOKEN')
                
                if redis_url and redis_token:
                    url = f"{redis_url}/get/comments"
                    headers = {
                        'Authorization': f"Bearer {redis_token}"
                    }
                    
                    response = requests.get(url, headers=headers)
                    if response.status_code == 200:
                        data = response.json()
                        result = data.get('result')
                        if result:
                            print("Loaded comments from Upstash Redis")
                            # Upstash should return a JSON string, parse it to dict
                            if isinstance(result, str):
                                try:
                                    return json.loads(result)
                                except json.JSONDecodeError:
                                    print("Failed to parse JSON from Upstash")
                                    return {}
                            # If it's already a dict, return it
                            return result if isinstance(result, dict) else {}
                        else:
                            print("No comments in Upstash Redis yet")
                            return {}
                    else:
                        print(f"Failed to load from Upstash: {response.status_code}")
                else:
                    print("Upstash Redis credentials not configured")
            else:
                print("requests library not available - cannot connect to Upstash")
        except Exception as e:
            print(f"Error loading comments: {e}")
        return {}
    
    def save_comments(self, comments):
        """Save comments to Upstash Redis (same as production)"""
        try:
            if HAS_REQUESTS:
                redis_url = os.getenv('KV_REST_API_URL')
                redis_token = os.getenv('KV_REST_API_TOKEN')
                
                if redis_url and redis_token:
                    url = f"{redis_url}/set/comments"
                    headers = {
                        'Authorization': f"Bearer {redis_token}",
                        'Content-Type': 'application/json'
                    }
                    
                    # For /set/key endpoint, send the JSON directly as the body
                    # Remove Content-Type header and send raw JSON string
                    headers_no_json = {
                        'Authorization': f"Bearer {redis_token}"
                    }
                    body = json.dumps(comments)
                    response = requests.post(url, 
                                           data=body,
                                           headers=headers_no_json)
                    if response.status_code == 200:
                        print("Saved comments to Upstash Redis")
                    else:
                        print(f"Failed to save to Upstash: {response.status_code}, {response.text}")
                else:
                    print("Upstash Redis credentials not configured")
            else:
                print("requests library not available - cannot save to Upstash")
        except Exception as e:
            print(f"Error saving comments: {e}")
    
    def send_json_response(self, data, status_code=200):
        self.send_response(status_code)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode('utf-8'))
    
    def check_admin_auth(self):
        """Check if the request has valid admin authorization"""
        auth_header = self.headers.get('Authorization', '')
        if not auth_header.startswith('Bearer '):
            return False
        
        provided_secret = auth_header[7:]  # Remove 'Bearer ' prefix
        return provided_secret == self.admin_secret
    
    def handle_get_moderate(self):
        """GET /api/comments/moderate - Get all pending comments for moderation"""
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
    
    def handle_post_moderate(self):
        """POST /api/comments/moderate - Approve or reject a comment"""
        try:
            if not self.check_admin_auth():
                self.send_json_response({'error': 'Unauthorized'}, 401)
                return
            
            # Read request body
            content_length = int(self.headers.get('Content-Length', 0))
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

def main():
    # Change to the directory containing the website files
    website_dir = Path(__file__).parent
    os.chdir(website_dir)
    
    PORT = 8080
    
    # Find an available port
    while True:
        try:
            with socketserver.TCPServer(("", PORT), CORSHTTPRequestHandler) as httpd:
                print(f"🌐 Critical Mineral Explorer server starting...")
                print(f"📍 Serving at: http://localhost:{PORT}")
                print(f"📁 Directory: {website_dir}")
                print(f"🚀 Opening browser...")
                
                # Open browser automatically
                webbrowser.open(f'http://localhost:{PORT}')
                
                print(f"✅ Server is running. Press Ctrl+C to stop.")
                httpd.serve_forever()
        except OSError as e:
            if "Address already in use" in str(e):
                PORT += 1
                if PORT > 8090:
                    print("❌ Could not find an available port")
                    return
            else:
                raise

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")
    except Exception as e:
        print(f"❌ Error: {e}")


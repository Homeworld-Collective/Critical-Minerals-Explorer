import json
import os
import time
from datetime import datetime, timedelta
from urllib.parse import parse_qs

# Try to import Redis client for Upstash
HAS_REDIS = False
redis_client = None

try:
    import redis
    # Use Upstash Redis from environment variables
    REDIS_URL = os.getenv('KV_REST_API_URL') or os.getenv('REDIS_URL')
    REDIS_TOKEN = os.getenv('KV_REST_API_TOKEN')
    
    if REDIS_URL and REDIS_TOKEN:
        # For REST API, we'll use requests instead
        import requests
        HAS_REDIS = True
        print("Using Upstash Redis REST API")
    else:
        print("Redis credentials not found in environment")
except ImportError:
    print("Warning: Redis not available, using in-memory storage")

# Configuration
MAX_COMMENTS_PER_HOUR = int(os.getenv('MAX_COMMENTS_PER_HOUR', '3'))
COMMENT_MAX_LENGTH = int(os.getenv('COMMENT_MAX_LENGTH', '500'))

# In-memory storage fallback (for development)
_memory_storage = {}

def handler(request, response):
    """Vercel serverless function handler"""
    # Set CORS headers
    response.headers = {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
        'Access-Control-Allow-Headers': 'Content-Type, Authorization',
        'Content-Type': 'application/json'
    }
    
    if request.method == 'OPTIONS':
        response.status_code = 200
        return ""
    
    try:
        if request.method == 'GET':
            # Parse query parameters
            query_params = dict(request.query_params)
            metal = query_params.get('metal')
            
            if not metal:
                response.status_code = 400
                return json.dumps({'error': 'Metal parameter is required'})
            
            # Load comments
            comments = load_comments()
            
            # Filter by metal and only return approved comments
            metal_comments = [
                comment for comment in comments.get(metal.lower(), [])
                if comment.get('approved', False)
            ]
            
            response.status_code = 200
            return json.dumps(metal_comments)
            
        elif request.method == 'POST':
            # Get request body
            try:
                comment_data = json.loads(request.body)
            except json.JSONDecodeError:
                response.status_code = 400
                return json.dumps({'error': 'Invalid JSON'})
            
            # Validate comment data
            if not validate_comment(comment_data):
                response.status_code = 400
                return json.dumps({'error': 'Invalid comment data'})
            
            # Sanitize comment
            sanitized_comment = sanitize_comment(comment_data)
            
            # Get client IP
            client_ip = request.headers.get('x-forwarded-for', '').split(',')[0].strip() or 'unknown'
            sanitized_comment['ip'] = client_ip
            
            # Load existing comments
            comments = load_comments()
            metal = sanitized_comment['metalName']
            
            if metal not in comments:
                comments[metal] = []
            
            # Check rate limiting
            if check_rate_limit(comments[metal], client_ip):
                response.status_code = 429
                return json.dumps({
                    'error': f'Too many comments. Please wait before commenting again. (Limit: {MAX_COMMENTS_PER_HOUR} per hour)'
                })
            
            # Add comment
            comments[metal].append(sanitized_comment)
            
            # Save comments
            save_comments(comments)
            
            response.status_code = 201
            return json.dumps({
                'success': True,
                'message': 'Comment submitted successfully! It will appear after moderation.',
                'id': sanitized_comment['id']
            })
            
        else:
            response.status_code = 405
            return json.dumps({'error': 'Method not allowed'})
            
    except Exception as e:
        print(f"Handler error: {e}")
        response.status_code = 500
        return json.dumps({'error': 'Internal server error', 'details': str(e)})

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
    try:
        if HAS_REDIS:
            import requests
            url = f"{os.getenv('KV_REST_API_URL')}/set/comments"
            headers = {
                'Authorization': f"Bearer {os.getenv('KV_REST_API_TOKEN')}",
                'Content-Type': 'application/json'
            }
            
            # Upstash expects the value as a JSON string
            data = {
                'value': json.dumps(comments)
            }
            
            response = requests.post(url, json=data, headers=headers)
            if response.status_code != 200:
                print(f"Failed to save comments: {response.text}")
        else:
            # Use in-memory storage for development
            global _memory_storage
            _memory_storage = comments
    except Exception as e:
        print(f"Error saving comments: {e}")
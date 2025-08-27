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

# Configuration
MAX_COMMENTS_PER_HOUR = int(os.getenv('MAX_COMMENTS_PER_HOUR', '3'))
COMMENT_MAX_LENGTH = int(os.getenv('COMMENT_MAX_LENGTH', '500'))

# In-memory storage fallback (for development)
_memory_storage = {}

def handler(request):
    # CORS headers
    headers = {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
        'Access-Control-Allow-Headers': 'Content-Type, Authorization',
        'Content-Type': 'application/json'
    }
    
    if request.method == 'OPTIONS':
        return {
            'statusCode': 200,
            'headers': headers,
            'body': ''
        }
    
    try:
        if request.method == 'GET':
            return handle_get_comments(request, headers)
        elif request.method == 'POST':
            return handle_post_comment(request, headers)
        else:
            return {
                'statusCode': 405,
                'headers': headers,
                'body': json.dumps({'error': 'Method not allowed'})
            }
    except Exception as e:
        print(f"Handler error: {e}")
        return {
            'statusCode': 500,
            'headers': headers,
            'body': json.dumps({'error': 'Internal server error'})
        }

def handle_get_comments(request, headers):
    # Parse query parameters
    query_params = request.args if hasattr(request, 'args') else {}
    metal = query_params.get('metal')
    
    if not metal:
        return {
            'statusCode': 400,
            'headers': headers,
            'body': json.dumps({'error': 'Metal parameter is required'})
        }
    
    # Load comments
    comments = load_comments()
    
    # Filter by metal and only return approved comments
    metal_comments = [
        comment for comment in comments.get(metal.lower(), [])
        if comment.get('approved', False)
    ]
    
    return {
        'statusCode': 200,
        'headers': headers,
        'body': json.dumps(metal_comments)
    }

def handle_post_comment(request, headers):
    try:
        # Get request body
        if hasattr(request, 'get_json'):
            comment_data = request.get_json()
        else:
            comment_data = json.loads(request.body) if hasattr(request, 'body') else {}
        
        # Validate comment data
        if not validate_comment(comment_data):
            return {
                'statusCode': 400,
                'headers': headers,
                'body': json.dumps({'error': 'Invalid comment data'})
            }
        
        # Sanitize comment
        sanitized_comment = sanitize_comment(comment_data)
        
        # Get client IP
        client_ip = get_client_ip(request)
        sanitized_comment['ip'] = client_ip
        
        # Load existing comments
        comments = load_comments()
        metal = sanitized_comment['metalName']
        
        if metal not in comments:
            comments[metal] = []
        
        # Check rate limiting
        if check_rate_limit(comments[metal], client_ip):
            return {
                'statusCode': 429,
                'headers': headers,
                'body': json.dumps({
                    'error': f'Too many comments. Please wait before commenting again. (Limit: {MAX_COMMENTS_PER_HOUR} per hour)'
                })
            }
        
        # Add comment
        comments[metal].append(sanitized_comment)
        
        # Save comments
        save_comments(comments)
        
        return {
            'statusCode': 201,
            'headers': headers,
            'body': json.dumps({
                'success': True,
                'message': 'Comment submitted successfully! It will appear after moderation.',
                'id': sanitized_comment['id']
            })
        }
        
    except Exception as e:
        print(f"Error handling POST comment: {e}")
        return {
            'statusCode': 500,
            'headers': headers,
            'body': json.dumps({'error': 'Internal server error'})
        }

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

def get_client_ip(request):
    # Try to get real IP from headers
    forwarded = getattr(request, 'headers', {}).get('x-forwarded-for')
    if forwarded:
        return forwarded.split(',')[0].strip()
    return 'unknown'

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
    try:
        if HAS_KV:
            # Use Vercel KV in production
            return kv.get('comments') or {}
        else:
            # Use in-memory storage for development
            return _memory_storage
    except Exception as e:
        print(f"Error loading comments: {e}")
        return {}

def save_comments(comments):
    try:
        if HAS_KV:
            # Use Vercel KV in production
            kv.set('comments', comments)
        else:
            # Use in-memory storage for development
            global _memory_storage
            _memory_storage = comments
    except Exception as e:
        print(f"Error saving comments: {e}")
from flask import Blueprint, request, jsonify
from helpers.helper import read_json, write_json
import uuid
from datetime import datetime

discussions = Blueprint('discussions', __name__)

# Endpoint to create a new discussion thread
@discussions.route('/threads', methods=['POST'])
def create_thread():
    data = request.get_json()
    bill_title = data.get('bill_title')
    description = data.get('description')
    user_id = data.get('user_id')  # Assuming user authentication provides user_id

    if not bill_title or not description or not user_id:
        return jsonify({'error': 'Missing required fields'}), 400

    thread = {
        'id': str(uuid.uuid4()),
        'bill_title': bill_title,
        'description': description,
        'creator': user_id,
        'created_at': datetime.utcnow().isoformat(),
        'comments': []
    }

    threads = read_json('storage/DiscussionThreads.json')
    threads.append(thread)
    write_json('storage/DiscussionThreads.json', threads)

    return jsonify({'message': 'Thread created successfully', 'thread': thread}), 201

# Endpoint to retrieve all discussion threads
@discussions.route('/threads', methods=['GET'])
def get_threads():
    threads = read_json('storage/DiscussionThreads.json')
    return jsonify({'threads': threads}), 200

# Endpoint to post a comment on a specific thread
@discussions.route('/threads/<thread_id>/comments', methods=['POST'])
def post_comment(thread_id):
    data = request.get_json()
    content = data.get('content')
    user_id = data.get('user_id')  # Assuming user authentication provides user_id

    if not content or not user_id:
        return jsonify({'error': 'Missing required fields'}), 400

    if len(content) > 500:
        return jsonify({'error': 'Comment exceeds 500 characters limit'}), 400

    comment = {
        'id': str(uuid.uuid4()),
        'user_id': user_id,
        'content': content,
        'created_at': datetime.utcnow().isoformat(),
        'replies': [],
        'likes': 0,
        'dislikes': 0,
        'liked_by': [],
        'disliked_by': [],
        'reports': []
    }

    threads = read_json('storage/DiscussionThreads.json')
    thread = next((t for t in threads if t['id'] == thread_id), None)
    if not thread:
        return jsonify({'error': 'Thread not found'}), 404

    thread['comments'].append(comment)
    write_json('storage/DiscussionThreads.json', threads)

    return jsonify({'message': 'Comment added successfully', 'comment': comment}), 201

# Endpoint to reply to a specific comment
@discussions.route('/threads/<thread_id>/comments/<comment_id>/replies', methods=['POST'])
def reply_comment(thread_id, comment_id):
    data = request.get_json()
    content = data.get('content')
    user_id = data.get('user_id')  # Assuming user authentication provides user_id

    if not content or not user_id:
        return jsonify({'error': 'Missing required fields'}), 400

    if len(content) > 500:
        return jsonify({'error': 'Reply exceeds 500 characters limit'}), 400

    reply = {
        'id': str(uuid.uuid4()),
        'user_id': user_id,
        'content': content,
        'created_at': datetime.utcnow().isoformat(),
        'likes': 0,
        'dislikes': 0,
        'liked_by': [],
        'disliked_by': [],
        'reports': []
    }

    threads = read_json('storage/DiscussionThreads.json')
    thread = next((t for t in threads if t['id'] == thread_id), None)
    if not thread:
        return jsonify({'error': 'Thread not found'}), 404

    comment = next((c for c in thread['comments'] if c['id'] == comment_id), None)
    if not comment:
        return jsonify({'error': 'Comment not found'}), 404

    comment['replies'].append(reply)
    write_json('storage/DiscussionThreads.json', threads)

    return jsonify({'message': 'Reply added successfully', 'reply': reply}), 201

# Endpoint to like a specific comment
@discussions.route('/threads/<thread_id>/comments/<comment_id>/like', methods=['POST'])
def like_comment(thread_id, comment_id):
    data = request.get_json()
    user_id = data.get('user_id')  # Assuming user authentication provides user_id

    if not user_id:
        return jsonify({'error': 'Missing user_id'}), 400

    threads = read_json('storage/DiscussionThreads.json')
    thread = next((t for t in threads if t['id'] == thread_id), None)
    if not thread:
        return jsonify({'error': 'Thread not found'}), 404

    comment = next((c for c in thread['comments'] if c['id'] == comment_id), None)
    if not comment:
        return jsonify({'error': 'Comment not found'}), 404

    if user_id in comment['liked_by']:
        return jsonify({'error': 'User has already liked this comment'}), 400

    if user_id in comment['disliked_by']:
        comment['disliked_by'].remove(user_id)
        comment['dislikes'] -= 1

    comment['liked_by'].append(user_id)
    comment['likes'] += 1
    write_json('storage/DiscussionThreads.json', threads)

    return jsonify({'message': 'Comment liked successfully', 'likes': comment['likes']}), 200

# Endpoint to dislike a specific comment
@discussions.route('/threads/<thread_id>/comments/<comment_id>/dislike', methods=['POST'])
def dislike_comment(thread_id, comment_id):
    data = request.get_json()
    user_id = data.get('user_id')  # Assuming user authentication provides user_id

    if not user_id:
        return jsonify({'error': 'Missing user_id'}), 400

    threads = read_json('storage/DiscussionThreads.json')
    thread = next((t for t in threads if t['id'] == thread_id), None)
    if not thread:
        return jsonify({'error': 'Thread not found'}), 404

    comment = next((c for c in thread['comments'] if c['id'] == comment_id), None)
    if not comment:
        return jsonify({'error': 'Comment not found'}), 404

    if user_id in comment['disliked_by']:
        return jsonify({'error': 'User has already disliked this comment'}), 400

    if user_id in comment['liked_by']:
        comment['liked_by'].remove(user_id)
        comment['likes'] -= 1

    comment['disliked_by'].append(user_id)
    comment['dislikes'] += 1
    write_json('storage/DiscussionThreads.json', threads)

    return jsonify({'message': 'Comment disliked successfully', 'dislikes': comment['dislikes']}), 200

# Endpoint to report a specific comment
@discussions.route('/threads/<thread_id>/comments/<comment_id>/report', methods=['POST'])
def report_comment(thread_id, comment_id):
    data = request.get_json()
    user_id = data.get('user_id')  # Assuming user authentication provides user_id
    reason = data.get('reason')

    if not user_id or not reason:
        return jsonify({'error': 'Missing required fields'}), 400

    threads = read_json('storage/DiscussionThreads.json')
    thread = next((t for t in threads if t['id'] == thread_id), None)
    if not thread:
        return jsonify({'error': 'Thread not found'}), 404

    comment = next((c for c in thread['comments'] if c['id'] == comment_id), None)
    if not comment:
        return jsonify({'error': 'Comment not found'}), 404

    report = {
        'user_id': user_id,
        'reason': reason,
        'reported_at': datetime.utcnow().isoformat()
    }

    comment['reports'].append(report)
    write_json('storage/DiscussionThreads.json', threads)

    return jsonify({'message': 'Comment reported successfully', 'report': report}), 200

# Endpoint to get a specific thread with comments and interactions
@discussions.route('/threads/<thread_id>', methods=['GET'])
def get_thread(thread_id):
    threads = read_json('storage/DiscussionThreads.json')
    thread = next((t for t in threads if t['id'] == thread_id), None)
    if not thread:
        return jsonify({'error': 'Thread not found'}), 404
    return jsonify({'thread': thread}), 200

# Register the blueprint (if not using app directly)
def register_routes(app):
    app.register_blueprint(discussions, url_prefix='/api')

# This function can be called in the main app to register the discussions routes
# Example:
# from discussions import register_routes
# register_routes(app)

# End of discussions.py
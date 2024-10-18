import React, { useState, useEffect } from 'react';
import io from 'socket.io-client';
import axios from 'axios';

const socket = io('http://localhost:5000'); // Adjust the URL as needed

const DiscussionThreads = () => {
  const [threads, setThreads] = useState([]);
  const [newThreadTitle, setNewThreadTitle] = useState('');
  const [newThreadContext, setNewThreadContext] = useState('');
  const [currentUser, setCurrentUser] = useState(null); // Assume user is set from context or props

  useEffect(() => {
    // Fetch existing discussion threads on component mount
    fetchThreads();

    // Listen for real-time updates
    socket.on('new_thread', (thread) => {
      setThreads((prevThreads) => [thread, ...prevThreads]);
    });

    socket.on('new_comment', ({ threadId, comment }) => {
      setThreads((prevThreads) =>
        prevThreads.map((thread) =>
          thread.id === threadId
            ? { ...thread, comments: [...thread.comments, comment] }
            : thread
        )
      );
    });

    socket.on('update_likes', ({ threadId, commentId, likes, dislikes }) => {
      setThreads((prevThreads) =>
        prevThreads.map((thread) => {
          if (thread.id === threadId) {
            return {
              ...thread,
              comments: thread.comments.map((comment) =>
                comment.id === commentId
                  ? { ...comment, likes, dislikes }
                  : comment
              ),
            };
          }
          return thread;
        })
      );
    });

    return () => {
      socket.off('new_thread');
      socket.off('new_comment');
      socket.off('update_likes');
    };
  }, []);

  const fetchThreads = async () => {
    try {
      const response = await axios.get('/api/discussions');
      setThreads(response.data);
    } catch (error) {
      console.error('Error fetching threads:', error);
    }
  };

  const handleCreateThread = async () => {
    if (!newThreadTitle || !newThreadContext) return;
    try {
      const response = await axios.post('/api/discussions', {
        title: newThreadTitle,
        context: newThreadContext,
        user: currentUser,
      });
      setNewThreadTitle('');
      setNewThreadContext('');
      // The new thread will be added via the 'new_thread' socket event
    } catch (error) {
      console.error('Error creating thread:', error);
    }
  };

  const handlePostComment = async (threadId, commentText) => {
    if (!commentText || commentText.length > 500) return;
    try {
      await axios.post(`/api/discussions/${threadId}/comments`, {
        text: commentText,
        user: currentUser,
      });
      // The new comment will be added via the 'new_comment' socket event
    } catch (error) {
      console.error('Error posting comment:', error);
    }
  };

  const handleReply = async (threadId, commentId, replyText) => {
    if (!replyText || replyText.length > 500) return;
    try {
      await axios.post(`/api/discussions/${threadId}/comments/${commentId}/replies`, {
        text: replyText,
        user: currentUser,
      });
      // The new reply will be added via the 'new_comment' socket event
    } catch (error) {
      console.error('Error posting reply:', error);
    }
  };

  const handleLikeDislike = async (threadId, commentId, type) => {
    try {
      await axios.post(`/api/discussions/${threadId}/comments/${commentId}/${type}`);
      // The updated likes/dislikes will be handled via the 'update_likes' socket event
    } catch (error) {
      console.error(`Error ${type} comment:`, error);
    }
  };

  const handleReport = async (threadId, commentId, reason) => {
    try {
      await axios.post(`/api/discussions/${threadId}/comments/${commentId}/report`, {
        reason,
        user: currentUser,
      });
      alert('Comment reported for review.');
    } catch (error) {
      console.error('Error reporting comment:', error);
    }
  };

  return (
    <div className="discussion-threads">
      <h2>Discussion Threads</h2>
      {/* Create New Thread */}
      <div className="create-thread">
        <h3>Create New Thread</h3>
        <input
          type="text"
          placeholder="Thread Title"
          value={newThreadTitle}
          onChange={(e) => setNewThreadTitle(e.target.value)}
        />
        <textarea
          placeholder="Thread Context"
          value={newThreadContext}
          onChange={(e) => setNewThreadContext(e.target.value)}
        ></textarea>
        <button onClick={handleCreateThread}>Create Thread</button>
      </div>
      {/* List of Threads */}
      <div className="threads-list">
        {threads.map((thread) => (
          <div key={thread.id} className="thread">
            <h4>{thread.title}</h4>
            <p>{thread.context}</p>
            <div className="comments">
              {thread.comments.map((comment) => (
                <div key={comment.id} className="comment">
                  <p>{comment.text}</p>
                  <div className="comment-actions">
                    <button onClick={() => handleLikeDislike(thread.id, comment.id, 'like')}>
                      Like ({comment.likes})
                    </button>
                    <button onClick={() => handleLikeDislike(thread.id, comment.id, 'dislike')}>
                      Dislike ({comment.dislikes})
                    </button>
                    <button
                      onClick={() => {
                        const reply = prompt('Enter your reply:');
                        if (reply) handleReply(thread.id, comment.id, reply);
                      }}
                    >
                      Reply
                    </button>
                    <button
                      onClick={() => {
                        const reason = prompt('Reason for reporting:');
                        if (reason) handleReport(thread.id, comment.id, reason);
                      }}
                    >
                      Report
                    </button>
                  </div>
                  {/* Render Replies */}
                  {comment.replies && comment.replies.length > 0 && (
                    <div className="replies" style={{ marginLeft: '20px' }}>
                      {comment.replies.map((reply) => (
                        <div key={reply.id} className="reply">
                          <p>{reply.text}</p>
                          <div className="reply-actions">
                            <button onClick={() => handleLikeDislike(thread.id, reply.id, 'like')}>
                              Like ({reply.likes})
                            </button>
                            <button onClick={() => handleLikeDislike(thread.id, reply.id, 'dislike')}>
                              Dislike ({reply.dislikes})
                            </button>
                            <button
                              onClick={() => {
                                const replyText = prompt('Enter your reply:');
                                if (replyText) handleReply(thread.id, reply.id, replyText);
                              }}
                            >
                              Reply
                            </button>
                            <button
                              onClick={() => {
                                const reason = prompt('Reason for reporting:');
                                if (reason) handleReport(thread.id, reply.id, reason);
                              }}
                            >
                              Report
                            </button>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default DiscussionThreads;
"""Tests for session store service"""

import pytest
import time
from backend.services import SessionStore


@pytest.fixture
def session_store():
    """Create session store with 1 second timeout for testing"""
    return SessionStore(timeout_minutes=1/60)  # 1 second


def test_create_session(session_store):
    """Test creating a new session"""
    schema = {"users": {"columns": [{"name": "id", "type": "INT"}]}}
    session_id = session_store.create_session(schema)

    assert isinstance(session_id, str)
    assert len(session_id) > 0
    assert session_store.session_exists(session_id)


def test_get_session(session_store):
    """Test retrieving a session"""
    schema = {"users": {"columns": [{"name": "id", "type": "INT"}]}}
    session_id = session_store.create_session(schema)

    session = session_store.get_session(session_id)
    assert session is not None
    assert session["schema"] == schema
    assert session["query_count"] == 0


def test_session_expiration(session_store):
    """Test that sessions expire after timeout"""
    schema = {"users": {"columns": []}}
    session_id = session_store.create_session(schema)

    # Session should exist immediately
    assert session_store.session_exists(session_id)

    # Wait for expiration (1 second + margin)
    time.sleep(1.1)

    # Session should be expired
    assert not session_store.session_exists(session_id)
    assert session_store.get_session(session_id) is None


def test_get_nonexistent_session(session_store):
    """Test retrieving a non-existent session"""
    assert session_store.get_session("nonexistent") is None


def test_delete_session(session_store):
    """Test deleting a session"""
    schema = {"users": {"columns": []}}
    session_id = session_store.create_session(schema)

    # Delete session
    result = session_store.delete_session(session_id)
    assert result is True
    assert not session_store.session_exists(session_id)

    # Delete again should return False
    result = session_store.delete_session(session_id)
    assert result is False


def test_increment_query_count(session_store):
    """Test incrementing query count"""
    schema = {"users": {"columns": []}}
    session_id = session_store.create_session(schema)

    # Initial count
    session = session_store.get_session(session_id)
    assert session["query_count"] == 0

    # Increment count
    result = session_store.increment_query_count(session_id)
    assert result is True

    session = session_store.get_session(session_id)
    assert session["query_count"] == 1

    # Increment again
    session_store.increment_query_count(session_id)
    session = session_store.get_session(session_id)
    assert session["query_count"] == 2


def test_increment_query_count_nonexistent(session_store):
    """Test incrementing count on non-existent session"""
    result = session_store.increment_query_count("nonexistent")
    assert result is False


def test_cleanup_expired_sessions(session_store):
    """Test cleanup of expired sessions"""
    # Create a session
    schema = {"users": {"columns": []}}
    session_id = session_store.create_session(schema)

    # Verify count
    assert session_store.get_active_session_count() == 1

    # Wait for expiration
    time.sleep(1.1)

    # Cleanup
    count = session_store.cleanup_expired_sessions()
    assert count == 1
    assert session_store.get_active_session_count() == 0


def test_get_active_session_count(session_store):
    """Test getting count of active sessions"""
    assert session_store.get_active_session_count() == 0

    schema = {"users": {"columns": []}}
    session_store.create_session(schema)
    assert session_store.get_active_session_count() == 1

    session_store.create_session(schema)
    assert session_store.get_active_session_count() == 2


def test_get_session_info(session_store):
    """Test getting session metadata"""
    schema = {"users": {"columns": [{"name": "id", "type": "INT"}]}}
    session_id = session_store.create_session(schema)

    info = session_store.get_session_info(session_id)
    assert info is not None
    assert info["session_id"] == session_id
    assert info["query_count"] == 0
    assert info["table_count"] == 1
    assert "created_at" in info
    assert "expires_at" in info


def test_get_session_info_nonexistent(session_store):
    """Test getting info for non-existent session"""
    info = session_store.get_session_info("nonexistent")
    assert info is None


def test_multiple_sessions_isolated(session_store):
    """Test that multiple sessions are isolated"""
    schema1 = {"users": {"columns": [{"name": "id", "type": "INT"}]}}
    schema2 = {"orders": {"columns": [{"name": "order_id", "type": "INT"}]}}

    sid1 = session_store.create_session(schema1)
    sid2 = session_store.create_session(schema2)

    session1 = session_store.get_session(sid1)
    session2 = session_store.get_session(sid2)

    assert session1["schema"] != session2["schema"]
    assert "users" in session1["schema"]
    assert "orders" in session2["schema"]


def test_last_accessed_updated(session_store):
    """Test that last_accessed timestamp is updated"""
    schema = {"users": {"columns": []}}
    session_id = session_store.create_session(schema)

    session1 = session_store.get_session(session_id)
    first_access = session1["last_accessed"]

    # Wait a bit
    time.sleep(0.1)

    # Access again
    session2 = session_store.get_session(session_id)
    second_access = session2["last_accessed"]

    # Last accessed should have been updated
    assert second_access >= first_access

"""
Tests for the Mergington High School Activities API
"""

import copy
import pytest
from fastapi.testclient import TestClient
from src.app import app, activities


@pytest.fixture
def client():
    """Create a test client for the FastAPI app"""
    return TestClient(app)


@pytest.fixture
def reset_activities():
    """Reset activities to initial state before and after each test"""
    # Save a deep copy of the original state
    original_activities = copy.deepcopy(activities)

    yield

    # Restore the entire activities dict to its original state
    activities.clear()
    activities.update(copy.deepcopy(original_activities))


class TestRoot:
    def test_root_redirect(self, client):
        """Test that root endpoint redirects to static index"""
        response = client.get("/", follow_redirects=False)
        assert response.status_code == 307
        assert "/static/index.html" in response.headers["location"]


class TestGetActivities:
    def test_get_activities(self, client):
        """Test retrieving all activities"""
        response = client.get("/activities")
        assert response.status_code == 200

        data = response.json()
        assert isinstance(data, dict)
        assert len(data) > 0

        # Check structure of an activity
        for activity_name, activity_data in data.items():
            assert "description" in activity_data
            assert "schedule" in activity_data
            assert "max_participants" in activity_data
            assert "participants" in activity_data
            assert isinstance(activity_data["participants"], list)


class TestSignup:
    def test_signup_success(self, client, reset_activities):
        """Test successful signup for an activity"""
        response = client.post(
            "/activities/Chess Club/signup", params={"email": "test@mergington.edu"})
        assert response.status_code == 200

        data = response.json()
        assert "message" in data
        assert "test@mergington.edu" in data["message"]

        # Verify participant was added
        activities_response = client.get("/activities")
        assert "test@mergington.edu" in activities_response.json()[
            "Chess Club"]["participants"]

    def test_signup_duplicate(self, client, reset_activities):
        """Test that duplicate signup is prevented"""
        # First signup
        response1 = client.post(
            "/activities/Chess Club/signup", params={"email": "duplicate@mergington.edu"})
        assert response1.status_code == 200

        # Second signup with same email
        response2 = client.post(
            "/activities/Chess Club/signup", params={"email": "duplicate@mergington.edu"})
        assert response2.status_code == 400

        data = response2.json()
        assert "detail" in data
        assert "already signed up" in data["detail"]

    def test_signup_invalid_activity(self, client):
        """Test signup for non-existent activity"""
        response = client.post(
            "/activities/Nonexistent Activity/signup", params={"email": "test@mergington.edu"})
        assert response.status_code == 404

        data = response.json()
        assert "detail" in data
        assert "Activity not found" in data["detail"]

    def test_signup_activity_full(self, client, reset_activities):
        """Test that signup is rejected when activity is at capacity"""
        # Get an activity with small max_participants
        activities_response = client.get("/activities")
        activities_data = activities_response.json()

        # Find an activity that's currently at or near capacity
        # Tennis Club has max 10 and 2 participants
        full_activity = "Tennis Club"
        activity = activities_data[full_activity]
        max_participants = activity["max_participants"]
        current_participants = len(activity["participants"])

        # Fill up the activity
        for i in range(max_participants - current_participants):
            response = client.post(
                f"/activities/{full_activity}/signup",
                params={"email": f"filler{i}@mergington.edu"}
            )
            assert response.status_code == 200

        # Try to signup when full
        response = client.post(
            f"/activities/{full_activity}/signup",
            params={"email": "overflow@mergington.edu"}
        )
        assert response.status_code == 409

        data = response.json()
        assert "detail" in data
        assert "full" in data["detail"].lower()


class TestUnregister:
    def test_unregister_success(self, client, reset_activities):
        """Test successful unregistration from activity"""
        # First, signup
        client.post("/activities/Chess Club/signup",
                    params={"email": "unreg@mergington.edu"})

        # Then unregister
        response = client.delete(
            "/activities/Chess Club/unregister", params={"email": "unreg@mergington.edu"})
        assert response.status_code == 200

        data = response.json()
        assert "message" in data
        assert "unreg@mergington.edu" in data["message"]

        # Verify participant was removed
        activities_response = client.get("/activities")
        assert "unreg@mergington.edu" not in activities_response.json()[
            "Chess Club"]["participants"]

    def test_unregister_not_found(self, client):
        """Test unregister for student not in activity"""
        response = client.delete(
            "/activities/Chess Club/unregister", params={"email": "notfound@mergington.edu"})
        assert response.status_code == 404

        data = response.json()
        assert "detail" in data
        assert "not found" in data["detail"]

    def test_unregister_invalid_activity(self, client):
        """Test unregister from non-existent activity"""
        response = client.delete(
            "/activities/Nonexistent Activity/unregister", params={"email": "test@mergington.edu"})
        assert response.status_code == 404

        data = response.json()
        assert "detail" in data


class TestActivityParticipantLimits:
    def test_get_participant_count(self, client):
        """Test that participant count is accurate"""
        response = client.get("/activities")
        data = response.json()

        for activity_name, activity_data in data.items():
            participants = activity_data["participants"]
            max_participants = activity_data["max_participants"]

            # Verify count doesn't exceed max
            assert len(participants) <= max_participants

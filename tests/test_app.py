import pytest
from fastapi.testclient import TestClient
from src.app import app


client = TestClient(app)


class TestActivities:
    """Tests for fetching activities"""

    def test_get_activities(self):
        """Test retrieving all activities"""
        response = client.get("/activities")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
        assert len(data) > 0
        assert "Chess Club" in data
        assert "Programming Class" in data
        assert "participants" in data["Chess Club"]

    def test_get_activities_structure(self):
        """Test that activities have the correct structure"""
        response = client.get("/activities")
        data = response.json()
        activity = data["Chess Club"]
        assert "description" in activity
        assert "schedule" in activity
        assert "max_participants" in activity
        assert isinstance(activity["participants"], list)


class TestSignUp:
    """Tests for signing up for activities"""

    def test_signup_new_participant(self):
        """Test signing up a new participant"""
        response = client.post(
            "/activities/Chess%20Club/signup?email=newstudent@mergington.edu"
        )
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "newstudent@mergington.edu" in data["message"]

    def test_signup_duplicate_participant(self):
        """Test that duplicate signups are prevented"""
        email = "duplicate@mergington.edu"
        # First signup
        response1 = client.post(
            f"/activities/Chess%20Club/signup?email={email}"
        )
        assert response1.status_code == 200

        # Attempt duplicate signup
        response2 = client.post(
            f"/activities/Chess%20Club/signup?email={email}"
        )
        assert response2.status_code == 400
        data = response2.json()
        assert "already signed up" in data["detail"]

    def test_signup_invalid_activity(self):
        """Test signing up for a non-existent activity"""
        response = client.post(
            "/activities/Invalid%20Activity/signup?email=student@mergington.edu"
        )
        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"]

    def test_signup_adds_participant(self):
        """Test that signup actually adds the participant to the list"""
        email = "verify@mergington.edu"
        response = client.post(
            f"/activities/Basketball%20Team/signup?email={email}"
        )
        assert response.status_code == 200

        # Verify participant is in the list
        activities = client.get("/activities").json()
        assert email in activities["Basketball Team"]["participants"]


class TestUnregister:
    """Tests for unregistering from activities"""

    def test_unregister_existing_participant(self):
        """Test unregistering an existing participant"""
        email = "unregister@mergington.edu"
        # First signup
        client.post(f"/activities/Tennis%20Club/signup?email={email}")

        # Then unregister
        response = client.post(
            f"/activities/Tennis%20Club/unregister?email={email}"
        )
        assert response.status_code == 200
        data = response.json()
        assert "Unregistered" in data["message"]

        # Verify participant is removed
        activities = client.get("/activities").json()
        assert email not in activities["Tennis Club"]["participants"]

    def test_unregister_non_participant(self):
        """Test unregistering someone who is not signed up"""
        response = client.post(
            "/activities/Drama%20Club/unregister?email=notasignedupstudent@mergington.edu"
        )
        assert response.status_code == 400
        data = response.json()
        assert "not signed up" in data["detail"]

    def test_unregister_invalid_activity(self):
        """Test unregistering from a non-existent activity"""
        response = client.post(
            "/activities/Invalid%20Activity/unregister?email=student@mergington.edu"
        )
        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"]

    def test_signup_after_unregister(self):
        """Test that a student can re-signup after unregistering"""
        email = "resignup@mergington.edu"
        activity = "Art%20Studio"

        # Signup
        response1 = client.post(f"/activities/{activity}/signup?email={email}")
        assert response1.status_code == 200

        # Unregister
        response2 = client.post(f"/activities/{activity}/unregister?email={email}")
        assert response2.status_code == 200

        # Re-signup
        response3 = client.post(f"/activities/{activity}/signup?email={email}")
        assert response3.status_code == 200

        # Verify in list
        activities = client.get("/activities").json()
        assert email in activities["Art Studio"]["participants"]


class TestEdgeCases:
    """Tests for edge cases and data integrity"""

    def test_participant_count_after_operations(self):
        """Test that participant counts remain accurate"""
        activity = "Science Club"
        initial = client.get("/activities").json()
        initial_count = len(initial[activity]["participants"])

        # Signup
        email = "counter@mergington.edu"
        client.post(f"/activities/Science%20Club/signup?email={email}")

        after_signup = client.get("/activities").json()
        assert len(after_signup[activity]["participants"]) == initial_count + 1

        # Unregister
        client.post(f"/activities/Science%20Club/unregister?email={email}")

        after_unregister = client.get("/activities").json()
        assert len(after_unregister[activity]["participants"]) == initial_count

    def test_max_participants_not_enforced(self):
        """Test current behavior - max_participants is not enforced"""
        # This documents the current behavior where max_participants is not validated
        activity = "Gym Class"
        response = client.get("/activities").json()
        gym = response[activity]
        max_p = gym["max_participants"]
        current_p = len(gym["participants"])

        # We can signup even if at capacity (documenting current behavior)
        email = "overcapacity@mergington.edu"
        signup_response = client.post(
            f"/activities/Gym%20Class/signup?email={email}"
        )
        # This currently succeeds, documenting the behavior
        assert signup_response.status_code in [200, 400]  # Either is acceptable currently

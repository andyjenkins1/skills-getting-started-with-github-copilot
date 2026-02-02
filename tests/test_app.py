"""
Tests for the Mergington High School API
"""

import pytest
from fastapi.testclient import TestClient
from src.app import app, activities


@pytest.fixture
def client():
    """Create a test client for the FastAPI app"""
    return TestClient(app)


@pytest.fixture(autouse=True)
def reset_activities():
    """Reset activities to initial state before each test"""
    activities.clear()
    activities.update({
        "Chess Club": {
            "description": "Learn strategies and compete in chess tournaments",
            "schedule": "Fridays, 3:30 PM - 5:00 PM",
            "max_participants": 12,
            "participants": ["michael@mergington.edu", "daniel@mergington.edu"]
        },
        "Programming Class": {
            "description": "Learn programming fundamentals and build software projects",
            "schedule": "Tuesdays and Thursdays, 3:30 PM - 4:30 PM",
            "max_participants": 20,
            "participants": ["emma@mergington.edu", "sophia@mergington.edu"]
        },
        "Gym Class": {
            "description": "Physical education and sports activities",
            "schedule": "Mondays, Wednesdays, Fridays, 2:00 PM - 3:00 PM",
            "max_participants": 30,
            "participants": ["john@mergington.edu", "olivia@mergington.edu"]
        },
        "Art Club": {
            "description": "Explore various art techniques and create your own masterpieces",
            "schedule": "Wednesdays, 4:00 PM - 6:00 PM",
            "max_participants": 15,
            "participants": []
        },
    })


class TestRootEndpoint:
    """Tests for the root endpoint"""

    def test_root_redirects_to_static(self, client):
        """Test that root endpoint redirects to static index.html"""
        response = client.get("/", follow_redirects=False)
        assert response.status_code == 307
        assert response.headers["location"] == "/static/index.html"


class TestGetActivities:
    """Tests for GET /activities endpoint"""

    def test_get_activities_returns_all_activities(self, client):
        """Test that getting activities returns all activities"""
        response = client.get("/activities")
        assert response.status_code == 200
        data = response.json()
        
        assert "Chess Club" in data
        assert "Programming Class" in data
        assert "Gym Class" in data
        assert "Art Club" in data

    def test_get_activities_structure(self, client):
        """Test that activities have the correct structure"""
        response = client.get("/activities")
        data = response.json()
        
        chess_club = data["Chess Club"]
        assert "description" in chess_club
        assert "schedule" in chess_club
        assert "max_participants" in chess_club
        assert "participants" in chess_club
        assert isinstance(chess_club["participants"], list)

    def test_get_activities_includes_participants(self, client):
        """Test that activities include participant information"""
        response = client.get("/activities")
        data = response.json()
        
        chess_club = data["Chess Club"]
        assert len(chess_club["participants"]) == 2
        assert "michael@mergington.edu" in chess_club["participants"]
        assert "daniel@mergington.edu" in chess_club["participants"]


class TestSignupForActivity:
    """Tests for POST /activities/{activity_name}/signup endpoint"""

    def test_signup_for_activity_success(self, client):
        """Test successful signup for an activity"""
        response = client.post(
            "/activities/Art%20Club/signup?email=newstudent@mergington.edu"
        )
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "newstudent@mergington.edu" in data["message"]
        assert "Art Club" in data["message"]

    def test_signup_adds_participant_to_activity(self, client):
        """Test that signup actually adds participant to the activity"""
        client.post("/activities/Art%20Club/signup?email=newstudent@mergington.edu")
        
        # Verify participant was added
        response = client.get("/activities")
        data = response.json()
        assert "newstudent@mergington.edu" in data["Art Club"]["participants"]

    def test_signup_for_nonexistent_activity(self, client):
        """Test signup for an activity that doesn't exist"""
        response = client.post(
            "/activities/Nonexistent%20Club/signup?email=student@mergington.edu"
        )
        assert response.status_code == 404
        data = response.json()
        assert data["detail"] == "Activity not found"

    def test_signup_duplicate_participant(self, client):
        """Test that a student cannot sign up for the same activity twice"""
        # First signup should succeed
        response1 = client.post(
            "/activities/Chess%20Club/signup?email=michael@mergington.edu"
        )
        assert response1.status_code == 400
        data = response1.json()
        assert "already signed up" in data["detail"]

    def test_signup_with_url_encoded_activity_name(self, client):
        """Test signup with URL encoded activity name"""
        response = client.post(
            "/activities/Programming%20Class/signup?email=newcoder@mergington.edu"
        )
        assert response.status_code == 200
        
        # Verify participant was added
        response = client.get("/activities")
        data = response.json()
        assert "newcoder@mergington.edu" in data["Programming Class"]["participants"]


class TestRemoveParticipant:
    """Tests for DELETE /activities/{activity_name}/participants/{email} endpoint"""

    def test_remove_participant_success(self, client):
        """Test successful removal of a participant"""
        response = client.delete(
            "/activities/Chess%20Club/participants/michael@mergington.edu"
        )
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "Removed" in data["message"]
        assert "michael@mergington.edu" in data["message"]

    def test_remove_participant_actually_removes(self, client):
        """Test that removal actually removes the participant"""
        client.delete("/activities/Chess%20Club/participants/michael@mergington.edu")
        
        # Verify participant was removed
        response = client.get("/activities")
        data = response.json()
        assert "michael@mergington.edu" not in data["Chess Club"]["participants"]
        assert "daniel@mergington.edu" in data["Chess Club"]["participants"]

    def test_remove_participant_from_nonexistent_activity(self, client):
        """Test removing participant from activity that doesn't exist"""
        response = client.delete(
            "/activities/Nonexistent%20Club/participants/student@mergington.edu"
        )
        assert response.status_code == 404
        data = response.json()
        assert data["detail"] == "Activity not found"

    def test_remove_nonexistent_participant(self, client):
        """Test removing a participant that's not in the activity"""
        response = client.delete(
            "/activities/Chess%20Club/participants/notregistered@mergington.edu"
        )
        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"]

    def test_remove_participant_with_url_encoding(self, client):
        """Test removal with URL encoded names and email"""
        response = client.delete(
            "/activities/Programming%20Class/participants/emma@mergington.edu"
        )
        assert response.status_code == 200
        
        # Verify participant was removed
        response = client.get("/activities")
        data = response.json()
        assert "emma@mergington.edu" not in data["Programming Class"]["participants"]


class TestIntegrationScenarios:
    """Integration tests for complete workflows"""

    def test_signup_and_remove_workflow(self, client):
        """Test complete workflow: signup a student and then remove them"""
        # Sign up
        signup_response = client.post(
            "/activities/Art%20Club/signup?email=test@mergington.edu"
        )
        assert signup_response.status_code == 200
        
        # Verify signup
        activities_response = client.get("/activities")
        data = activities_response.json()
        assert "test@mergington.edu" in data["Art Club"]["participants"]
        
        # Remove participant
        remove_response = client.delete(
            "/activities/Art%20Club/participants/test@mergington.edu"
        )
        assert remove_response.status_code == 200
        
        # Verify removal
        activities_response = client.get("/activities")
        data = activities_response.json()
        assert "test@mergington.edu" not in data["Art Club"]["participants"]

    def test_multiple_signups_to_different_activities(self, client):
        """Test that a student can sign up for multiple different activities"""
        email = "multitasker@mergington.edu"
        
        # Sign up for Art Club
        response1 = client.post(f"/activities/Art%20Club/signup?email={email}")
        assert response1.status_code == 200
        
        # Sign up for Gym Class
        response2 = client.post(f"/activities/Gym%20Class/signup?email={email}")
        assert response2.status_code == 200
        
        # Verify both signups
        response = client.get("/activities")
        data = response.json()
        assert email in data["Art Club"]["participants"]
        assert email in data["Gym Class"]["participants"]

    def test_activity_participants_count_updates(self, client):
        """Test that participant counts update correctly after signup and removal"""
        # Initial state
        response = client.get("/activities")
        data = response.json()
        initial_count = len(data["Art Club"]["participants"])
        
        # Add participant
        client.post("/activities/Art%20Club/signup?email=newbie@mergington.edu")
        response = client.get("/activities")
        data = response.json()
        assert len(data["Art Club"]["participants"]) == initial_count + 1
        
        # Remove participant
        client.delete("/activities/Art%20Club/participants/newbie@mergington.edu")
        response = client.get("/activities")
        data = response.json()
        assert len(data["Art Club"]["participants"]) == initial_count

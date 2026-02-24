"""
Tests for the Mergington High School Activities API.
"""

import pytest
from fastapi.testclient import TestClient

from src.app import app, activities


@pytest.fixture(autouse=True)
def reset_activities():
    """Reset participant lists to a known state before each test."""
    original = {name: list(details["participants"]) for name, details in activities.items()}
    yield
    for name, original_participants in original.items():
        activities[name]["participants"] = original_participants


@pytest.fixture
def client():
    return TestClient(app, follow_redirects=False)


# ---------------------------------------------------------------------------
# GET /
# ---------------------------------------------------------------------------

def test_root_redirects_to_index(client):
    response = client.get("/")
    assert response.status_code == 307
    assert response.headers["location"] == "/static/index.html"


# ---------------------------------------------------------------------------
# GET /activities
# ---------------------------------------------------------------------------

def test_get_activities_returns_all(client):
    response = client.get("/activities")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, dict)
    assert len(data) == 9


def test_get_activities_contains_expected_fields(client):
    response = client.get("/activities")
    data = response.json()
    for activity in data.values():
        assert "description" in activity
        assert "schedule" in activity
        assert "max_participants" in activity
        assert "participants" in activity


def test_get_activities_chess_club_present(client):
    response = client.get("/activities")
    data = response.json()
    assert "Chess Club" in data


# ---------------------------------------------------------------------------
# POST /activities/{activity_name}/signup
# ---------------------------------------------------------------------------

def test_signup_success(client):
    response = client.post(
        "/activities/Chess%20Club/signup",
        params={"email": "newstudent@mergington.edu"},
    )
    assert response.status_code == 200
    assert "newstudent@mergington.edu" in response.json()["message"]
    assert "newstudent@mergington.edu" in activities["Chess Club"]["participants"]


def test_signup_adds_participant_visible_in_get(client):
    email = "visible@mergington.edu"
    client.post("/activities/Drama%20Club/signup", params={"email": email})
    response = client.get("/activities")
    assert email in response.json()["Drama Club"]["participants"]


def test_signup_already_registered_returns_400(client):
    response = client.post(
        "/activities/Chess%20Club/signup",
        params={"email": "michael@mergington.edu"},
    )
    assert response.status_code == 400
    assert "already signed up" in response.json()["detail"]


def test_signup_unknown_activity_returns_404(client):
    response = client.post(
        "/activities/Unknown%20Activity/signup",
        params={"email": "someone@mergington.edu"},
    )
    assert response.status_code == 404
    assert "Activity not found" in response.json()["detail"]


# ---------------------------------------------------------------------------
# DELETE /activities/{activity_name}/signup
# ---------------------------------------------------------------------------

def test_unregister_success(client):
    response = client.delete(
        "/activities/Chess%20Club/signup",
        params={"email": "michael@mergington.edu"},
    )
    assert response.status_code == 200
    assert "michael@mergington.edu" in response.json()["message"]
    assert "michael@mergington.edu" not in activities["Chess Club"]["participants"]


def test_unregister_participant_no_longer_in_get(client):
    email = "daniel@mergington.edu"
    client.delete("/activities/Chess%20Club/signup", params={"email": email})
    response = client.get("/activities")
    assert email not in response.json()["Chess Club"]["participants"]


def test_unregister_not_signed_up_returns_400(client):
    response = client.delete(
        "/activities/Chess%20Club/signup",
        params={"email": "notregistered@mergington.edu"},
    )
    assert response.status_code == 400
    assert "not signed up" in response.json()["detail"]


def test_unregister_unknown_activity_returns_404(client):
    response = client.delete(
        "/activities/Unknown%20Activity/signup",
        params={"email": "someone@mergington.edu"},
    )
    assert response.status_code == 404
    assert "Activity not found" in response.json()["detail"]

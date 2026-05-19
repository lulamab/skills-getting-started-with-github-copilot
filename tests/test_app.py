import pytest
from fastapi.testclient import TestClient
from src.app import app, activities


@pytest.fixture(autouse=True)
def reset_activities():
    """Reset participants to a known state before each test."""
    original = {name: list(details["participants"]) for name, details in activities.items()}
    yield
    for name, details in activities.items():
        details["participants"] = original[name]


client = TestClient(app)


# ---------------------------------------------------------------------------
# GET /activities
# ---------------------------------------------------------------------------

def test_get_activities_returns_200():
    response = client.get("/activities")
    assert response.status_code == 200


def test_get_activities_returns_dict():
    response = client.get("/activities")
    data = response.json()
    assert isinstance(data, dict)
    assert len(data) > 0


def test_get_activities_contains_expected_fields():
    response = client.get("/activities")
    for activity in response.json().values():
        assert "description" in activity
        assert "schedule" in activity
        assert "max_participants" in activity
        assert "participants" in activity


# ---------------------------------------------------------------------------
# POST /activities/{activity_name}/signup
# ---------------------------------------------------------------------------

def test_signup_success():
    response = client.post(
        "/activities/Chess Club/signup",
        params={"email": "newstudent@mergington.edu"},
    )
    assert response.status_code == 200
    assert "newstudent@mergington.edu" in response.json()["message"]


def test_signup_adds_participant():
    client.post("/activities/Chess Club/signup", params={"email": "newstudent@mergington.edu"})
    response = client.get("/activities")
    assert "newstudent@mergington.edu" in response.json()["Chess Club"]["participants"]


def test_signup_unknown_activity_returns_404():
    response = client.post(
        "/activities/Underwater Basket Weaving/signup",
        params={"email": "student@mergington.edu"},
    )
    assert response.status_code == 404


def test_signup_duplicate_returns_400():
    email = "michael@mergington.edu"  # already in Chess Club fixtures
    response = client.post("/activities/Chess Club/signup", params={"email": email})
    assert response.status_code == 400


# ---------------------------------------------------------------------------
# DELETE /activities/{activity_name}/signup
# ---------------------------------------------------------------------------

def test_unregister_success():
    email = "michael@mergington.edu"  # pre-existing Chess Club participant
    response = client.delete("/activities/Chess Club/signup", params={"email": email})
    assert response.status_code == 200
    assert email in response.json()["message"]


def test_unregister_removes_participant():
    email = "michael@mergington.edu"
    client.delete("/activities/Chess Club/signup", params={"email": email})
    response = client.get("/activities")
    assert email not in response.json()["Chess Club"]["participants"]


def test_unregister_unknown_activity_returns_404():
    response = client.delete(
        "/activities/Underwater Basket Weaving/signup",
        params={"email": "student@mergington.edu"},
    )
    assert response.status_code == 404


def test_unregister_not_registered_returns_404():
    response = client.delete(
        "/activities/Chess Club/signup",
        params={"email": "nobody@mergington.edu"},
    )
    assert response.status_code == 404


# ---------------------------------------------------------------------------
# GET / (redirect)
# ---------------------------------------------------------------------------

def test_root_redirects_to_static():
    response = client.get("/", follow_redirects=False)
    assert response.status_code in (301, 302, 307, 308)
    assert "/static/index.html" in response.headers["location"]

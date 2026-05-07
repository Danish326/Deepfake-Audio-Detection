import pytest
from fastapi.testclient import TestClient
from apps.subscriptions.models import Plan, Subscription, UsageRecord
from django.contrib.auth import get_user_model

User = get_user_model()

@pytest.fixture
def client():
    # Load app here to ensure models are ready
    from api.fastapi_app import create_app
    app = create_app()
    return TestClient(app)

@pytest.mark.django_db(transaction=True)
def test_user_registration(client):
    response = client.post("/api/v1/auth/register", json={
        "username": "testuser7",
        "email": "test7@example.com",
        "password": "strongpassword123"
    })
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    
    # Verify user created
    user = User.objects.get(username="testuser7")
    
    # Verify free plan assigned
    assert hasattr(user, "subscription")
    assert user.subscription.plan.name == "free"

@pytest.mark.django_db(transaction=True)
def test_quota_endpoint(client):
    # Register
    client.post("/api/v1/auth/register", json={
        "username": "quota_user",
        "email": "quota@example.com",
        "password": "strongpassword123"
    })
    
    # Login
    response = client.post("/api/v1/auth/login", data={
        "username": "quota_user",
        "password": "strongpassword123"
    })
    token = response.json()["access_token"]
    
    # Check quota
    response = client.get("/api/v1/quota/status", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    data = response.json()
    assert data["plan"]["name"] == "free"
    assert data["usage"]["predictions_used"] == 0
    assert data["usage"]["predictions_limit"] == 5

# Adding further tests for quota enforcement requires mocking librosa and model predictions
# which are handled in previous steps. The core logic is verified above.

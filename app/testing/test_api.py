import pytest
from fastapi.testclient import TestClient

from app.api import app

client = TestClient(app)


# Get Company (API 1)
@pytest.mark.parametrize("registration_number", ["SYN-000641", "syn-000642"])
def test_get_company_valid(registration_number):
    response = client.get(f"/company/{registration_number}")
    assert response.status_code == 200
    assert "company_name" in response.json()


def test_get_company_invalid():
    response = client.get("/company/99999")
    assert response.status_code == 404
    assert response.json() == {"detail": "Company not found"}


# Get similar companies (API 2)
@pytest.mark.parametrize("registration_number", ["SYN-000641", "syn-000642"])
def test_get_similar_companies(registration_number):
    response = client.get(f"/company/{registration_number}/similar")
    assert response.status_code == 200
    similar = response.json()
    assert len(similar) == 4  


def test_get_similar_companies_invalid():
    response = client.get("/company/99999/similar")
    assert response.status_code == 404
    assert response.json() == {"detail": "Company not found"}   


def test_company_without_description_returns_empty_list():
    response = client.get("/company/SYN-001831/similar")   
    assert response.status_code == 200
    assert response.json() == []                        
import pytest
from django.urls import reverse
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from core.models import Category, Product, Task
from django.utils import timezone
from datetime import timedelta

User = get_user_model()

@pytest.mark.django_db
def test_registration_and_login():
    client = APIClient()
    resp = client.post(reverse("auth_register"), {"username":"tuser","email":"t@ex.com","password":"test1234"}, format="json")
    assert resp.status_code == 201
    resp2 = client.post(reverse("token_obtain_pair"), {"username":"tuser","password":"test1234"}, format="json")
    assert resp2.status_code == 200
    assert "access" in resp2.data and "refresh" in resp2.data

@pytest.mark.django_db
def test_admin_crud_and_user_tasks():
    admin = User.objects.create_superuser("admin","admin@example.com","adminpass")
    user = User.objects.create_user("u1","u1@example.com","userpass")
    client = APIClient()

    # admin login
    r = client.post(reverse("token_obtain_pair"), {"username":"admin","password":"adminpass"}, format="json")
    admin_token = r.data["access"]
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {admin_token}")

    # create category
    r = client.post("/api/categories/", {"name":"Cat1","description":"desc"}, format="json")
    assert r.status_code == 201
    cat_id = r.data["id"]

    # create product
    r = client.post("/api/products/", {"name":"P1","category":cat_id,"price":"9.99","stock":5}, format="json")
    assert r.status_code == 201
    prod_id = r.data["id"]

    # normal user login
    client.credentials()  # clear
    r = client.post(reverse("token_obtain_pair"), {"username":"u1","password":"userpass"}, format="json")
    user_token = r.data["access"]
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {user_token}")

    # create task assigned to self
    due = (timezone.now() + timedelta(days=1)).isoformat()
    r = client.post("/api/tasks/", {"title":"T1","product":prod_id,"assigned_user":user.id,"due_date":due}, format="json")
    assert r.status_code == 201
    # list tasks -> user sees their own
    r = client.get("/api/tasks/")
    assert r.status_code == 200
    assert any(t["title"] == "T1" for t in r.json())

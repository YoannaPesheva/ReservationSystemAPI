"""
This module is used for testing the platform.
"""

import unittest
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, StaticPool
from sqlalchemy.orm import sessionmaker

from main import app
from database import get_db, Base

SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
LOCAL_TESTING_SESSION = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    """
    This function is used to override the database with a local
    testing session.
    """
    try:
        db = LOCAL_TESTING_SESSION()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


class APITests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """
        This function is used to set up the test environment.
        It creates all database tables, adds some
        test accounts as well.
        """
        Base.metadata.create_all(bind=engine)
        cls.client = TestClient(app)

        cls.user_creds = {"email": "user@test.com", "password": "password123"}
        cls.provider_creds = {"email": "provider@test.com", "password": "password123"}

        cls.client.post(
            "/register",
            json={
                "email": cls.user_creds["email"],
                "password": cls.user_creds["password"],
                "role": "user",
            },
        )
        cls.client.post(
            "/register",
            json={
                "email": cls.provider_creds["email"],
                "password": cls.provider_creds["password"],
                "role": "provider",
            },
        )

    @classmethod
    def tearDownClass(cls):
        """
        This function is used to drop everything
        after the testing has finished.
        """
        Base.metadata.drop_all(bind=engine)

    def get_auth_header(self, email, password):
        """
        This is a helper function 
        and it is used to login a user
        and get a token.
        """
        response = self.client.post(
            "/token", data={"username": email, "password": password}
        )
        if response.status_code != 200:
            print(f"Login failed for {email}: {response.json()}")
        token = response.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}


    def test_auth_flow(self):
        """
        This function is for testing all cases that have
        to do with registering and logging in.
        """
        # trying to register with the same email
        res = self.client.post(
            "/register",
            json={
                "email": self.user_creds["email"],
                "password": "newpass",
                "role": "user",
            },
        )
        self.assertEqual(res.status_code, 400)

        # trying to register with a role - admin
        res = self.client.post(
            "/register",
            json={"email": "admin_fake@test.com", "password": "pass", "role": "admin"},
        )
        self.assertEqual(res.status_code, 403)

        # testing if logging in works normally
        res = self.client.post(
            "/token",
            data={
                "username": self.user_creds["email"],
                "password": self.user_creds["password"],
            },
        )
        self.assertEqual(res.status_code, 200)
        self.assertIn("access_token", res.json())

        # trying to login with a wrong password
        res = self.client.post(
            "/token",
            data={"username": self.user_creds["email"], "password": "wrongpassword"},
        )
        self.assertEqual(res.status_code, 400)


    def test_user_management(self):
        """
        This is for testing the user's information profile, 
        like get and update the profile.
        """
        headers = self.get_auth_header(
            self.user_creds["email"], self.user_creds["password"]
        )

        # try to get my account
        res = self.client.get("/users/me", headers=headers)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["email"], self.user_creds["email"])

        # try to update my account
        new_email = "user_updated@test.com"
        res = self.client.put(
            "/users/me",
            json={"email": new_email, "password": "password123", "role": "user"},
            headers=headers,
        )

        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["email"], new_email)

        # put back the email we changed, so its fine
        # for next tests
        self.client.put(
            "/users/me",
            json={
                "email": self.user_creds["email"],
                "password": "password123",
                "role": "user",
            },
            headers=headers,
        )


    def test_hall(self):
        """
        This module is testing everything that 
        has to do with halls.
        """
        provider_headers = self.get_auth_header(
            self.provider_creds["email"], self.provider_creds["password"]
        )
        user_headers = self.get_auth_header(
            self.user_creds["email"], self.user_creds["password"]
        )

        # try to create a hall as a provider
        hall_data = {
            "name": "Grand Hall",
            "category": "Wedding",
            "capacity": 100,
            "price_per_hour": 50.0,
            "location": "Downtown",
        }
        res = self.client.post("/halls/", json=hall_data, headers=provider_headers)
        self.assertEqual(res.status_code, 201)
        hall_id = res.json()["id"]

        # try to create a hall as a user
        res = self.client.post("/halls/", json=hall_data, headers=user_headers)
        self.assertEqual(res.status_code, 403)

        # get a specific hall
        res = self.client.get(f"/halls/{hall_id}")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["name"], "Grand Hall")

        # try to search for halls with some minimum capacity
        res = self.client.get("/halls/search?search=Grand&min_capacity=50")
        self.assertEqual(res.status_code, 200)
        self.assertTrue(len(res.json()) > 0)

        # try to update a hall (as provider)
        updated_data = {
            "name": "Grand Hall Updated",
            "category": "Wedding",
            "capacity": 100,
            "price_per_hour": 50.0,
            "location": "Downtown",
        }
        res = self.client.put(
            f"/halls/{hall_id}", json=updated_data, headers=provider_headers
        )
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["name"], "Grand Hall Updated")

        # add favourites
        res = self.client.post(f"/users/favourites/{hall_id}", headers=user_headers)
        self.assertEqual(res.status_code, 201)

        # get favourites
        res = self.client.get("/users/favourites", headers=user_headers)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()[0]["id"], hall_id)


    def test_reservation_flow(self):
        """
        This function tests everything that has
        to do with the reservations.
        """
        provider_headers = self.get_auth_header(
            self.provider_creds["email"], self.provider_creds["password"]
        )
        # have to create a hall to reserve
        res = self.client.post(
            "/halls/",
            json={
                "name": "Party Room",
                "category": "Party",
                "capacity": 20,
                "price_per_hour": 100,
                "location": "City",
            },
            headers=provider_headers,
        )
        hall_id = res.json()["id"]

        user_headers = self.get_auth_header(
            self.user_creds["email"], self.user_creds["password"]
        )

        # create a normal reservation
        start_time = (datetime.now() + timedelta(days=1)).isoformat()
        end_time = (datetime.now() + timedelta(days=1, hours=2)).isoformat()

        res = self.client.post(
            "/reservations/",
            json={
                "hall_id": hall_id,
                "start_time": start_time,
                "end_time": end_time,
                "notes": "Birthday",
            },
            headers=user_headers,
        )
        self.assertEqual(res.status_code, 200)
        reservation_id = res.json()["id"]

        # try to create an overlapping reservation
        res = self.client.post(
            "/reservations/",
            json={"hall_id": hall_id, "start_time": start_time, "end_time": end_time},
            headers=user_headers,
        )
        self.assertEqual(res.status_code, 400)

        # get the reservations for users
        res = self.client.get("/reservations/", headers=user_headers)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(len(res.json()), 1)

        # try to update the status to confirmed as a provider
        res = self.client.patch(
            f"/reservations/{reservation_id}/status?new_status=confirmed",
            headers=provider_headers,
        )
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["status"], "confirmed")

        # try to update the status to confirmed as a user
        res = self.client.patch(
            f"/reservations/{reservation_id}/status?new_status=confirmed",
            headers=user_headers,
        )
        self.assertEqual(res.status_code, 403)

        # try to update the status to completed as a user
        res = self.client.patch(
            f"/reservations/{reservation_id}/status?new_status=completed",
            headers=user_headers,
        )
        self.assertEqual(res.status_code, 403)

        # try to update the status to cancelled as a provider
        res = self.client.patch(
            f"/reservations/{reservation_id}/status?new_status=cancelled",
            headers=provider_headers,
        )
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["status"], "cancelled")


    def test_reviews(self):
        """
        This is used to test everything that has to do with reviews of halls.
        """
        provider_headers = self.get_auth_header(
            self.provider_creds["email"], self.provider_creds["password"]
        )
        # have to create a hall to review
        res = self.client.post(
            "/halls/",
            json={
                "name": "Review Hall",
                "category": "Test",
                "capacity": 10,
                "price_per_hour": 10,
                "location": "Test",
            },
            headers=provider_headers,
        )
        hall_id = res.json()["id"]

        user_headers = self.get_auth_header(
            self.user_creds["email"], self.user_creds["password"]
        )

        # try create a review
        res = self.client.post(
            "/reviews/",
            json={"hall_id": hall_id, "rating": 5, "comment": "Great!"},
            headers=user_headers,
        )

        self.assertEqual(res.status_code, 201)
        review_id = res.json()["id"]

        # try to review the same hall again
        res = self.client.post(
            "/reviews/",
            json={"hall_id": hall_id, "rating": 3, "comment": "Again"},
            headers=user_headers,
        )
        self.assertEqual(res.status_code, 400)

        # try to get reviews for a specific hall
        res = self.client.get(f"/reviews/hall/{hall_id}")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(len(res.json()), 1)

        # delete a review
        res = self.client.delete(f"/reviews/{review_id}", headers=user_headers)
        self.assertEqual(res.status_code, 204)


if __name__ == "__main__":
    unittest.main()

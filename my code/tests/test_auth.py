import unittest
from backend.app import create_app
from backend.database.db import db
from backend.database.models import User

def json_response(resp):
    try:
        return resp.get_json()
    except Exception:
        return None

class AuthTest(unittest.TestCase):
    def setUp(self):
        app = create_app('testing')
        self.app = app
        self.client = app.test_client()
        with app.app_context():
            db.create_all()

    def tearDown(self):
        with self.app.app_context():
            db.drop_all()

    def test_register_and_login(self):
        # register a new user
        resp = self.client.post('/auth/register', json={
            'email': 'alice@example.com',
            'password': 'secret',
            'role': 'client'
        })
        self.assertEqual(resp.status_code, 201)
        data = json_response(resp)
        self.assertIn('token', data)
        self.assertEqual(data['user']['email'], 'alice@example.com')

        # login with correct creds
        resp2 = self.client.post('/auth/login', json={
            'email': 'alice@example.com',
            'password': 'secret'
        })
        self.assertEqual(resp2.status_code, 200)
        data2 = json_response(resp2)
        self.assertIn('token', data2)

        # use token to hit /auth/me
        token = data2['token']
        resp3 = self.client.get('/auth/me', headers={'Authorization': f'Bearer {token}'})
        self.assertEqual(resp3.status_code, 200)
        data3 = json_response(resp3)
        self.assertEqual(data3['user']['email'], 'alice@example.com')

    def test_bad_login(self):
        resp = self.client.post('/auth/login', json={'email': 'none', 'password': 'no'})
        self.assertEqual(resp.status_code, 401)

    def test_register_duplicate(self):
        self.client.post('/auth/register', json={'email': 'bob@example.com', 'password': 'x'})
        resp = self.client.post('/auth/register', json={'email': 'bob@example.com', 'password': 'x'})
        self.assertEqual(resp.status_code, 400)

if __name__ == '__main__':
    unittest.main()

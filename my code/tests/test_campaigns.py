"""Tests for campaign management endpoints."""
import unittest
from backend.app import create_app


class CampaignsTest(unittest.TestCase):
    def setUp(self):
        self.app = create_app('testing')
        self.app_context = self.app.app_context()
        self.app_context.push()
        from backend.database.db import db
        db.create_all()
        self.client = self.app.test_client()

        # create and login a user to obtain auth token
        resp = self.client.post('/auth/register', json={
            'email': 'tester@example.com',
            'password': 'pw',
            'role': 'client'
        })
        self.token = resp.get_json()['token']

    def tearDown(self):
        from backend.database.db import db
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_create_and_list(self):
        payload = {
            'name': 'Test',
            'slug': 'test-camp',
            'target_url': 'https://example.com',
            'cpc': 1.5,
            'budget': 100.0
        }
        resp = self.client.post('/campaigns', json=payload,
                                headers={'Authorization': f'Bearer {self.token}'})
        self.assertEqual(resp.status_code, 201)
        data = resp.json
        # slug is now auto-generated with random suffix for uniqueness
        self.assertIn('test_camp', data['slug'])
        # tracking_id should be generated with cmp_ prefix
        self.assertTrue(data['tracking_id'].startswith('cmp_'))

        # list should include created campaign
        resp2 = self.client.get('/campaigns', headers={'Authorization': f'Bearer {self.token}'})
        self.assertEqual(len(resp2.json), 1)

    def test_update_and_pause_and_stats(self):
        # create first
        payload = {
            'name': 'Foo',
            'slug': 'foo',
            'target_url': 'https://foo.com',
        }
        resp = self.client.post('/campaigns', json=payload,
                                headers={'Authorization': f'Bearer {self.token}'})
        cid = resp.json['id']
        # update
        resp = self.client.put(f'/campaigns/{cid}', json={'cpc': 2.0, 'budget': 50}, headers={'Authorization': f'Bearer {self.token}'})
        self.assertEqual(resp.json['cpc'], 2.0)
        # pause
        resp = self.client.post(f'/campaigns/{cid}/pause', headers={'Authorization': f'Bearer {self.token}'})
        self.assertEqual(resp.json['status'], 'paused')
        # stats initially empty
        resp = self.client.get(f'/campaigns/{cid}/stats')
        self.assertEqual(resp.json['clicks'], 0)
        self.assertEqual(resp.json['budget'], 50)


if __name__ == '__main__':
    unittest.main()

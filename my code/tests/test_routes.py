"""Ensure that all routes are registered automatically."""
import unittest
from backend.app import create_app


class RoutesTest(unittest.TestCase):
    def setUp(self):
        self.app = create_app('testing')
        self.app_context = self.app.app_context()
        self.app_context.push()
        # create in‑memory tables and sample campaign
        from backend.database.db import db
        from backend.database.models import Campaign

        db.create_all()
        from backend.utils.hash import generate_tracking_id
        campaign = Campaign(
            name='Example',
            slug='test',
            target_url='https://example.com',
            tracking_id=generate_tracking_id(prefix='cmp_'),
        )
        db.session.add(campaign)
        db.session.commit()

        self.client = self.app.test_client()

    def tearDown(self):
        from backend.database.db import db
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_redirect_blueprint_registered(self):
        # HEAD should redirect (no body)
        resp = self.client.head('/r/test', follow_redirects=False)
        self.assertEqual(resp.status_code, 302)
        self.assertIn('Location', resp.headers)

    def test_redirect_logs_click(self):
        from backend.database.models import Click
        resp = self.client.get('/r/test', follow_redirects=False)
        self.assertEqual(resp.status_code, 302)
        # ensure a click record was created
        clicks = Click.query.all()
        self.assertEqual(len(clicks), 1)
        self.assertEqual(clicks[0].campaign_id, 1)
        self.assertEqual(resp.headers['Location'], 'https://example.com')

    def test_duplicate_header_present(self):
        # first click creates normal entry
        self.client.get('/r/test', follow_redirects=False)
        resp = self.client.get('/r/test', follow_redirects=False)
        # second request within duplicate window should still redirect
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(resp.headers.get('X-Click-Status'), 'duplicate')

    def test_campaigns_route_exists(self):
        resp = self.client.get('/campaigns')
        self.assertEqual(resp.status_code, 200)
        # at least the sample campaign created in setUp should appear
        self.assertGreaterEqual(len(resp.json), 1)

    def test_analytics_route_exists(self):
        resp = self.client.get('/analytics/client')
        self.assertEqual(resp.status_code, 200)
        self.assertIn('total_clicks', resp.json)


if __name__ == '__main__':
    unittest.main()

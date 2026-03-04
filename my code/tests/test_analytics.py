"""Tests for analytics endpoints."""
import unittest
from datetime import datetime, timedelta

from backend.app import create_app
from backend.database.db import db
from backend.database.models import Campaign, Click
from backend.utils.hash import generate_tracking_id


class AnalyticsTest(unittest.TestCase):
    def setUp(self):
        self.app = create_app('testing')
        self.ctx = self.app.app_context()
        self.ctx.push()
        db.create_all()
        # create two campaigns
        c1 = Campaign(name='One', slug='one', target_url='http://a', cpc=1.0, tracking_id=generate_tracking_id(prefix='cmp_'))
        c2 = Campaign(name='Two', slug='two', target_url='http://b', cpc=2.0, tracking_id=generate_tracking_id(prefix='cmp_'))
        db.session.add_all([c1, c2])
        db.session.commit()
        # add some clicks
        # add clicks using tracker so payout field is set
        from backend.services.tracker import track_click
        now = datetime.utcnow()
        track_click(c1.id, ip_address='1.1.1.1')
        track_click(c1.id, ip_address='2.2.2.2')
        track_click(c2.id, ip_address='3.3.3.3', affiliate_id=5)
        self.client = self.app.test_client()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.ctx.pop()

    def test_campaign_stats(self):
        resp = self.client.get('/analytics/campaign/1')
        self.assertEqual(resp.status_code, 200)
        data = resp.json
        self.assertIn('campaign', data)
        self.assertEqual(data['total_clicks'], 2)
        self.assertIsInstance(data['last_7_days'], list)

    def test_client_summary(self):
        resp = self.client.get('/analytics/client')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json['total_clicks'], 3)
        # spend = 1*2 + 2*1 = 4
        self.assertAlmostEqual(resp.json['spend'], 4.0)

    def test_affiliate_breakdown(self):
        resp = self.client.get('/analytics/affiliate')
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(any(d['affiliate_id'] == 5 for d in resp.json))

    def test_live_endpoint(self):
        resp = self.client.get('/analytics/live')
        self.assertEqual(resp.status_code, 200)
        self.assertIn('last_minute', resp.json)


if __name__ == '__main__':
    unittest.main()

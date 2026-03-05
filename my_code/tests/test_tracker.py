"""Unit tests for tracker service logic."""
import unittest
from datetime import timedelta, datetime

from backend.app import create_app
from backend.services.tracker import track_click
from backend.database.db import db
from backend.database.models import Campaign, Click
from backend.utils.hash import generate_tracking_id


class TrackerTest(unittest.TestCase):
    def setUp(self):
        self.app = create_app('testing')
        self.ctx = self.app.app_context()
        self.ctx.push()
        db.create_all()
        self.camp = Campaign(name='T', slug='t', target_url='http://x', cpc=1.0, budget=5.0, tracking_id=generate_tracking_id(prefix='cmp_'))
        db.session.add(self.camp)
        db.session.commit()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.ctx.pop()

    def test_basic_click_allowed(self):
        result = track_click(self.camp.id, ip_address='1.2.3.4')
        self.assertTrue(result['allowed'])
        self.assertEqual(result['click'].payout, 1.0)
        self.assertEqual(Campaign.query.get(self.camp.id).spend, 1.0)

    def test_duplicate_blocked(self):
        # first click
        track_click(self.camp.id, ip_address='1.2.3.4')
        # immediate duplicate
        result = track_click(self.camp.id, ip_address='1.2.3.4')
        self.assertFalse(result['allowed'])
        self.assertEqual(result['reason'], 'duplicate')
        self.assertEqual(result['click'].status, 'duplicate')

    def test_budget_pauses_campaign(self):
        # create 6 clicks to exceed budget
        for _ in range(6):
            track_click(self.camp.id, ip_address=str(datetime.utcnow().timestamp()))
        camp = Campaign.query.get(self.camp.id)
        self.assertEqual(camp.status, 'paused')

    def test_inactive_campaign(self):
        # manually pause
        self.camp.status = 'paused'
        db.session.commit()
        result = track_click(self.camp.id, ip_address='9.9.9.9')
        self.assertFalse(result['allowed'])
        self.assertEqual(result['reason'], 'campaign_inactive')


if __name__ == '__main__':
    unittest.main()

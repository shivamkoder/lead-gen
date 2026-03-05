"""Unit tests for tracking and routing helpers."""

import unittest
from backend.services.tracker import track_click
from backend.services.traffic_filter import is_valid_traffic
from backend.middleware.bot_detection import detect_bot


class TestRedirect(unittest.TestCase):
    def test_track_click_creates_entry(self):
        # call tracker with nonexistent campaign; should return a dict
        from backend.database.db import db
        # set up temporary app context
        from backend.app import create_app
        app = create_app('testing')
        with app.app_context():
            db.create_all()
            result = track_click(campaign_id=42, ip_address='1.2.3.4', user_agent='test-agent')
            self.assertIsInstance(result, dict)
            self.assertFalse(result['allowed'])
            self.assertEqual(result['reason'], 'campaign_inactive')
            db.drop_all()

    def test_tracker_accepts_affiliate(self):
        # tracker should accept affiliate_id argument without error
        from backend.app import create_app
        from backend.database.db import db
        app = create_app('testing')
        with app.app_context():
            db.create_all()
            res = track_click(campaign_id=42, affiliate_id=123)
            self.assertIsInstance(res, dict)
            self.assertFalse(res['allowed'])
            db.drop_all()

    def test_traffic_filter_rejects_bots(self):
        class DummyRequest:
            headers = {'User-Agent': 'Googlebot/2.1'}
        self.assertFalse(is_valid_traffic(DummyRequest()))
        self.assertTrue(is_valid_traffic(type('R',(object,),{'headers':{'User-Agent':'Mozilla/5.0'}})()))

    def test_bot_detection_helper(self):
        self.assertTrue(detect_bot('Some crawler bot'))
        self.assertFalse(detect_bot('Mozilla/5.0 (Windows NT 10.0; Win64; x64)'))


if __name__ == '__main__':
    unittest.main()

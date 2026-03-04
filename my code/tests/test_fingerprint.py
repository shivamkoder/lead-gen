"""Tests for fingerprinting and fraud detection."""
import unittest
from backend.app import create_app
from backend.database.db import db
from backend.database.models import Campaign, Click
from backend.utils.hash import generate_tracking_id
from backend.services.fingerprint import (
    generate_click_fingerprint,
    get_click_risk_score,
    _is_likely_vpn_proxy,
    _is_likely_bot_ua,
)


class FingerprintTest(unittest.TestCase):
    def setUp(self):
        self.app = create_app('testing')
        self.app_context = self.app.app_context()
        self.app_context.push()
        from backend.database.db import db
        db.create_all()
        self.client = self.app.test_client()

    def tearDown(self):
        from backend.database.db import db
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_bot_ua_detection(self):
        """Test that bot user agents are detected."""
        self.assertTrue(_is_likely_bot_ua('curl/7.68.0'))
        self.assertTrue(_is_likely_bot_ua('python-requests/2.28.0'))
        self.assertTrue(_is_likely_bot_ua('Selenium/4.0'))
        self.assertFalse(_is_likely_bot_ua('Mozilla/5.0 (Windows NT 10.0; Win64; x64)'))
        self.assertFalse(_is_likely_bot_ua('Chrome/91.0 Safari/537.36'))

    def test_vpn_detection_with_mock_request(self):
        """Test VPN/proxy detection with mock request object."""
        class MockRequest:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows)',
                'X-Forwarded-For': '1.2.3.4',
                'Via': 'proxy-server',
            }

        # Both X-Forwarded-For and Via = likely proxy
        self.assertTrue(_is_likely_vpn_proxy(MockRequest()))

    def test_fingerprint_consistency(self):
        """Test that same request produces same fingerprint."""
        class MockRequest:
            remote_addr = '192.168.1.1'
            headers = {
                'User-Agent': 'Mozilla/5.0',
                'Accept-Language': 'en-US',
                'Sec-CH-UA': 'test-browser',
            }

        fp1 = generate_click_fingerprint(MockRequest(), ip_address='192.168.1.1')
        fp2 = generate_click_fingerprint(MockRequest(), ip_address='192.168.1.1')
        self.assertEqual(fp1, fp2)
        # fingerprint should be hex SHA256 (64 chars)
        self.assertEqual(len(fp1), 64)

    def test_fingerprint_difference_with_ua_change(self):
        """Test that different user agents produce different fingerprints."""
        class MockRequest1:
            remote_addr = '192.168.1.1'
            headers = {
                'User-Agent': 'Mozilla/5.0 Chrome',
                'Accept-Language': 'en-US',
                'Sec-CH-UA': '',
            }

        class MockRequest2:
            remote_addr = '192.168.1.1'
            headers = {
                'User-Agent': 'Mozilla/5.0 Firefox',
                'Accept-Language': 'en-US',
                'Sec-CH-UA': '',
            }

        fp1 = generate_click_fingerprint(MockRequest1(), ip_address='192.168.1.1')
        fp2 = generate_click_fingerprint(MockRequest2(), ip_address='192.168.1.1')
        self.assertNotEqual(fp1, fp2)

    def test_risk_score_normal_browser(self):
        """Test risk scoring for normal browser request."""
        class MockRequest:
            remote_addr = '192.168.1.1'
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept': 'text/html,application/*,*/*',
                'Sec-CH-UA': '"Chrome";v="91"',
                'Sec-Fetch-Site': 'cross-site',
                'Sec-Fetch-Mode': 'navigate',
            }

        risk = get_click_risk_score(MockRequest())
        self.assertLess(risk['risk_score'], 0.3)
        self.assertEqual(risk['recommendation'], 'allow')
        self.assertFalse(risk['is_bot_ua'])
        self.assertFalse(risk['is_vpn'])

    def test_risk_score_bot_ua(self):
        """Test risk scoring for bot user agent."""
        class MockRequest:
            remote_addr = '192.168.1.1'
            headers = {
                'User-Agent': 'curl/7.68.0',
                'Accept-Language': 'en-US',
                'Accept': 'text/html',
            }

        risk = get_click_risk_score(MockRequest())
        self.assertGreaterEqual(risk['risk_score'], 0.5)
        self.assertTrue(risk['is_bot_ua'])

    def test_risk_score_missing_headers(self):
        """Test risk scoring with missing headers."""
        class MockRequest:
            remote_addr = '192.168.1.1'
            headers = {
                'User-Agent': 'Mozilla/5.0',
                # Missing Accept-Language, Accept
            }

        risk = get_click_risk_score(MockRequest())
        self.assertGreater(risk['risk_score'], 0.1)
        self.assertIn('missing_accept_language', risk['suspicious_headers'])

    def test_fingerprint_stored_in_click(self):
        """Test that fingerprint is stored when tracking a click."""
        # Create campaign
        camp = Campaign(name='Test', slug='test', target_url='https://example.com', cpc=1.0, tracking_id=generate_tracking_id(prefix='cmp_'))
        db.session.add(camp)
        db.session.commit()

        # Track with fingerprint
        from backend.services.tracker import track_click
        result = track_click(
            camp.id,
            ip_address='1.2.3.4',
            user_agent='test-ua',
            fingerprint='abc123def456',
            risk_score=0.1
        )

        self.assertTrue(result['allowed'])
        click = result['click']
        self.assertEqual(click.fingerprint, 'abc123def456')
        self.assertAlmostEqual(click.risk_score, 0.1)

        # Verify it was stored in DB
        stored = Click.query.get(click.id)
        self.assertEqual(stored.fingerprint, 'abc123def456')


if __name__ == '__main__':
    unittest.main()

"""Tests for visitor profiling and device detection."""
import unittest
from backend.app import create_app
from backend.database.db import db
from backend.database.models import Campaign, Click
from backend.utils.hash import generate_tracking_id
from backend.utils.helpers import (
    detect_device_type,
    extract_browser_name,
    get_referrer as get_ref_helper,
)


class VisitorProfilingTest(unittest.TestCase):
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

    def test_device_type_detection_mobile(self):
        """Test detection of mobile devices."""
        self.assertEqual(detect_device_type('Mozilla/5.0 (iPhone OS 14_6) AppleWebKit/605.1.15'), 'mobile')
        self.assertEqual(detect_device_type('Mozilla/5.0 (Linux; Android 11)'), 'mobile')
        self.assertEqual(detect_device_type('Mozilla/5.0 BlackBerry'), 'mobile')

    def test_device_type_detection_tablet(self):
        """Test detection of tablets."""
        self.assertEqual(detect_device_type('Mozilla/5.0 (iPad; CPU OS 14_6)'), 'tablet')
        self.assertEqual(detect_device_type('Mozilla/5.0 (Kindle Fire)'), 'tablet')

    def test_device_type_detection_desktop(self):
        """Test detection of desktop platforms."""
        self.assertEqual(detect_device_type('Mozilla/5.0 (Windows NT 10.0; Win64; x64)'), 'desktop')
        self.assertEqual(detect_device_type('Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)'), 'desktop')
        self.assertEqual(detect_device_type('Mozilla/5.0 (X11; Linux x86_64)'), 'desktop')

    def test_device_type_detection_bot(self):
        """Test detection of bots."""
        self.assertEqual(detect_device_type('Mozilla/5.0 (compatible; Googlebot/2.1)'), 'bot')
        self.assertEqual(detect_device_type('curl/7.68.0'), 'bot')
        self.assertEqual(detect_device_type('Mozilla/5.0 Crawler'), 'bot')

    def test_browser_detection_chrome(self):
        """Test Chrome detection."""
        self.assertEqual(extract_browser_name('Mozilla/5.0 Chrome/91.0'), 'chrome')
        self.assertEqual(extract_browser_name('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/91.0.4472.124'), 'chrome')

    def test_browser_detection_firefox(self):
        """Test Firefox detection."""
        self.assertEqual(extract_browser_name('Mozilla/5.0 Firefox/89.0'), 'firefox')
        self.assertEqual(extract_browser_name('Mozilla/5.0 (X11; Linux x86_64; rv:89.0) Gecko/20100101 Firefox/89.0'), 'firefox')

    def test_browser_detection_safari(self):
        """Test Safari detection."""
        self.assertEqual(extract_browser_name('Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 Safari/605.1.15'), 'safari')

    def test_browser_detection_edge(self):
        """Test Edge detection."""
        self.assertEqual(extract_browser_name('Mozilla/5.0 Edg/91.0'), 'edge')

    def test_browser_detection_ie(self):
        """Test IE detection."""
        self.assertEqual(extract_browser_name('Mozilla/4.0 (compatible; MSIE 9.0)'), 'ie')
        self.assertEqual(extract_browser_name('Mozilla/5.0 Trident/7.0'), 'ie')

    def test_click_stores_device_browser_referrer(self):
        """Test that Click model stores device, browser, and referrer."""
        # Create campaign
        camp = Campaign(name='Test', slug='test', target_url='https://example.com', cpc=1.0, tracking_id=generate_tracking_id(prefix='cmp_'))
        db.session.add(camp)
        db.session.commit()

        # Create click with full visitor data
        click = Click(
            campaign_id=camp.id,
            ip_address='203.0.113.1',
            user_agent='Mozilla/5.0 (iPhone OS)',
            device_type='mobile',
            browser='safari',
            referrer='https://google.com/search',
            fingerprint='abc123',
            risk_score=0.1,
            payout=1.0,
            status='ok',
        )
        db.session.add(click)
        db.session.commit()

        # Retrieve and verify
        stored = Click.query.get(click.id)
        self.assertEqual(stored.device_type, 'mobile')
        self.assertEqual(stored.browser, 'safari')
        self.assertEqual(stored.referrer, 'https://google.com/search')

    def test_click_tracking_with_visitor_data(self):
        """Test that track_click accepts and stores visitor profile."""
        from backend.services.tracker import track_click

        camp = Campaign(name='Test', slug='test', target_url='https://example.com', cpc=1.0, tracking_id=generate_tracking_id(prefix='cmp_'))
        db.session.add(camp)
        db.session.commit()

        result = track_click(
            camp.id,
            ip_address='198.51.100.1',
            user_agent='Mozilla/5.0 (Windows NT 10.0)',
            device_type='desktop',
            browser='chrome',
            referrer='https://fb.com',
            fingerprint='xyz789',
            risk_score=0.05,
        )

        self.assertTrue(result['allowed'])
        click = result['click']
        self.assertEqual(click.device_type, 'desktop')
        self.assertEqual(click.browser, 'chrome')
        self.assertEqual(click.referrer, 'https://fb.com')

    def test_redirect_endpoint_captures_visitor_data(self):
        """Test that /r/<slug> endpoint captures full visitor profile."""
        # Create campaign
        camp = Campaign(name='Test', slug='tracker-test', target_url='https://example.com', cpc=1.0, tracking_id=generate_tracking_id(prefix='cmp_'))
        db.session.add(camp)
        db.session.commit()

        # Hit redirect with mock headers
        resp = self.client.get(
            '/r/tracker-test',
            headers={
                'User-Agent': 'Mozilla/5.0 (iPhone OS 14_6) AppleWebKit/605.1.15',
                'Referer': 'https://twitter.com',
            },
            follow_redirects=False
        )

        # Verify redirect happened
        self.assertEqual(resp.status_code, 302)

        # Check that click was recorded with visitor data
        clicks = Click.query.all()
        self.assertEqual(len(clicks), 1)
        click = clicks[0]
        self.assertEqual(click.device_type, 'mobile')
        self.assertEqual(click.browser, 'safari')
        self.assertEqual(click.referrer, 'https://twitter.com')
        self.assertIsNotNone(click.fingerprint)


if __name__ == '__main__':
    unittest.main()

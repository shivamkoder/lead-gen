"""Tests for traffic_filter service."""
import unittest
import os
import time

from backend.services.traffic_filter import is_valid_traffic, _check_rate


class DummyReq:
    def __init__(self, ua, ip=None):
        self.headers = {'User-Agent': ua}
        self.remote_addr = ip


class TrafficFilterTest(unittest.TestCase):
    def setUp(self):
        # ensure blacklist environment cleared
        if 'BLACKLISTED_IPS' in os.environ:
            del os.environ['BLACKLISTED_IPS']
        if 'RATE_LIMIT_PER_MIN' in os.environ:
            del os.environ['RATE_LIMIT_PER_MIN']

    def test_bot_user_agent(self):
        req = DummyReq('Googlebot/2.1', '1.1.1.1')
        self.assertFalse(is_valid_traffic(req))
        req2 = DummyReq('Mozilla/5.0', '1.1.1.1')
        self.assertTrue(is_valid_traffic(req2))

    def test_empty_user_agent(self):
        req = DummyReq('', '2.2.2.2')
        self.assertFalse(is_valid_traffic(req))

    def test_blacklist(self):
        os.environ['BLACKLISTED_IPS'] = '3.3.3.3,4.4.4.4'
        # reload module variables by reimport
        from importlib import reload
        reload(__import__('backend.services.traffic_filter', fromlist=['']))
        req = DummyReq('Mozilla/5.0', '3.3.3.3')
        self.assertFalse(is_valid_traffic(req))
        req2 = DummyReq('Mozilla/5.0', '5.5.5.5')
        self.assertTrue(is_valid_traffic(req2))

    def test_rate_limit(self):
        # direct test of helper
        ip = '6.6.6.6'
        # reset history
        from backend.services import traffic_filter
        traffic_filter._history.clear()
        limit = 3
        os.environ['RATE_LIMIT_PER_MIN'] = str(limit)
        from importlib import reload
        reload(__import__('backend.services.traffic_filter', fromlist=['']))
        # call _check_rate three times should pass, fourth fail
        self.assertTrue(_check_rate(ip))
        self.assertTrue(_check_rate(ip))
        self.assertTrue(_check_rate(ip))
        self.assertFalse(_check_rate(ip))


if __name__ == '__main__':
    unittest.main()

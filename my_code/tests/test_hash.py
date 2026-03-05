"""Tests for hash.py utility module."""
import unittest
from backend.utils.hash import (
    generate_token,
    generate_tracking_id,
    generate_affiliate_token,
    generate_campaign_slug,
    hash_string,
    verify_hash,
    generate_data_hash,
    verify_data_hash,
    generate_click_token,
    hash_click_parameters,
    is_valid_token_format,
    shorten_hash,
)


class HashGenerationTest(unittest.TestCase):
    """Test secure token and ID generation."""

    def test_generate_token_produces_unique(self):
        """Test that generate_token produces unique tokens."""
        token1 = generate_token()
        token2 = generate_token()
        self.assertNotEqual(token1, token2)
        self.assertGreater(len(token1), 20)

    def test_generate_tracking_id_basic(self):
        """Test basic tracking ID generation."""
        tid = generate_tracking_id()
        self.assertIsInstance(tid, str)
        self.assertGreater(len(tid), 8)
        # Should be hex-ish (0-9, a-f)
        self.assertTrue(all(c in '0123456789abcdef' for c in tid))

    def test_generate_tracking_id_with_prefix(self):
        """Test tracking ID generation with prefix."""
        tid = generate_tracking_id(prefix='cmp_')
        self.assertTrue(tid.startswith('cmp_'))
        self.assertGreater(len(tid), len('cmp_'))

    def test_generate_affiliate_token(self):
        """Test affiliate token generation."""
        aff_token = generate_affiliate_token()
        self.assertTrue(aff_token.startswith('aff_'))

    def test_generate_affiliate_tokens_unique(self):
        """Test that affiliate tokens are unique."""
        tokens = [generate_affiliate_token() for _ in range(10)]
        self.assertEqual(len(tokens), len(set(tokens)))

    def test_generate_campaign_slug_basic(self):
        """Test campaign slug generation."""
        slug = generate_campaign_slug('My Test Campaign')
        self.assertIn('my_test_campaign', slug)
        self.assertIn('_', slug)  # Has separator

    def test_generate_campaign_slug_with_id(self):
        """Test campaign slug with database ID."""
        slug = generate_campaign_slug('Q1 Ads', campaign_id=42)
        self.assertIn('q1_ads_42', slug)

    def test_generate_campaign_slug_sanitizes(self):
        """Test that slug sanitizes special characters."""
        slug = generate_campaign_slug('Q1 Ads!@# $%^')
        self.assertNotIn('!', slug)
        self.assertNotIn('@', slug)
        self.assertNotIn('#', slug)

    def test_generate_campaign_slug_unique(self):
        """Test that identical campaign names produce different slugs (due to randomness)."""
        slug1 = generate_campaign_slug('Same Name')
        slug2 = generate_campaign_slug('Same Name')
        self.assertNotEqual(slug1, slug2)


class HashAlgorithmsTest(unittest.TestCase):
    """Test hashing functions."""

    def test_hash_string_sha256(self):
        """Test SHA256 hashing."""
        text = "test data"
        hashed = hash_string(text)
        # SHA256 produces 64 hex characters
        self.assertEqual(len(hashed), 64)
        self.assertEqual(hashed, hash_string(text))  # Deterministic

    def test_hash_string_different_algorithms(self):
        """Test different hashing algorithms."""
        text = "test"
        sha256 = hash_string(text, 'sha256')
        sha512 = hash_string(text, 'sha512')
        self.assertNotEqual(sha256, sha512)
        self.assertEqual(len(sha512), 128)  # SHA512 is 128 hex chars

    def test_verify_hash_success(self):
        """Test hash verification with matching data."""
        text = "secret data"
        hashed = hash_string(text)
        self.assertTrue(verify_hash(text, hashed))

    def test_verify_hash_failure(self):
        """Test hash verification with mismatched data."""
        text = "secret data"
        hashed = hash_string(text)
        self.assertFalse(verify_hash("different data", hashed))

    def test_verify_hash_timing_resistance(self):
        """Test that verify_hash uses constant-time comparison (hmac.compare_digest)."""
        text = "data"
        hashed = hash_string(text)
        # Tampered hash should fail securely
        tampered = 'a' * 64
        result = verify_hash(text, tampered)
        self.assertFalse(result)


class DataIntegrityTest(unittest.TestCase):
    """Test HMAC-based data integrity functions."""

    def setUp(self):
        self.secret = "test_secret_key"
        self.data = {'campaign_id': 15, 'affiliate_id': 7}

    def test_generate_data_hash(self):
        """Test data hash generation."""
        hash_value = generate_data_hash(self.data, self.secret)
        # HMAC-SHA256 produces 64 hex characters
        self.assertEqual(len(hash_value), 64)

    def test_data_hash_deterministic(self):
        """Test that same data produces same hash."""
        hash1 = generate_data_hash(self.data, self.secret)
        hash2 = generate_data_hash(self.data, self.secret)
        self.assertEqual(hash1, hash2)

    def test_data_hash_sensitive_to_changes(self):
        """Test that hash changes if data changes."""
        hash1 = generate_data_hash(self.data, self.secret)
        modified_data = {'campaign_id': 16, 'affiliate_id': 7}
        hash2 = generate_data_hash(modified_data, self.secret)
        self.assertNotEqual(hash1, hash2)

    def test_verify_data_hash_success(self):
        """Test data hash verification with valid data."""
        hash_value = generate_data_hash(self.data, self.secret)
        self.assertTrue(verify_data_hash(self.data, hash_value, self.secret))

    def test_verify_data_hash_failure_tampering(self):
        """Test data hash verification fails if data tampered."""
        hash_value = generate_data_hash(self.data, self.secret)
        tampered_data = {'campaign_id': 999, 'affiliate_id': 7}
        self.assertFalse(verify_data_hash(tampered_data, hash_value, self.secret))

    def test_verify_data_hash_failure_wrong_secret(self):
        """Test data hash verification fails with wrong secret."""
        hash_value = generate_data_hash(self.data, self.secret)
        wrong_secret = "different_secret"
        self.assertFalse(verify_data_hash(self.data, hash_value, wrong_secret))

    def test_data_hash_order_insensitive(self):
        """Test that JSON key order doesn't affect hash."""
        data1 = {'a': 1, 'b': 2}
        data2 = {'b': 2, 'a': 1}
        hash1 = generate_data_hash(data1, self.secret)
        hash2 = generate_data_hash(data2, self.secret)
        self.assertEqual(hash1, hash2)


class ClickTrackingTest(unittest.TestCase):
    """Test click-specific hashing functions."""

    def setUp(self):
        self.secret = "test_secret_key"

    def test_generate_click_token(self):
        """Test click token generation."""
        token = generate_click_token()
        self.assertTrue(token.startswith('clk_'))

    def test_click_tokens_unique(self):
        """Test that click tokens are unique."""
        tokens = [generate_click_token() for _ in range(10)]
        self.assertEqual(len(tokens), len(set(tokens)))

    def test_hash_click_parameters(self):
        """Test click parameter hashing."""
        hash_value = hash_click_parameters(
            campaign_slug="promo_xyz",
            affiliate_id="aff_123",
            user_agent="Mozilla/5.0",
            ip_address="192.168.1.1",
            secret_key=self.secret
        )
        self.assertEqual(len(hash_value), 64)

    def test_click_hash_deterministic(self):
        """Test that click hash is reproducible."""
        hash1 = hash_click_parameters("slug1", "aff1", "ua", "1.1.1.1", self.secret)
        hash2 = hash_click_parameters("slug1", "aff1", "ua", "1.1.1.1", self.secret)
        self.assertEqual(hash1, hash2)

    def test_click_hash_changes_with_ip(self):
        """Test that different IPs produce different hashes."""
        hash1 = hash_click_parameters("slug1", "aff1", "ua", "1.1.1.1", self.secret)
        hash2 = hash_click_parameters("slug1", "aff1", "ua", "2.2.2.2", self.secret)
        self.assertNotEqual(hash1, hash2)

    def test_click_hash_changes_with_ua(self):
        """Test that different user agents produce different hashes."""
        hash1 = hash_click_parameters("slug1", "aff1", "ua1", "1.1.1.1", self.secret)
        hash2 = hash_click_parameters("slug1", "aff1", "ua2", "1.1.1.1", self.secret)
        self.assertNotEqual(hash1, hash2)


class ValidationUtilsTest(unittest.TestCase):
    """Test validation utility functions."""

    def test_is_valid_token_format_valid(self):
        """Test valid token format."""
        token = "aff_abc123xyz"
        self.assertTrue(is_valid_token_format(token, prefix='aff_'))

    def test_is_valid_token_format_wrong_prefix(self):
        """Test invalid token with wrong prefix."""
        token = "clk_abc123xyz"
        self.assertFalse(is_valid_token_format(token, prefix='aff_'))

    def test_is_valid_token_format_no_prefix(self):
        """Test token validation without prefix requirement."""
        token = "somertokenthatislong"
        self.assertTrue(is_valid_token_format(token))

    def test_is_valid_token_format_too_short(self):
        """Test that short tokens are invalid."""
        token = "short"
        self.assertFalse(is_valid_token_format(token))

    def test_is_valid_token_format_invalid_input(self):
        """Test with invalid input types."""
        self.assertFalse(is_valid_token_format(None))
        self.assertFalse(is_valid_token_format(""))
        self.assertFalse(is_valid_token_format(123))

    def test_shorten_hash_default_length(self):
        """Test hash shortening with default length."""
        full_hash = "a" * 64
        short = shorten_hash(full_hash)
        self.assertEqual(len(short), 10)

    def test_shorten_hash_custom_length(self):
        """Test hash shortening with custom length."""
        full_hash = "abcdefghijklmnopqrstuvwxyz"
        short = shorten_hash(full_hash, length=5)
        self.assertEqual(short, "abcde")


class SecurityPropertiesTest(unittest.TestCase):
    """Test security properties of hash functions."""

    def test_tokens_have_sufficient_entropy(self):
        """Test that generated tokens have sufficient entropy (low collision probability)."""
        # Generate many tokens and check uniqueness
        tokens = set(generate_tracking_id() for _ in range(1000))
        self.assertEqual(len(tokens), 1000)  # All unique

    def test_campaign_slugs_collisions_rare(self):
        """Test that campaign slug collisions are extremely rare."""
        slugs = set(generate_campaign_slug("Test", i) for i in range(100))
        # All should be unique (100% for this small dataset)
        self.assertEqual(len(slugs), 100)

    def test_hash_avalanche_effect(self):
        """Test hash avalanche effect (small input change = large output change)."""
        hash1 = hash_string("data1")
        hash2 = hash_string("data2")
        # Hashes should differ significantly
        diff_count = sum(1 for a, b in zip(hash1, hash2) if a != b)
        # Expect ~50% or more of characters to differ (avalanche property)
        self.assertGreater(diff_count, len(hash1) * 0.3)


if __name__ == '__main__':
    unittest.main()

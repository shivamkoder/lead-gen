"""
Payout Service
Handle affiliate payouts and payment processing
"""

from datetime import datetime
from app.extensions import db
from app.models import Affiliate, Payout


class PayoutService:
    """Service for processing affiliate payouts"""
    
    MINIMUM_PAYOUT = 50.0  # Minimum amount for payout
    
    def __init__(self):
        self.supported_methods = ['paypal', 'bank_transfer', 'crypto', 'wire']
    
    def process_payout(self, payout_id):
        """Process a pending payout"""
        payout = Payout.query.get(payout_id)
        if not payout:
            raise ValueError('Payout not found')
        
        if payout.status != 'pending':
            raise ValueError('Payout is not in pending status')
        
        # Process based on payment method
        if payout.payment_method == 'paypal':
            return self._process_paypal(payout)
        elif payout.payment_method == 'bank_transfer':
            return self._process_bank_transfer(payout)
        elif payout.payment_method == 'crypto':
            return self._process_crypto(payout)
        elif payout.payment_method == 'wire':
            return self._process_wire(payout)
        else:
            raise ValueError(f'Unsupported payment method: {payout.payment_method}')
    
    def _process_paypal(self, payout):
        """Process PayPal payout"""
        # In production, integrate with PayPal API
        # This is a placeholder implementation
        
        affiliate = payout.affiliate
        if not affiliate.payment_email:
            raise ValueError('No payment email on file')
        
        # Simulate payment processing
        payout.status = 'processing'
        payout.payment_reference = f"PP-{payout.id}-{datetime.utcnow().timestamp()}"
        db.session.commit()
        
        # In production, call PayPal API here
        # After successful processing:
        payout.status = 'completed'
        payout.processed_at = datetime.utcnow()
        db.session.commit()
        
        return {
            'status': 'success',
            'payout_id': payout.id,
            'reference': payout.payment_reference
        }
    
    def _process_bank_transfer(self, payout):
        """Process bank transfer"""
        # In production, integrate with banking API
        
        payout.status = 'processing'
        payout.payment_reference = f"BK-{payout.id}-{datetime.utcnow().timestamp()}"
        db.session.commit()
        
        # Simulate processing delay
        payout.status = 'completed'
        payout.processed_at = datetime.utcnow()
        db.session.commit()
        
        return {
            'status': 'success',
            'payout_id': payout.id,
            'reference': payout.payment_reference
        }
    
    def _process_crypto(self, payout):
        """Process cryptocurrency payout"""
        # In production, integrate with crypto payment processor
        
        payout.status = 'processing'
        payout.payment_reference = f"CRYPTO-{payout.id}-{datetime.utcnow().timestamp()}"
        db.session.commit()
        
        payout.status = 'completed'
        payout.processed_at = datetime.utcnow()
        db.session.commit()
        
        return {
            'status': 'success',
            'payout_id': payout.id,
            'reference': payout.payment_reference
        }
    
    def _process_wire(self, payout):
        """Process wire transfer"""
        # In production, integrate with SWIFT wire system
        
        payout.status = 'processing'
        payout.payment_reference = f"WIRE-{payout.id}-{datetime.utcnow().timestamp()}"
        db.session.commit()
        
        # Wire transfers typically take 1-3 business days
        payout.status = 'completed'
        payout.processed_at = datetime.utcnow()
        db.session.commit()
        
        return {
            'status': 'success',
            'payout_id': payout.id,
            'reference': payout.payment_reference
        }
    
    def process_failed_payout(self, payout_id, reason):
        """Mark payout as failed"""
        payout = Payout.query.get(payout_id)
        if not payout:
            raise ValueError('Payout not found')
        
        payout.status = 'failed'
        
        # Refund to affiliate pending balance
        affiliate = payout.affiliate
        affiliate.pending_payout += payout.amount
        
        db.session.commit()
        
        return {
            'status': 'failed',
            'payout_id': payout.id,
            'reason': reason,
            'amount_refunded': payout.amount
        }
    
    def can_request_payout(self, affiliate_id):
        """Check if affiliate can request payout"""
        affiliate = Affiliate.query.get(affiliate_id)
        if not affiliate:
            return False, 'Affiliate not found'
        
        if affiliate.pending_payout < self.MINIMUM_PAYOUT:
            return False, f'Minimum payout amount is ${self.MINIMUM_PAYOUT}'
        
        # Check for pending payouts
        pending = Payout.query.filter_by(
            affiliate_id=affiliate_id,
            status='pending'
        ).first()
        
        if pending:
            return False, 'Already have a pending payout request'
        
        return True, None
    
    def get_payment_details(self, affiliate_id):
        """Get payment details for affiliate"""
        affiliate = Affiliate.query.get(affiliate_id)
        if not affiliate:
            return None
        
        return {
            'payment_email': affiliate.payment_email,
            'pending_balance': affiliate.pending_payout,
            'total_earnings': affiliate.total_earnings,
            'minimum_payout': self.MINIMUM_PAYOUT,
            'supported_methods': self.supported_methods
        }
    
    def calculate_fees(self, amount, method):
        """Calculate processing fees for payout"""
        fees = {
            'paypal': 0.029 + 0.30,  # 2.9% + $0.30
            'bank_transfer': 0.01,  # 1%
            'crypto': 0.01,  # 1%
            'wire': 25.00  # Flat fee
        }
        
        if method not in fees:
            raise ValueError(f'Unsupported payment method: {method}')
        
        if method == 'wire':
            return fees[method]
        
        return amount * fees[method]
    
    def calculate_net_payout(self, amount, method):
        """Calculate net payout after fees"""
        fees = self.calculate_fees(amount, method)
        return amount - fees

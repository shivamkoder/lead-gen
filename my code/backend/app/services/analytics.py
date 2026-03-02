"""
Analytics Service
Generate reports and analytics for campaigns and affiliates
"""

from datetime import datetime, timedelta
from sqlalchemy import func
from app.extensions import db
from app.models import Analytics, Campaign, Affiliate, Lead


class AnalyticsService:
    """Service for generating analytics and reports"""
    
    def get_campaign_analytics(self, campaign_id, start_date=None, end_date=None):
        """Get analytics for a specific campaign"""
        query = Analytics.query.filter_by(campaign_id=campaign_id)
        
        if start_date:
            query = query.filter(Analytics.created_at >= start_date)
        if end_date:
            query = query.filter(Analytics.created_at <= end_date)
        
        # Get event counts
        clicks = query.filter_by(event_type='click').count()
        leads = query.filter_by(event_type='lead').count()
        conversions = query.filter_by(event_type='conversion').count()
        
        # Get unique visitors (by IP)
        unique_visitors = db.session.query(
            func.count(func.distinct(Analytics.ip_address))
        ).filter(
            Analytics.campaign_id == campaign_id,
            Analytics.event_type == 'click'
        ).scalar() or 0
        
        return {
            'campaign_id': campaign_id,
            'clicks': clicks,
            'leads': leads,
            'conversions': conversions,
            'unique_visitors': unique_visitors,
            'click_to_lead_rate': (leads / clicks * 100) if clicks > 0 else 0,
            'lead_to_conversion_rate': (conversions / leads * 100) if leads > 0 else 0
        }
    
    def get_affiliate_analytics(self, affiliate_id, start_date=None, end_date=None):
        """Get analytics for a specific affiliate"""
        query = Analytics.query.filter_by(affiliate_id=affiliate_id)
        
        if start_date:
            query = query.filter(Analytics.created_at >= start_date)
        if end_date:
            query = query.filter(Analytics.created_at <= end_date)
        
        clicks = query.filter_by(event_type='click').count()
        leads = query.filter_by(event_type='lead').count()
        conversions = query.filter_by(event_type='conversion').count()
        
        # Get earnings
        affiliate = Affiliate.query.get(affiliate_id)
        
        return {
            'affiliate_id': affiliate_id,
            'clicks': clicks,
            'leads': leads,
            'conversions': conversions,
            'total_earnings': affiliate.total_earnings if affiliate else 0,
            'pending_payout': affiliate.pending_payout if affiliate else 0,
            'conversion_rate': (conversions / clicks * 100) if clicks > 0 else 0
        }
    
    def get_overall_analytics(self, days=30):
        """Get overall platform analytics"""
        start_date = datetime.utcnow() - timedelta(days=days)
        
        # Event counts
        clicks = Analytics.query.filter(
            Analytics.event_type == 'click',
            Analytics.created_at >= start_date
        ).count()
        
        leads = Analytics.query.filter(
            Analytics.event_type == 'lead',
            Analytics.created_at >= start_date
        ).count()
        
        conversions = Analytics.query.filter(
            Analytics.event_type == 'conversion',
            Analytics.created_at >= start_date
        ).count()
        
        # Active campaigns
        active_campaigns = Campaign.query.filter_by(status='active').count()
        
        # Active affiliates
        active_affiliates = Affiliate.query.filter_by(status='active').count()
        
        # Total earnings
        total_earnings = db.session.query(
            func.sum(Affiliate.total_earnings)
        ).scalar() or 0
        
        return {
            'period_days': days,
            'clicks': clicks,
            'leads': leads,
            'conversions': conversions,
            'active_campaigns': active_campaigns,
            'active_affiliates': active_affiliates,
            'total_earnings': float(total_earnings),
            'click_to_lead_rate': (leads / clicks * 100) if clicks > 0 else 0,
            'lead_to_conversion_rate': (conversions / leads * 100) if leads > 0 else 0
        }
    
    def get_daily_stats(self, days=30):
        """Get daily statistics"""
        start_date = datetime.utcnow() - timedelta(days=days)
        
        # Get daily clicks
        daily_clicks = db.session.query(
            func.date(Analytics.created_at).label('date'),
            func.count(Analytics.id).label('count')
        ).filter(
            Analytics.event_type == 'click',
            Analytics.created_at >= start_date
        ).group_by(func.date(Analytics.created_at)).all()
        
        # Get daily leads
        daily_leads = db.session.query(
            func.date(Analytics.created_at).label('date'),
            func.count(Analytics.id).label('count')
        ).filter(
            Analytics.event_type == 'lead',
            Analytics.created_at >= start_date
        ).group_by(func.date(Analytics.created_at)).all()
        
        # Convert to dict
        clicks_dict = {str(item.date): item.count for item in daily_clicks}
        leads_dict = {str(item.date): item.count for item in daily_leads}
        
        # Build result
        result = []
        for i in range(days):
            date = (datetime.utcnow() - timedelta(days=days-i-1)).date()
            date_str = str(date)
            result.append({
                'date': date_str,
                'clicks': clicks_dict.get(date_str, 0),
                'leads': leads_dict.get(date_str, 0)
            })
        
        return result
    
    def get_top_campaigns(self, limit=10):
        """Get top performing campaigns"""
        campaigns = db.session.query(
            Campaign.id,
            Campaign.name,
            func.count(Analytics.id).label('clicks')
        ).join(
            Analytics, Campaign.id == Analytics.campaign_id
        ).filter(
            Analytics.event_type == 'click'
        ).group_by(
            Campaign.id, Campaign.name
        ).order_by(
            func.count(Analytics.id).desc()
        ).limit(limit).all()
        
        return [{
            'id': c.id,
            'name': c.name,
            'clicks': c.clicks
        } for c in campaigns]
    
    def get_top_affiliates(self, limit=10):
        """Get top performing affiliates"""
        affiliates = db.session.query(
            Affiliate.id,
            Affiliate.referral_code,
            func.count(Analytics.id).label('clicks'),
            func.sum(Lead.payout_amount).label('earnings')
        ).join(
            Analytics, Affiliate.id == Analytics.affiliate_id
        ).outerjoin(
            Lead, Lead.affiliate_id == Affiliate.id
        ).filter(
            Analytics.event_type == 'click'
        ).group_by(
            Affiliate.id, Affiliate.referral_code
        ).order_by(
            func.count(Analytics.id).desc()
        ).limit(limit).all()
        
        return [{
            'id': a.id,
            'referral_code': a.referral_code,
            'clicks': a.clicks,
            'earnings': float(a.earnings or 0)
        } for a in affiliates]
    
    def get_lead_status_breakdown(self):
        """Get breakdown of lead statuses"""
        statuses = db.session.query(
            Lead.status,
            func.count(Lead.id).label('count')
        ).group_by(Lead.status).all()
        
        return {
            s.status: s.count for s in statuses
        }

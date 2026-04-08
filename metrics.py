import logging
from database import Database

logger = logging.getLogger(__name__)
db = Database()


class MetricsTracker:
    """Track analytics and metrics"""
    
    def track_user_start(self, user_id):
        """Track user starting the bot"""
        db.add_metric("user_start", user_id)
    
    def track_onboarding_complete(self, user_id):
        """Track onboarding completion"""
        db.add_metric("onboarding_complete", user_id)
    
    def track_onboarding_cancelled(self, user_id):
        """Track onboarding cancellation"""
        db.add_metric("onboarding_cancelled", user_id)
    
    def track_free_tips_view(self, user_id):
        """Track free tips preview view"""
        db.add_metric("free_tips_viewed", user_id)
    
    def track_payment_initiated(self, user_id, plan):
        """Track payment initiation"""
        db.add_metric("payment_initiated", user_id, plan=plan)
    
    def track_payment_successful(self, user_id, plan, amount):
        """Track successful payment"""
        db.add_metric("payment_successful", user_id, plan=plan, amount=amount)
    
    def get_conversion_stats(self):
        """Get conversion statistics"""
        all_starts = len(db.get_metrics("user_start"))
        onboarding_completes = len(db.get_metrics("onboarding_complete"))
        payments = len(db.get_metrics("payment_successful"))
        
        onboarding_rate = (onboarding_completes / all_starts * 100) if all_starts > 0 else 0
        conversion_rate = (payments / all_starts * 100) if all_starts > 0 else 0
        
        return {
            "total_starts": all_starts,
            "onboarding_completes": onboarding_completes,
            "successful_payments": payments,
            "onboarding_rate": f"{onboarding_rate:.1f}%",
            "conversion_rate": f"{conversion_rate:.1f}%",
        }
    
    def get_revenue_stats(self):
        """Get revenue statistics"""
        payments = db.get_metrics("payment_successful", limit=1000)
        total_revenue = sum([m.amount for m in payments if m.amount])
        
        return {
            "total_transactions": len(payments),
            "total_revenue": total_revenue,
            "avg_transaction": total_revenue / len(payments) if payments else 0,
        }
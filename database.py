import logging
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Float, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from config import Config

logger = logging.getLogger(__name__)
Base = declarative_base()


class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(String, unique=True)
    username = Column(String)
    first_name = Column(String)
    goal = Column(String)
    sport = Column(String)
    stake = Column(String)
    plan = Column(String)
    payment_id = Column(String)
    amount = Column(Float)
    currency = Column(String)
    status = Column(String, default="active")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Metric(Base):
    __tablename__ = "metrics"
    
    id = Column(Integer, primary_key=True)
    event_type = Column(String)
    user_id = Column(String)
    plan = Column(String)
    amount = Column(Float)
    meta_json = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)


class Database:
    def __init__(self):
        self.engine = create_engine(Config.DATABASE_URL, echo=Config.DEBUG)
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)
    
    def add_user(self, user_id, username, first_name, goal, sport, stake, plan, payment_id, amount, currency):
        """Add or update user"""
        try:
            session = self.Session()
            user = session.query(User).filter_by(user_id=str(user_id)).first()
            
            if user:
                user.username = username
                user.first_name = first_name
                user.goal = goal
                user.sport = sport
                user.stake = stake
                user.plan = plan
                user.payment_id = payment_id
                user.amount = amount
                user.currency = currency
                user.status = "active"
                user.updated_at = datetime.utcnow()
            else:
                user = User(
                    user_id=str(user_id),
                    username=username,
                    first_name=first_name,
                    goal=goal,
                    sport=sport,
                    stake=stake,
                    plan=plan,
                    payment_id=payment_id,
                    amount=amount,
                    currency=currency,
                    status="active"
                )
                session.add(user)
            
            session.commit()
            session.close()
            logger.info(f"✅ User {user_id} saved to database")
            return True
        except Exception as e:
            logger.error(f"❌ Error saving user: {e}")
            return False
    
    def get_user(self, user_id):
        """Get user by ID"""
        try:
            session = self.Session()
            user = session.query(User).filter_by(user_id=str(user_id)).first()
            session.close()
            return user
        except Exception as e:
            logger.error(f"Error fetching user: {e}")
            return None
    
    def get_active_users(self):
        """Get all active users"""
        try:
            session = self.Session()
            users = session.query(User).filter_by(status="active").all()
            session.close()
            return users
        except Exception as e:
            logger.error(f"Error fetching active users: {e}")
            return []
    
    def get_all_users(self):
        """Get all users"""
        try:
            session = self.Session()
            users = session.query(User).all()
            session.close()
            return users
        except Exception as e:
            logger.error(f"Error fetching users: {e}")
            return []
    
    def add_metric(self, event_type, user_id, plan=None, amount=None, metadata=None):
        """Track metric event"""
        try:
            session = self.Session()
            metric = Metric(
                event_type=event_type,
                user_id=str(user_id),
                plan=plan,
                amount=amount,
                metadata=metadata
            )
            session.add(metric)
            session.commit()
            session.close()
            logger.info(f"📊 Metric tracked: {event_type} for user {user_id}")
            return True
        except Exception as e:
            logger.error(f"Error tracking metric: {e}")
            return False
    
    def get_metrics(self, event_type=None, limit=100):
        """Get metrics"""
        try:
            session = self.Session()
            query = session.query(Metric)
            
            if event_type:
                query = query.filter_by(event_type=event_type)
            
            metrics = query.order_by(Metric.created_at.desc()).limit(limit).all()
            session.close()
            return metrics
        except Exception as e:
            logger.error(f"Error fetching metrics: {e}")
            return []

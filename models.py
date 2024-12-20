from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timezone

db = SQLAlchemy()  # Object Relational Mapping (ORM) framework


# User Table
class UserAccount(db.Model):
    __tablename__ = 'UserAccount'
    UserID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    UserName = db.Column(db.String(100), unique=True, nullable=False)
    PasswordHash = db.Column(db.String(256))
    UserRole = db.Column(db.String(20))
    CreatedAt = db.Column(db.DateTime, default=datetime.now(timezone.utc))
    PrimaryContact = db.Column(db.String(100))
    Region = db.Column(db.String(50))


# Quote Table
class Quote(db.Model):
    __tablename__ = 'Quote'
    QuoteID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    CustomerID = db.Column(db.Integer, db.ForeignKey('UserAccount.UserID'))
    PolicyType = db.Column(db.String(50))
    SubProduct = db.Column(db.String(50))
    RiskScore = db.Column(db.Numeric(5, 2))
    PremiumQuoted = db.Column(db.Numeric(18, 2))
    GeneratedAt = db.Column(db.DateTime, default=datetime.now(timezone.utc))
    Status = db.Column(db.String(20))


# Policy Table
class Policy(db.Model):
    __tablename__ = 'Policy'
    PolicyID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    CustomerID = db.Column(db.Integer, db.ForeignKey('UserAccount.UserID'))
    QuoteID = db.Column(db.Integer, db.ForeignKey('Quote.QuoteID'))
    PolicyType = db.Column(db.String(50))
    SubProduct = db.Column(db.String(50))
    EffectiveDate = db.Column(db.Date)
    PremiumAmount = db.Column(db.Numeric(18, 2))
    Status = db.Column(db.String(20))
    CreatedAt = db.Column(db.DateTime, default=datetime.now(timezone.utc))
    UpdatedAt = db.Column(db.DateTime, default=datetime.now(timezone.utc))


# Transaction Table
class PolicyTransaction(db.Model):
    __tablename__ = 'PolicyTransaction'
    TransactionID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    PolicyID = db.Column(db.Integer, db.ForeignKey('Policy.PolicyID'))
    CustomerID = db.Column(db.Integer, db.ForeignKey('UserAccount.UserID'))
    QuoteID = db.Column(db.Integer, db.ForeignKey('Quote.QuoteID'))
    PaymentAmount = db.Column(db.Numeric(18, 2))
    PaymentDate = db.Column(db.DateTime, default=datetime.now(timezone.utc))
    TransactionStatus = db.Column(db.String(20))

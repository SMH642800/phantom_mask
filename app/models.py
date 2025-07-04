from sqlalchemy import Column, Integer, Float, String, Time, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship, declarative_base


# SQLAlchemy declarative base for all ORM models
Base = declarative_base()



class Pharmacy(Base):
    """
    Pharmacy table: stores pharmacy info and cash balance.
    Relationships: opening hours, masks, transactions.
    """
    __tablename__ = 'pharmacies'

    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)
    cash_balance = Column(Float, nullable=False)

    opening_hours = relationship('OpeningHour', back_populates='pharmacy')
    masks = relationship('PharmacyMask', back_populates='pharmacy')
    transactions = relationship('Transaction', back_populates='pharmacy')



class OpeningHour(Base):
    """
    OpeningHour table: stores opening hours for each pharmacy.
    """
    __tablename__ = 'opening_hours'

    id = Column(Integer, primary_key=True)
    pharmacy_id = Column(Integer, ForeignKey('pharmacies.id'), nullable=False)
    day_of_week = Column(String, nullable=False)
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)
    is_overnight = Column(Boolean, default=False)

    pharmacy = relationship('Pharmacy', back_populates='opening_hours')



class Mask(Base):
    """
    Mask table: stores mask product info.
    Relationships: pharmacies selling this mask, transactions.
    """
    __tablename__ = 'masks'

    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)

    pharmacies = relationship('PharmacyMask', back_populates='mask')
    transactions = relationship('Transaction', back_populates='mask')



class PharmacyMask(Base):
    """
    PharmacyMask table: association table for pharmacy and mask, with price.
    """
    __tablename__ = 'pharmacy_masks'

    id = Column(Integer, primary_key=True)
    pharmacy_id = Column(Integer, ForeignKey('pharmacies.id'), nullable=False)
    mask_id = Column(Integer, ForeignKey('masks.id'), nullable=False)
    price = Column(Float, nullable=False)

    pharmacy = relationship('Pharmacy', back_populates='masks')
    mask = relationship('Mask', back_populates='pharmacies')



class User(Base):
    """
    User table: stores user info and cash balance.
    """
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)
    cash_balance = Column(Float, nullable=False)

    transactions = relationship('Transaction', back_populates='user')



class Transaction(Base):
    """
    Transaction table: records each mask purchase transaction.
    """
    __tablename__ = 'transactions'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    pharmacy_id = Column(Integer, ForeignKey('pharmacies.id'), nullable=False)
    mask_id = Column(Integer, ForeignKey('masks.id'), nullable=False)
    transaction_amount = Column(Float, nullable=False)
    transaction_date = Column(DateTime, nullable=False)

    user = relationship('User', back_populates='transactions')
    pharmacy = relationship('Pharmacy', back_populates='transactions')
    mask = relationship('Mask', back_populates='transactions')
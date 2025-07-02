from sqlalchemy import Column, Integer, Float, String, Time, DateTime, Boolean, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class Pharmacy(Base):
    __tablename__ = 'pharmacies'

    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)
    cash_balance = Column(Float, nullable=False)

    opening_hours = relationship('OpeningHour', back_populates='pharmacy')
    masks = relationship('PharmacyMask', back_populates='pharmacy')
    transactions = relationship('Transaction', back_populates='pharmacy')


class OpeningHour(Base):
    __tablename__ = 'opening_hours'

    id = Column(Integer, primary_key=True)
    pharmacy_id = Column(Integer, ForeignKey('pharmacies.id'), nullable=False)
    day_of_week = Column(String, nullable=False)
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)
    is_overnight = Column(Boolean, default=False)

    pharmacy = relationship('Pharmacy', back_populates='opening_hours')


class Mask(Base):
    __tablename__ = 'masks'

    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)

    pharmacies = relationship('PharmacyMask', back_populates='mask')
    transactions = relationship('Transaction', back_populates='mask')


class PharmacyMask(Base):
    __tablename__ = 'pharmacy_masks'

    id = Column(Integer, primary_key=True)
    pharmacy_id = Column(Integer, ForeignKey('pharmacies.id'), nullable=False)
    mask_id = Column(Integer, ForeignKey('masks.id'), nullable=False)
    price = Column(Float, nullable=False)

    pharmacy = relationship('Pharmacy', back_populates='masks')
    mask = relationship('Mask', back_populates='pharmacies')


class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)
    cash_balance = Column(Float, nullable=False)

    transactions = relationship('Transaction', back_populates='user')


class Transaction(Base):
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
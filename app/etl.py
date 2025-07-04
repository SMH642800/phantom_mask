import json
from datetime import datetime
from sqlalchemy.orm import Session

from app.models import Base, Pharmacy, OpeningHour, Mask, PharmacyMask, User, Transaction
from app.db import engine, SessionLocal
from app.utils.time_parser import parse_opening_hours


def load_pharmacies(session: Session, path: str):
    """
    Load pharmacy data from JSON file, including opening hours and masks sold.
    Avoids duplicate pharmacies and masks.
    """
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    for entry in data:
        # Check if pharmacy already exists
        pharmacy = session.query(Pharmacy).filter_by(name=entry["name"]).first()
        if not pharmacy:
            pharmacy = Pharmacy(
                name=entry["name"],
                cash_balance=entry["cashBalance"]
            )
            session.add(pharmacy)
            session.flush()
        else:
            # Optionally update cash balance if needed:
            pharmacy.cash_balance = entry["cashBalance"]

        # Load opening hours
        for opening_hours in parse_opening_hours(entry["openingHours"]):
            session.add(OpeningHour(
                pharmacy_id=pharmacy.id,
                day_of_week=opening_hours["day"],
                start_time=opening_hours["start"],
                end_time=opening_hours["end"],
                is_overnight=opening_hours["is_overnight"]
            ))

        # Load masks sold by pharmacy
        for mask_entry in entry["masks"]:
            mask = session.query(Mask).filter_by(name=mask_entry["name"]).first()
            if not mask:
                mask = Mask(name=mask_entry["name"])
                session.add(mask)
                session.flush()

            # Avoid duplicate PharmacyMask entries
            existing_pharmacyMask = session.query(PharmacyMask).filter_by(
                pharmacy_id=pharmacy.id,
                mask_id=mask.id
            ).first()
            if not existing_pharmacyMask:
                session.add(PharmacyMask(
                    pharmacy_id=pharmacy.id,
                    mask_id=mask.id,
                    price=mask_entry["price"]
                ))


def load_users(session: Session, path: str):
    """
    Load user data from JSON file, including purchase histories.
    Avoids duplicate users and transactions.
    """
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    for entry in data:
        # Check if user already exists
        user = session.query(User).filter_by(name=entry["name"]).first()
        if not user:
            user = User(
                name=entry["name"],
                cash_balance=entry["cashBalance"]
            )
            session.add(user)
            session.flush()
        else:
            # Optionally update user's cash balance
            user.cash_balance = entry["cashBalance"]

        # Load purchase histories
        for purchase in entry.get("purchaseHistories", []):
            pharmacy = session.query(Pharmacy).filter_by(name=purchase["pharmacyName"]).first()
            mask = session.query(Mask).filter_by(name=purchase["maskName"]).first()

            if pharmacy and mask:
                # Check if similar transaction already exists
                existing_transaction = session.query(Transaction).filter_by(
                    user_id=user.id,
                    pharmacy_id=pharmacy.id,
                    mask_id=mask.id,
                    transaction_amount=purchase["transactionAmount"],
                    transaction_date=datetime.strptime(purchase["transactionDate"], "%Y-%m-%d %H:%M:%S")
                ).first()

                if not existing_transaction:
                    transaction = Transaction(
                        user_id=user.id,
                        pharmacy_id=pharmacy.id,
                        mask_id=mask.id,
                        transaction_amount=purchase["transactionAmount"],
                        transaction_date=datetime.strptime(purchase["transactionDate"], "%Y-%m-%d %H:%M:%S")
                    )
                    session.add(transaction)

def main():
    """
    Main ETL entry point: create tables, load pharmacies and users, commit and close session.
    """
    Base.metadata.create_all(bind=engine)
    session = SessionLocal()

    print("🚚 Loading pharmacies...")
    load_pharmacies(session, "data/pharmacies.json")

    print("👥 Loading users...")
    load_users(session, "data/users.json")

    session.commit()
    session.close()
    print("✅ ETL complete!")


if __name__ == "__main__":
    main()

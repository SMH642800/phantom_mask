from app.models import User, Pharmacy, Mask, PharmacyMask
from app.api import pharmacies, purchase, summary, search, users

def setup_test_data(db):
    """
    Create test user, pharmacy, mask, and their relationship for testing.
    """
    user = User(name="TestUser", cash_balance=100.0)
    pharmacy = Pharmacy(name="TestPharmacy", cash_balance=0.0)
    mask = Mask(name="KF94")
    pharmacy_mask = PharmacyMask(pharmacy=pharmacy, mask=mask, price=10.0)

    db.add_all([user, pharmacy, mask, pharmacy_mask])
    db.commit()
    return user, pharmacy, mask

def _test_get_db_covered(get_db_func):
    """
    Cover the finally block of get_db generator to improve coverage.
    """
    gen = get_db_func()
    db = next(gen)
    assert db is not None
    try:
        next(gen)
    except StopIteration:
        pass

def test_pharmacies_get_db():
    _test_get_db_covered(pharmacies.get_db)

def test_purchase_get_db():
    _test_get_db_covered(purchase.get_db)

def test_summary_get_db():
    _test_get_db_covered(summary.get_db)

def test_search_get_db():
    _test_get_db_covered(search.get_db)

def test_users_get_db():
    _test_get_db_covered(users.get_db)


def test_purchase_success(client):
    """
    Test successful purchase flow.
    """
    db = next(client.app.dependency_overrides[client.app.dependency_overrides.keys().__iter__().__next__()]())
    user, pharmacy, mask = setup_test_data(db)

    payload = {
        "user_name": user.name,
        "items": [
            {
                "pharmacy_name": pharmacy.name,
                "mask_name": mask.name,
                "quantity": 2
            }
        ]
    }

    response = client.post("/purchase", json=payload)
    assert response.status_code == 200
    assert "message" in response.json()


def test_purchase_insufficient_funds(client):
    """
    Test purchase flow when user has insufficient funds.
    """
    db = next(client.app.dependency_overrides[client.app.dependency_overrides.keys().__iter__().__next__()]())
    user = User(name="LowFundsUser", cash_balance=5.0)
    pharmacy = Pharmacy(name="CheapPharmacy", cash_balance=0.0)
    mask = Mask(name="KN95")
    pharmacy_mask = PharmacyMask(pharmacy=pharmacy, mask=mask, price=20.0)

    db.add_all([user, pharmacy, mask, pharmacy_mask])
    db.commit()

    payload = {
        "user_name": user.name,
        "items": [
            {
                "pharmacy_name": pharmacy.name,
                "mask_name": mask.name,
                "quantity": 1
            }
        ]
    }

    response = client.post("/purchase", json=payload)
    assert response.status_code == 400
    assert response.json()["error"] == "Insufficient balance"


def test_purchase_invalid_user(client):
    payload = {
        "user_name": "NonExistentUser",
        "items": [
            {
                "pharmacy_name": "TestPharmacy",
                "mask_name": "KF94",
                "quantity": 1
            }
        ]
    }
    response = client.post("/purchase", json=payload)
    assert response.status_code == 404
    assert response.json()["error"] == "User not found"


def test_purchase_invalid_mask(client):
    db = next(client.app.dependency_overrides[client.app.dependency_overrides.keys().__iter__().__next__()]())
    user = User(name="User2", cash_balance=100.0)
    pharmacy = Pharmacy(name="NoMaskPharmacy", cash_balance=0.0)
    db.add_all([user, pharmacy])
    db.commit()

    payload = {
        "user_name": user.name,
        "items": [
            {
                "pharmacy_name": pharmacy.name,
                "mask_name": "NotExistMask",
                "quantity": 1
            }
        ]
    }

    response = client.post("/purchase", json=payload)
    assert response.status_code == 404
    assert response.json()["error"] == "Mask 'NotExistMask' not found"


def test_root(client):
    response = client.get("/")
    assert response.status_code == 200
    assert "message" in response.json()


def test_open_pharmacies_invalid_time(client):
    response = client.get("/pharmacies/open", params={"weekday": "Mon", "time_str": "bad"})
    assert response.status_code == 400


def test_open_pharmacies_success(client):
    response = client.get("/pharmacies/open", params={"weekday": "Mon", "time_str": "08:30"})
    assert response.status_code == 200


def test_search_pharmacy(client):
    response = client.get("/search", params={"query_name": "Test", "search_type": "pharmacy"})
    assert response.status_code == 200
    assert "data" in response.json()


def test_search_mask(client):
    response = client.get("/search", params={"query_name": "KF94", "search_type": "mask"})
    assert response.status_code == 200
    assert "data" in response.json()


def test_top_users_invalid_date(client):
    response = client.get("/users/top", params={"start_date": "bad", "end_date": "2025-07-01"})
    assert response.status_code == 400


def test_top_users_success(client):
    response = client.get("/users/top", params={"start_date": "2020-01-01", "end_date": "2030-01-01"})
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_summary_invalid_date(client):
    response = client.get("/summary", params={"start_date": "bad", "end_date": "2025-07-01"})
    assert response.status_code == 400


def test_summary_success(client):
    response = client.get("/summary", params={"start_date": "2020-01-01", "end_date": "2030-01-01"})
    assert response.status_code == 200
    assert "total_masks_sold" in response.json()


def test_filter_by_mask_count_invalid(client):
    response = client.get("/pharmacies/filter_by_mask_count_within_price_range", params={
        "min_price": 50,
        "max_price": 10,
        "count": 2,
        "comparison": "more"
    })
    assert response.status_code == 400


def test_filter_by_mask_count_success(client):
    response = client.get("/pharmacies/filter_by_mask_count_within_price_range", params={
        "min_price": 0,
        "max_price": 100,
        "count": 0,
        "comparison": "more"
    })
    assert response.status_code == 200
    assert "data" in response.json()

def test_get_masks_by_pharmacy_name(client):
    response = client.get("/pharmacies/TestPharmacy/masks")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_get_masks_by_pharmacy_name_invalid(client):
    response = client.get("/pharmacies/NotExist/masks")
    assert response.status_code == 404
    assert response.json()["error"] == "Pharmacy not found"


def test_get_masks_by_pharmacy_sorted_by_price(client):
    response = client.get("/pharmacies/TestPharmacy/masks", params={"sort_by": "price"})
    assert response.status_code == 200
    assert isinstance(response.json(), list)

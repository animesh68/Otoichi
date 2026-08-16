from pathlib import Path
import pytest

from app.db.models.catalog import Album, Artist, Track
from app.db.models.product import VinylProduct
from app.db.models.social_and_promo import Coupon
from app.db.models.user import User
from scripts.seed import seed_catalog_from_json, seed_coupons, seed_users


@pytest.mark.asyncio
async def test_seed_execution_and_idempotency(mongo_db):
    """Test seed execution from JSON file and verify that re-running is completely idempotent."""
    json_path = Path(__file__).parent.parent / "data" / "seed_data.json"
    assert json_path.exists()

    # 1. First run of seeder
    await seed_users()
    await seed_coupons()
    await seed_catalog_from_json(json_path)

    # Record counts
    users_count_1 = await User.count()
    artists_count_1 = await Artist.count()
    albums_count_1 = await Album.count()
    tracks_count_1 = await Track.count()
    products_count_1 = await VinylProduct.count()
    coupons_count_1 = await Coupon.count()

    assert users_count_1 == 2  # Admin + Customer
    assert artists_count_1 >= 4  # Fleetwood Mac, Radiohead, Steely Dan, Fela Kuti
    assert albums_count_1 == 2   # Rumours, OK Computer
    assert products_count_1 >= 4
    assert coupons_count_1 >= 3

    # 2. Second run of seeder (Idempotency test)
    await seed_users()
    await seed_coupons()
    await seed_catalog_from_json(json_path)

    # Verify counts remain exactly identical
    assert await User.count() == users_count_1
    assert await Artist.count() == artists_count_1
    assert await Album.count() == albums_count_1
    assert await Track.count() == tracks_count_1
    assert await VinylProduct.count() == products_count_1
    assert await Coupon.count() == coupons_count_1

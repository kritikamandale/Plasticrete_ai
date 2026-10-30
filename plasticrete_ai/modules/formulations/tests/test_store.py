import pytest
from modules.formulations.store import (
    init_db,
    create_formulation,
    get_formulation,
    list_formulations,
    update_formulation,
    duplicate_formulation,
    delete_formulation,
)


def test_formulation_crud():
    init_db()
    mix = {
        "plastic_type": "HDPE",
        "replacement_pct": 20.0,
        "particle_size_mm": 3.0,
        "wc_ratio": 0.42,
        "additive_type": "fly_ash",
        "additive_pct": 12.0,
        "curing_temp_c": 30.0,
        "curing_days": 28,
    }
    # Create
    record = create_formulation(
        name="Test Eco HDPE Mix",
        mix_params=mix,
        notes="Automated test record",
    )
    assert record is not None
    assert record["name"] == "Test Eco HDPE Mix"
    assert record["mix_params"]["plastic_type"] == "HDPE"
    fid = record["id"]

    # Read
    fetched = get_formulation(fid)
    assert fetched is not None
    assert fetched["id"] == fid

    # Update
    updated = update_formulation(fid, name="Updated Test Mix", notes="Modified notes")
    assert updated is not None
    assert updated["name"] == "Updated Test Mix"
    assert updated["notes"] == "Modified notes"

    # Duplicate
    cloned = duplicate_formulation(fid, new_name="Cloned Test Mix")
    assert cloned is not None
    assert cloned["name"] == "Cloned Test Mix"
    assert cloned["version"] == 2
    assert cloned["parent_id"] == fid

    # List & Search
    records = list_formulations(search="Updated Test Mix")
    assert any(r["id"] == fid for r in records)

    # Delete
    assert delete_formulation(fid) is True
    assert get_formulation(fid) is None
    assert delete_formulation(cloned["id"]) is True


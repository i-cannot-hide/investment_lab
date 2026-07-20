import json
from pathlib import Path

import pytest

from run_registry import find_entries, latest_entry, steps_path


def write_registry(runs_dir: Path, entries: list[dict]) -> None:
    path = runs_dir / "registry.jsonl"
    with open(path, "w") as f:
        for entry in entries:
            f.write(json.dumps(entry) + "\n")


@pytest.fixture
def runs_dir(tmp_path: Path) -> Path:
    write_registry(
        tmp_path,
        [
            {
                "id": "aa",
                "folder": "26-07-20_10-00_aa",
                "strategy": "hold",
                "assets": ["BTC"],
                "params": {},
            },
            {
                "id": "bb",
                "folder": "26-07-20_10-01_bb",
                "strategy": "hold",
                "assets": ["ETH"],
                "params": {},
            },
            {
                "id": "cc",
                "folder": "26-07-20_10-02_cc",
                "strategy": "buybelow",
                "assets": ["BTC"],
                "params": {"target_price": "20000"},
            },
            {
                "id": "dd",
                "folder": "26-07-20_10-03_dd",
                "strategy": "buybelow",
                "assets": ["BTC"],
                "params": {"target_price": "30000"},
            },
        ],
    )
    return tmp_path


def test_latest_by_strategy_only(runs_dir: Path):
    entry = latest_entry(runs_dir, strategy="hold")
    assert entry["id"] == "bb"


def test_filter_by_id(runs_dir: Path):
    entry = latest_entry(runs_dir, id="aa")
    assert entry["folder"] == "26-07-20_10-00_aa"


def test_filter_by_strategy_and_assets(runs_dir: Path):
    entry = latest_entry(runs_dir, strategy="hold", assets="BTC")
    assert entry["id"] == "aa"

    entry = latest_entry(runs_dir, strategy="hold", assets=["ETH"])
    assert entry["id"] == "bb"


def test_filter_by_params(runs_dir: Path):
    entry = latest_entry(
        runs_dir,
        strategy="buybelow",
        params={"target_price": "20000"},
    )
    assert entry["id"] == "cc"


def test_find_entries_returns_all_matches(runs_dir: Path):
    matches = find_entries(runs_dir, strategy="buybelow")
    assert [entry["id"] for entry in matches] == ["cc", "dd"]


def test_no_match_raises(runs_dir: Path):
    with pytest.raises(FileNotFoundError):
        latest_entry(runs_dir, strategy="hold", assets="SOL")


def test_steps_path(runs_dir: Path):
    entry = latest_entry(runs_dir, id="aa")
    assert steps_path(runs_dir, entry) == runs_dir / "26-07-20_10-00_aa" / "steps.jsonl"

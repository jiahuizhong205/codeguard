import pytest
from pathlib import Path
from codeguard.memory.store import MemoryStore


def test_save_and_load(tmp_workspace: Path):
    store = MemoryStore(tmp_workspace / ".codeguard" / "memory.json")
    store.save("test_framework", "convention", "pytest")
    entry = store.load("test_framework")
    assert entry is not None
    assert entry.value == "pytest"
    assert entry.category == "convention"


def test_load_nonexistent(tmp_workspace: Path):
    store = MemoryStore(tmp_workspace / ".codeguard" / "memory.json")
    entry = store.load("nonexistent")
    assert entry is None


def test_query_by_category(tmp_workspace: Path):
    store = MemoryStore(tmp_workspace / ".codeguard" / "memory.json")
    store.save("framework", "convention", "pytest")
    store.save("style", "convention", "black")
    store.save("decision1", "decision", "use mock LLM")
    results = store.query(category="convention")
    assert len(results) == 2


def test_clear(tmp_workspace: Path):
    store = MemoryStore(tmp_workspace / ".codeguard" / "memory.json")
    store.save("key1", "convention", "value1")
    store.clear("key1")
    assert store.load("key1") is None


def test_persistence_across_instances(tmp_workspace: Path):
    path = tmp_workspace / ".codeguard" / "memory.json"
    store1 = MemoryStore(path)
    store1.save("key", "convention", "value")
    store2 = MemoryStore(path)
    entry = store2.load("key")
    assert entry is not None
    assert entry.value == "value"

import pytest
import asyncio
from pathlib import Path
from codeguard.demo import (
    demo_1_guardrail_blocks_dangerous_action,
    demo_2_feedback_loop,
    demo_3_scope_fence,
)


@pytest.mark.asyncio
async def test_demo_1(tmp_path: Path):
    (tmp_path / ".codeguard").mkdir()
    (tmp_path / "skills").mkdir()
    await demo_1_guardrail_blocks_dangerous_action(tmp_path)


@pytest.mark.asyncio
async def test_demo_2(tmp_path: Path):
    (tmp_path / ".codeguard").mkdir()
    (tmp_path / "skills").mkdir()
    await demo_2_feedback_loop(tmp_path)


@pytest.mark.asyncio
async def test_demo_3(tmp_path: Path):
    (tmp_path / ".codeguard").mkdir()
    (tmp_path / "skills").mkdir()
    await demo_3_scope_fence(tmp_path)

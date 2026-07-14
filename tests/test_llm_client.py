import pytest
from codeguard.agent.llm_client import LLMClient, MockLLMClient
from codeguard.models.entities import Message, MessageRole, LLMResponse


@pytest.mark.asyncio
async def test_mock_llm_returns_preset_response():
    responses = [
        LLMResponse(content="Reading file", tool_calls=[{"name": "read_file", "params": {"path": "test.py"}}]),
        LLMResponse(content="Done", tool_calls=[]),
    ]
    client = MockLLMClient(responses)
    messages = [Message(role=MessageRole.USER, content="Read test.py")]

    resp1 = await client.call(messages)
    assert resp1.content == "Reading file"
    assert resp1.tool_calls[0]["name"] == "read_file"

    resp2 = await client.call(messages)
    assert resp2.content == "Done"
    assert len(resp2.tool_calls) == 0


@pytest.mark.asyncio
async def test_mock_llm_raises_on_overflow():
    responses = [LLMResponse(content="Only one", tool_calls=[])]
    client = MockLLMClient(responses)
    messages = [Message(role=MessageRole.USER, content="Hi")]

    await client.call(messages)
    with pytest.raises(IndexError):
        await client.call(messages)


def test_llm_client_is_abstract():
    with pytest.raises(TypeError):
        LLMClient()

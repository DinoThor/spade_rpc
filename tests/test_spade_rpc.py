#!/usr/bin/env python

"""Tests for `spade_rpc` package."""
import pytest
from spade.agent import Agent
from spade.behaviour import OneShotBehaviour

from spade_rpc import RPCMixin

AGENT_JID = "demo@araylop-vrain/df"
AGENT2_JID = "test@araylop-vrain/client"
PWD = "1234"


@pytest.mark.asyncio
async def test_create_mixin():
    class TestAgent(RPCMixin, Agent):
        async def setup(self):
            pass

    class DummyBeh(OneShotBehaviour):
        async def run(self):
            self.kill(exit_code="Success")

    agent = TestAgent(AGENT_JID, PWD)
    await agent.start(auto_register=True)
    assert agent.is_alive() is True

    dummy = DummyBeh()
    agent.add_behaviour(dummy)
    await dummy.join()

    assert dummy.exit_code == "Success"

    await agent.stop()
    assert agent.is_alive() is False


@pytest.mark.asyncio
async def test_register_method():
    class TestAgent(RPCMixin, Agent):
        async def setup(self):
            def sum_service(a, b):
                return a + b

            self.rpc.register_method(sum_service, method_name="sum")

    class AskBehaviour(OneShotBehaviour):
        def __init__(self, agent_jid):
            super().__init__()
            self.agent_jid = agent_jid

        async def run(self):
            result = await self.agent.rpc.call(self.agent_jid, 'sum', [3, 5])
            self.kill(exit_code=result[0])

    class ClientAgent(RPCMixin, Agent):
        async def setup(self):
            pass

    agent = TestAgent(AGENT_JID, PWD)
    await agent.start()
    assert agent.is_alive() is True

    client = ClientAgent(AGENT2_JID, PWD)
    await client.start()
    assert client.is_alive() is True

    ask = AskBehaviour(AGENT_JID)
    client.add_behaviour(ask)
    await ask.join()

    assert ask.exit_code == 8

    await agent.stop()
    assert agent.is_alive() is False


@pytest.mark.asyncio
async def test_missing_method():
    class TestAgent(RPCMixin, Agent):
        async def setup(self):
            def sum_service(a, b):
                return a + b

            self.rpc.register_method(sum_service, method_name="sum")

    class AskBehaviour(OneShotBehaviour):
        def __init__(self, agent_jid):
            super().__init__()
            self.agent_jid = agent_jid

        async def run(self):
            result = await self.agent.rpc.call(self.agent_jid, 'sum2', [3, 5])
            if result:
                self.kill(exit_code=result[0])

    class ClientAgent(RPCMixin, Agent):
        async def setup(self):
            pass

    agent = TestAgent(AGENT_JID, PWD)
    await agent.start()
    assert agent.is_alive() is True

    client = ClientAgent(AGENT2_JID, PWD)
    await client.start()
    assert client.is_alive() is True

    ask = AskBehaviour(AGENT_JID)
    client.add_behaviour(ask)

    await ask.join()
    assert ask.exit_code == 0

    await agent.stop()
    assert agent.is_alive() is False


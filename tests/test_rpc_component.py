from unittest.mock import MagicMock, AsyncMock, patch

import pytest
from slixmpp import JID, Iq

from spade_rpc.rpc import RPCMixin


@pytest.fixture
def rpc_agent():
    mock_xmpp_client = MagicMock()
    mock_rpc_client = MagicMock()
    mock_xmpp_client.__getitem__.side_effect = lambda key: {"xep_0009": mock_rpc_client}[key]

    mock_handle_call = MagicMock()
    mock_handle_response = MagicMock()
    mock_handle_fault = MagicMock()
    mock_handle_error = MagicMock()

    class DummyAgent:
        def __init__(self, *args, **kwargs):
            self.client = mock_xmpp_client
            self.handle_call = mock_handle_call
            self.handle_response = mock_handle_response
            self.handle_fault = mock_handle_fault
            self.handle_error = mock_handle_error

    class RPCAgent(RPCMixin, DummyAgent):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.rpc = RPCMixin.RPCComponent(mock_xmpp_client)

    yield RPCAgent("as@localhost", "123"), mock_xmpp_client, mock_rpc_client


def test_component_init():
    mock_xmpp_client = MagicMock()
    mock_rpc_client = MagicMock()
    mock_xmpp_client.__getitem__.return_value = mock_rpc_client

    mock_handle_call = MagicMock()
    mock_handle_response = MagicMock()
    mock_handle_fault = MagicMock()
    mock_handle_error = MagicMock()

    class DummyAgent:
        def __init__(self):
            self.client = mock_xmpp_client
            self.handle_call = mock_handle_call
            self.handle_response = mock_handle_response
            self.handle_fault = mock_handle_fault
            self.handle_error = mock_handle_error

    class TestClass(RPCMixin, DummyAgent):
        def __init__(self):
            DummyAgent.__init__(self)
            RPCMixin.RPCComponent.__init__(self, self.client)

    test_class = TestClass()

    assert test_class.client == mock_xmpp_client
    assert test_class._rpc_client == mock_rpc_client
    assert test_class.methods == {}
    assert test_class.pending_calls == {}

    mock_xmpp_client.register_plugin.assert_called_once_with("xep_0009")
    assert mock_xmpp_client.add_event_handler.call_count == 4
    args = mock_xmpp_client.add_event_handler.call_args_list
    args = [a[0] for a in args]
    assert ("jabber_rpc_method_call", mock_handle_call) in args
    assert ("jabber_rpc_method_response", mock_handle_response) in args
    assert ("jabber_rpc_method_fault", mock_handle_fault) in args
    assert ("jabber_rpc_error", mock_handle_error) in args


async def test_call(rpc_agent):
    rpc_agent, _, mock_rpc_client = rpc_agent
    jid = JID("test@localhost")
    method_name = "fake_function"
    params = []

    mock_res = MagicMock()
    mock_rpc_query = MagicMock()
    mock_method_response = MagicMock()
    mock_params = MagicMock()
    mock_res.__class__ = Iq

    mock_res.__getitem__.side_effect = lambda key: {"rpc_query": mock_rpc_query}[key]
    mock_rpc_query.__getitem__.side_effect = lambda key: {"method_response": mock_method_response}[key]
    mock_method_response.get_fault.return_value = None
    mock_method_response.__getitem__.side_effect = lambda key: {"params": mock_params}[key]

    mock_call_stanza = AsyncMock()
    mock_call_stanza.send.return_value = mock_res
    mock_rpc_client.make_iq_method_call.return_value = mock_call_stanza

    with patch("spade_rpc.rpc.xml2py") as mock_xml2py:
        res = await rpc_agent.rpc.call(jid, method_name, params)

        assert res == mock_xml2py.return_value
        mock_xml2py.assert_called_once_with(mock_params)

async def test_call_fault(rpc_agent):
    rpc_agent, _, mock_rpc_client = rpc_agent
    jid = JID("test@localhost")
    method_name = "fake_function"
    params = []

    mock_res = MagicMock()
    mock_rpc_query = MagicMock()
    mock_method_response = MagicMock()
    mock_params = MagicMock()
    mock_res.__class__ = Iq

    mock_res.__getitem__.side_effect = lambda key: {"rpc_query": mock_rpc_query}[key]
    mock_rpc_query.__getitem__.side_effect = lambda key: {"method_response": mock_method_response}[key]

    mock_call_stanza = AsyncMock()
    mock_call_stanza.send.return_value = mock_res
    mock_rpc_client.make_iq_method_call.return_value = mock_call_stanza

    with patch("spade_rpc.rpc.logger") as mock_log:
        res = await rpc_agent.rpc.call(jid, method_name, params)

        assert res is None
        mock_log.error.assert_called_once()


async def test_handle_call(rpc_agent):
    rpc_agent, _, mock_rpc_client = rpc_agent

    mock_iq = MagicMock()
    mock_rpc_query = MagicMock()
    mock_method_call = MagicMock()

    mock_iq.__getitem__.side_effect = lambda key: {"rpc_query": mock_rpc_query}[key]
    mock_rpc_query.__getitem__.side_effect = lambda key: {"method_call": mock_method_call}[key]
    mock_method_call.__getitem__.side_effect = lambda key: {"method_name": "fake_method"}[key]

    rpc_agent.rpc.methods["fake_method"] = MagicMock()

    with patch("spade_rpc.rpc.logger") as mock_log:
        await rpc_agent.rpc.handle_call(mock_iq)

        rpc_agent.rpc.methods["fake_method"].assert_called_once_with(mock_iq)


async def test_handle_call_keyerror(rpc_agent):
    rpc_agent, _, mock_rpc_client = rpc_agent

    mock_iq = MagicMock()
    mock_rpc_query = MagicMock()
    mock_method_call = MagicMock()

    mock_iq.__getitem__.side_effect = lambda key: {"rpc_query": mock_rpc_query, "id": "123", "to": "fake@localhost"}[key]
    mock_rpc_query.__getitem__.side_effect = lambda key: {"method_call": mock_method_call}[key]
    mock_method_call.__getitem__.side_effect = lambda key: {"method_name": "bad_fake_method"}[key]

    rpc_agent.rpc.methods["fake_method"] = MagicMock()

    with patch("spade_rpc.rpc.fault2xml") as mock_fault2xml:
        await rpc_agent.rpc.handle_call(mock_iq)

        rpc_agent.rpc.methods["fake_method"].assert_not_called()
        mock_fault2xml.assert_called_once()
        mock_rpc_client.make_iq_method_response_fault.assert_called_once_with(
            pid="123",
            pto="fake@localhost",
            params=mock_fault2xml.return_value
        )
        mock_rpc_client.make_iq_method_response_fault.return_value.send.assert_called_once()


async def test_register_method(rpc_agent):
    rpc_agent, _, mock_rpc_client = rpc_agent
    handler = MagicMock()
    method_name = "fake_method"

    rpc_agent.rpc.register_method(handler, method_name)

    assert rpc_agent.rpc.methods[method_name] is not None

    mock_iq = MagicMock()
    mock_rpc_query = MagicMock()
    mock_method_call = MagicMock()
    mock_params = MagicMock()

    mock_iq.__getitem__.side_effect = lambda key: {
        "rpc_query": mock_rpc_query,
        "id": "123",
        "from": "fake@localhost"
    }[key]
    mock_rpc_query.__getitem__.side_effect = lambda key: {"method_call": mock_method_call}[key]
    mock_method_call.__getitem__.side_effect = lambda key: {"params": mock_params}[key]

    with (
        patch("spade_rpc.rpc.xml2py") as mock_xml2py,
        patch("spade_rpc.rpc.py2xml") as mock_py2xml
    ):
        rpc_agent.rpc.methods[method_name](mock_iq)

        mock_xml2py.assert_called_once_with(mock_params)
        handler.assert_called_once_with(*mock_params)

        mock_py2xml.assert_called_once_with(*[handler.return_value])

        mock_rpc_client.make_iq_method_response.assert_called_once_with(
            pid="123",
            pto="fake@localhost",
            params=mock_py2xml.return_value
        )
        mock_rpc_client.make_iq_method_response.return_value.send.assert_called_once()


async def test_unregister_method(rpc_agent):
    rpc_agent, _, _ = rpc_agent
    rpc_agent.rpc.methods.clear()
    rpc_agent.rpc.methods["fake_method"] = MagicMock()
    rpc_agent.rpc.methods["another_fake_method"] = MagicMock()

    assert len(rpc_agent.rpc.methods) == 2

    rpc_agent.rpc.unregister_method("fake_method")

    assert "fake_method" not in rpc_agent.rpc.methods
    assert "another_fake_method" in rpc_agent.rpc.methods
    assert len(rpc_agent.rpc.methods) == 1

    with patch("spade_rpc.rpc.logger") as mock_logger:
        rpc_agent.rpc.unregister_method("bad_another_fake_method")

        mock_logger.warning.assert_called_once()

        assert len(rpc_agent.rpc.methods) == 1

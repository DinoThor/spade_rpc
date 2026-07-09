# -*- coding: utf-8 -*-
from abc import ABCMeta, abstractmethod
from typing import List

from slixmpp import ClientXMPP
from slixmpp.plugins.xep_0009 import XEP_0009
from slixmpp.plugins.xep_0009.binding import py2xml, xml2py, fault2xml
from slixmpp.stanza.iq import Iq

from loguru import logger


class RPCMixin(metaclass=ABCMeta):
    async def _hook_plugin_after_connection(self, *args, **kwargs):
        try:
            await super()._hook_plugin_after_connection(*args, **kwargs)
        except AttributeError:
            logger.debug("_hook_plugin_after_connection is undefined")

        self.rpc = self.RPCComponent(self.client)

    class RPCComponent:
        def __init__(self, client):
            client.register_plugin("xep_0009")
            self._rpc_client: XEP_0009 = client["xep_0009"]

            client.add_event_handler("jabber_rpc_method_call", self.handle_call)
            client.add_event_handler(
                "jabber_rpc_method_response", self.handle_response
            )
            client.add_event_handler("jabber_rpc_method_fault", self.handle_fault)
            client.add_event_handler("jabber_rpc_error", self.handle_error)

            self.methods = {}
            self.pending_calls = {}

        async def call(
            self, jid: str, method_name: str, params: List, timeout: int = 10
        ):
            if not isinstance(params, list):
                params = [params]

            call_stanza: Iq = self._rpc_client.make_iq_method_call(
                pto=jid, pmethod=method_name, params=py2xml(*params)
            )

            res = await call_stanza.send(timeout=timeout)
            if isinstance(res, Iq):
                fault = res["rpc_query"]["method_response"].get_fault()
                if fault is None:
                    return xml2py(res["rpc_query"]["method_response"]["params"])

                logger.error(
                    f"{method_name} not found in {jid} methods registered list"
                )
            return None

        async def handle_call(self, iq: Iq):
            try:
                name = iq["rpc_query"]["method_call"]["method_name"]
                return self.methods[name](iq)
            except KeyError:
                if iq["to"] is not None:
                    fault = fault2xml({"code": 404, "string": "Method not found"})
                    res = self._rpc_client.make_iq_method_response_fault(
                        pid=iq["id"], pto=iq["to"], params=fault
                    )
                    res.send()

        async def handle_response(self, iq): #pragma: no cover
            """
            Handles the response received from the client after an RPC request is performed.
            Used to handle asynchronously the RPC response
            To override
            """
            pass

        async def handle_fault(self, iq): #pragma: no cover
            """
            Handled a fault response received from the client if it's unable to process our request.
            To override
            """
            pass

        async def handle_error(self, iq): #pragma: no cover
            """
            Default error
            To override
            """
            pass

        def register_method(self, handler, method_name: str):
            def method_wrapper(iq):
                params = xml2py(iq["rpc_query"]["method_call"]["params"])
                response = handler(*params)

                if not isinstance(response, list):
                    response = [response]

                res = self._rpc_client.make_iq_method_response(
                    pid=_id, pto=iq["from"], params=py2xml(*response)
                )

                res.send()

            self.methods[method_name] = method_wrapper

        def unregister_method(self, method_name: str):
            try:
                self.methods.pop(method_name)
            except KeyError:
                logger.warning(
                    f"Unable to unregister {method_name}. There's no method registered with that name"
                )

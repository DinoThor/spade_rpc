import getpass
from asyncio import run
from spade.agent import Agent
from spade.behaviour import OneShotBehaviour
from spade_rpc.rpc import RPCMixin

import logging


class ServerAgent(RPCMixin, Agent):
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
        print(f"3 + 5 = {result[0]}")
        assert result[0] == 8

        await self.agent.stop()


class ClientAgent(RPCMixin, Agent):
    async def setup(self):
        pass


async def main(jid, passwd):
    server_jid = f'{jid}/df'

    server_agent = ServerAgent(server_jid, passwd)
    await server_agent.start()

    test_client = ClientAgent(f'client_{jid}/test', passwd)
    test_client.server_jid = server_jid

    rpc_call = AskBehaviour(server_jid)
    test_client.add_behaviour(rpc_call)

    await test_client.start()
    await rpc_call.join()


if __name__ == "__main__":
    jid = input("JID> ")
    passwd = getpass.getpass()

    run(main(jid, passwd))

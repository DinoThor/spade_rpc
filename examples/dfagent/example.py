from dfagent import DFAgent
from spade_rpc import RPCAgent
import time
from spade.behaviour import OneShotBehaviour
import getpass


class AskBehaviour(OneShotBehaviour):
    def __init__(self, dfagent_jid):
        super().__init__()
        self.dfagent_jid = dfagent_jid

    async def run(self):
        await self.agent.rpc.call_method(self.dfagent_jid, 'register_method', 'foo')
        await self.agent.rpc.call_method(self.dfagent_jid, 'register_method', 'bar')
        methods = await self.agent.rpc.call_method(self.dfagent_jid, 'list_methods', str(self.agent.jid))
        jids = await self.agent.rpc.call_method(self.dfagent_jid, 'list_jids', 'foo')

        print(methods)
        print(jids)

        await self.agent.stop()


def main(jid, passwd):
    dfagent_jid = jid + '/df'

    dfagent = DFAgent(dfagent_jid, passwd)
    future = dfagent.start()
    future.result()

    for i in range(5):
        testclient = RPCAgent('{}/test{}'.format(jid, str(i)), passwd)

        ab = AskBehaviour(dfagent_jid)
        ab.set_agent(testclient)
        testclient.add_behaviour(ab)

        future = testclient.start()
        future.result()

    while testclient.is_alive():
        try:
            time.sleep(1)
        except KeyboardInterrupt:
            testclient.stop()
            break


if __name__ == "__main__":
    jid = input("JID> ")
    passwd = getpass.getpass()

    main(jid, passwd)

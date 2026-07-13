import asyncio
import getpass

import numpy as np
import sklearn.datasets
from spade.agent import Agent
from spade.behaviour import OneShotBehaviour
from spade_rpc import RPCMixin

import classifiers as clfs


def get_dataset(file):
    file = open(file, 'r')

    dataset = [x.split(',') for x in file][:-1]
    x = np.double([x[0:3] for x in dataset])
    y = np.asarray([x[4][:-1] for x in dataset])

    return x.tolist(), y.tolist()


def split_dataset(x, y, num_test=100):
    train_len = len(x) - num_test
    x_train = x[:train_len]
    x_test = x[train_len:]

    y_train = y[:train_len]
    y_test = y[train_len:]

    return (x_train.tolist(), y_train.tolist()), (x_test.tolist(), y_test.tolist())


def load_sklearn_dataset(dataset):
    x, y = dataset.data, dataset.target

    return x, y


def divide_dataset(x, y, num):
    n = int(len(x) / num)

    datasets = []
    for i in range(num):
        x_split = x[i * n:i * n + n]
        y_split = y[i * n:i * n + n]

        datasets.append([x_split, y_split])

    return datasets


class Client(RPCMixin, Agent):
    async def ask_to(self, JID, x):
        if type(JID) == list:
            tasks = [self.ask_to(jidx, x) for jidx in JID]
            return await asyncio.gather(*tasks)
        return await self.rpc.call_method(JID, 'predict', x)


class AskBehaviour(OneShotBehaviour):
    def __init__(self, classifiers_jids, x, y):
        super().__init__()
        self.classifiers_jids = classifiers_jids
        self.x = x
        self.y = y

    async def run(self):
        predictions = await self.agent.ask_to(self.classifiers_jids, self.x)
        predictions = np.array(predictions)
        print(predictions.shape)
        total_ok = 0
        global_ok = 0
        classifiers_ok = [0 for _ in range(len(self.classifiers_jids))]

        for i in range(predictions.shape[-1]):
            results = predictions[:, i]
            groundtruth = self.y[i]

            values, counts = np.unique(results, return_counts=True)
            ind = np.argmax(counts)

            print('Asked: {}'.format(self.x[0][i]))
            print('Predictions: {}'.format(results))
            print('Most common prediction: {}'.format(values[ind]))
            print('Groundtruth: {}'.format(groundtruth))
            print('')

            for i_classifier, result in enumerate(results):
                if result == groundtruth:
                    global_ok += 1
                    classifiers_ok[i_classifier] += 1

            if values[ind] == groundtruth:
                total_ok += 1

        print('---------------------------')
        print('global accuracy: {}'.format(global_ok / (len(self.classifiers_jids) * predictions.shape[-1])))
        print('pooling accuracy: {}'.format(total_ok / predictions.shape[-1]))
        for i, classifier in enumerate(self.classifiers_jids):
            print('{} accuracy: {}'.format(classifier, classifiers_ok[i] / predictions.shape[-1]))

        await self.agent.stop()


async def main(jid, passwd):
    print("Fetching dataset")
    dataset = sklearn.datasets.fetch_covtype(shuffle=True)
    x, y = load_sklearn_dataset(dataset)

    print("Splitting dataset")
    (x_train, y_train), (x_test, y_test) = split_dataset(x, y, num_test=50)
    x_train, y_train = x_train[:1000], y_train[:1000]
    divided_dataset = divide_dataset(x_train, y_train, len(clfs.classifiers))

    print("Creating and training classifiers")
    classifiers = [clfs.register_classifier(jid, passwd, classifier, training_data) for classifier, training_data in
                   zip(clfs.classifiers, divided_dataset)]

    client = Client("{}/client".format(jid), passwd)

    ab = AskBehaviour(list(classifiers), x_test, y_test)
    ab.set_agent(client)
    client.add_behaviour(ab)

    print("Predicting")
    await client.start()
    await ab.join()


if __name__ == "__main__":
    np.random.seed(722)

    jid = input("JID> ")
    passwd = getpass.getpass()

    asyncio.run(main(jid, passwd))

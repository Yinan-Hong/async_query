import json
import random
import requests
import sys
import time
import web3



def generate_random_block_num(size=0) -> tuple:
    """ Return a tuple of integer, each representing a block number.

        size: length of the list.
    """
    MIN_BLOCK_NUM = 10000000
    MAX_BLOCK_NUM = 15537420

    param_lst = list()

    for _ in range(size):
        random_block_num = random.randint(MIN_BLOCK_NUM, MAX_BLOCK_NUM)
        param = [hex(random_block_num), True]
        param_lst.append(param)

    return tuple(param_lst)

def big_small_block_num_test() -> None:
    print('Geting block 100')
    start = time.perf_counter()
    block = web3.eth.get_block(100)
    print('Size of block:', sys.getsizeof(str(block).encode()), 'Bytes')
    print('Time cost in second:', time.perf_counter() - start)
    print('\n -------------------')

    print('Geting block 1000000')
    start = time.perf_counter()
    block = web3.eth.get_block(1000000)
    print('Size of block:', sys.getsizeof(str(block).encode()), 'Bytes')
    print('Time cost in second:', time.perf_counter() - start)


def query_request() -> None:
    url = 'http://chenlin02.fbe.hku.hk:8547'

    param = [
        hex(10000000),
        False
    ]

    data = {
        'jsonrpc': '2.0',
        'method': 'eth_getBlockByNumber',
        'params': param,
        'id': 1
    }

    data = json.dumps(data)

    headers = {'Content-Type': 'application/json'}
    resp = requests.post(url, data, headers=headers)
    print(resp.json())


# query_request()


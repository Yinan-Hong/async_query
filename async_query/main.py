import configparser
import examples.example_util as example_util
import utils.util as util

import os
os.chdir('/home/yinan/bishe_backup/async_query')
print(os.getcwd())

# Load config
def load_config() -> None:
    CONFIG_PATH = './config.ini'
    config = dict()

    parser = configparser.ConfigParser()
    parser.read(CONFIG_PATH)

    for _ in parser.sections():
        items = parser.items(_)
        for item in items:
            config[item[0]] = item[1]

    return config

# read query param
    # generate random number
def load_query_param() -> util.Param_pool:
    """ Load query parameters to memory.

        Returns a Param_pool that contains all query parameter.

        In this example project, the program queries eth built in function 'get_block',
        so the parameter of each query would be a block number (integer).
    """

    PARAM_CNT = 5000
    PARAM_POOL_SIZE = 5000 + 1

    # Generate param_pool and push parametes to the pool
    # Pool size is infanite when maxsize=0
    param_pool = util.Param_pool(maxsize = PARAM_POOL_SIZE)

    # Generate and process data of parameters
    params = example_util.generate_random_block_num(PARAM_CNT)

    # Push all parameters into Param_pool
    param_pool.push_all_params_no_wait(params=params)

    return param_pool


def get_url(url, port) -> str:
    return url + ':' + str(port)

def get_data(method) -> dict:
    data = {
        'jsonrpc': '2.0',
        'method': str(method),
        'id': 1
    }
    return data

def async_query() -> None:
    """ Entrance of a async query work.
    """

    config = load_config()

    print('Loading parameters.')

    # Records time spend of parameter loading process
    loading_timer = util.Timer()

    param_pool = load_query_param()
    loading_timer.timing_stop()

    print('Parameters loaded.')
    # Output time spend to command line
    print('Time cost: %.5f (s)\n'% loading_timer.get_time_spent())



    # query timer
    print('Query starts.')
    query_timer = util.Timer()

    # create async http dealer
    async_http_dealer = util.Async_http_dealer(
        get_url(config['host'], config['port']),
        config['err_msg_log'],
        config['err_param_log'],
        get_data(config['method'])
    )

    query_cnt = param_pool.qsize()

    # call send async http
    async_http_dealer.start_query(param_pool, 100)
    # timer stop
    query_timer.timing_stop()
    print('Query done')
    print('Time cost: %.5f (s)'% query_timer.get_time_spent())
    print('Average query speed: %.5f (queries/s)'% query_timer.get_avg_time_spent(query_cnt))


    # get response pool
    # response_lst = async_http_dealer.__get_response_lst()

    # deal with response
    # pass


def main():
    async_query()

if __name__ == '__main__':
    main()
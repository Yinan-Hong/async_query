from aiofile import AIOFile
import aiohttp
import asyncio
import json
import time
import progressbar


class Param_pool(asyncio.Queue):
    def __init__(self, maxsize: int) -> None:
        super().__init__(maxsize)

    def push_all_params_no_wait(self, params: tuple) -> None:
        for _ in params:
            self.put_nowait(params)


class Response():
    def __init__(self, status, content) -> None:
        self.status = status
        self.content = content


class Response_pool(asyncio.Queue):
    def __init__(self, maxsize: int) -> None:
        super().__init__(maxsize)

    def get_response_no_wait(self) -> Response:
        return self.get_nowait()


class Timer():
    """ A timer to record the time spend of a process.

    Timer starts when initializing, ends when __timing_stop is called.
    """
    __start = 0
    __end = 0

    def __init__(self) -> None:
        self.__start = time.perf_counter()

    def timing_stop(self) -> None:
        """ Call to stop timing.
        """
        self.__end = time.perf_counter()

    def get_time_spent(self) -> float:
        """ Returns total time spent from initializing Time object to __timing_stop was called.
        """
        return float(self.__end - self.__start)

    def get_avg_time_spent(self, query_cnt: int) -> float:
        """ Returns average time spent of each query.

        query_cnt: number of queries.
        """
        return float(query_cnt / float(self.__end-self.__start))


class Async_http_dealer():
    response_lst = None
    headers = {'Content-Type': 'application/json'}

    def __init__(self, url: str, err_msg_log, err_param_log, data) -> None:
        self.url = url
        self.err_msg_log = err_msg_log
        self.err_param_log = err_param_log
        self.data = data

    def __init_progress_bar(self, size) -> progressbar.ProgressBar:
        bar = progressbar.ProgressBar(
            maxval=size,
            widgets=[
                progressbar.Bar('#', '[', ']'), ' ',
                progressbar.Percentage(), ' | Count:',
                progressbar.Counter(), '/' + str(size) + ' | ',
                progressbar.Timer(), ' | ',
                progressbar.ETA()
            ]
        )
        bar.start()
        return bar

    async def __update_progress_bar(self, queue: Param_pool, bar: progressbar.ProgressBar, total) -> None:
        while not queue.empty():
            bar.update(total-queue.qsize()-1)
            await asyncio.sleep(0.5)

        bar.finish()
        queue.task_done()

    def __create_reponse_pool(self, maxsize) -> Response_pool:
        return Response_pool(maxsize=maxsize)

    async def __async_send_http(self, param_pool: Param_pool, task_cnt: int) -> None:
        pool_size = param_pool.qsize()
        resp_pool = self.__create_reponse_pool(maxsize=pool_size+1)
        bar = self.__init_progress_bar(size=pool_size)

        tasks = list()
        for _ in range(task_cnt):
            task = asyncio.create_task(
                self.__send_request(param_pool, resp_pool))
            tasks.append(task)

        tasks.append(asyncio.create_task(
            self.__update_progress_bar(param_pool, bar, pool_size)))

        await asyncio.gather(*tasks)

        self.__put_response_to_list(resp_pool)


    async def __send_request(self, param_pool: Param_pool,
                           resp_pool: Response_pool) -> None:

        while not param_pool.empty():
            param = await param_pool.get()
            data = self.data
            data['params'] = param
            data = json.dumps(data)

            try:
                async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=False)) as session:
                    async with session.post(url=self.url, data=data, headers=self.headers) as resp:
                        if resp.status == 200:
                            content = await resp.json()
                            await self.__put_response(content, resp_pool)
                        else:
                            raise Exception
            except Exception as e:
                await asyncio.sleep(0.5)
                await self.__log_error(param, str(e))


    async def __log_error(self, param, err_msg) -> None:
        async with AIOFile(self.err_param_log, 'a+') as file:
            param = str(param) + '\n'
            await file.write(param)
            await file.fsync()

        async with AIOFile(self.err_msg_log, 'a+') as file:
            err_msg = str(err_msg) + '\n'
            await file.write(err_msg)
            await file.fsync()


    async def __resend_request(self) -> None:
        pass


    async def __put_response(status, content, resp_pool: Response_pool) -> None:
        resp = Response(status, content)
        await resp_pool.put(resp)

    def __put_response_to_list(self, response_pool: Response_pool) -> None:
        response_lst = list()
        while not response_pool.empty():
            response_lst.append(response_pool.get_nowait())

        self.response_lst = tuple(response_lst)

    def get_response_lst(self) -> tuple:
        return self.response_lst


    def start_query(self, param_pool, task_cnt) -> None:
        asyncio.run(self.__async_send_http(param_pool, task_cnt))


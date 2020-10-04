from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, Future, wait
from multiprocessing import current_process, JoinableQueue
from typing import List, Dict, Optional
from hyper.contrib import HTTP20Adapter
from traceback import print_exc
from queue import Queue
from math import ceil
from time import time
from copy import copy

from .common.constants import IP, PORT, HEADER_SIZE
from .weblib.fetch import fetch_data
from .common.base import Client

import platform
import requests
import pickle
import sys
import os


def download_process(links, total_links, session, http2, max_retries,
                     convert, file_link_maps, path_prefix, debug, progress_bar_queue) -> None:
    print(f"Starting Download process {current_process().name}")
    start_time = time()
    try:
        download_manager = DownloadProcess(links, total_links, session, http2,
                                           max_retries, convert, debug)

        start_processes(download_manager, file_link_maps, path_prefix, progress_bar_queue)
        try:
            client = Client(IP, PORT)
            client.send_data(f"{'STOP_QUEUE':<{HEADER_SIZE}}{download_manager.get_total_downloaded_links_count()}")
        except (ConnectionRefusedError, ConnectionResetError):
            print_exc()

    except (KeyboardInterrupt, Exception):
        print_exc()

    minutes, seconds = divmod(time() - start_time, 60)
    print(f"\nDownload took {minutes} minutes and {seconds} seconds")
    print(f"Stopped Download process {current_process().name}")


class DownloadProcess:
    def __init__(self, links: List[str], total_links: int, session: requests.Session,
                 http2: bool = False, max_retries: int = 5,
                 convert: bool = True, debug: bool = False):
        """Initialize Object of DownloadProcess.

        Parameters
        ----------
        links: List[str]
            The links to be downloaded
        total_links: int
            The number of links to be downloaded
        session: requests.Session
            The session using which all the links will be downloaded
        http2: bool
            A flag to keep track of the type of http headers
        max_retries: int
            The maximum number of retries for a particular link
        convert: bool
            A flag to keep track of the whether the downloaded video should be converted
        debug: bool
            A flag to print messages to the console
        """
        self.__session: requests.Session = session
        self.__total_links: int = total_links
        self.__links: List[str] = links
        self.max_retries: int = max_retries
        self.http2: bool = http2
        self.convert = convert
        self.__sent = 0
        self.__process_num = len(os.sched_getaffinity(os.getpid())) if platform.system() == "Linux" else 4
        self.__thread_num = int(ceil((total_links - self.__sent) / (self.__process_num * 4)))
        self.debug = debug
        self.done_retries = 0
        self.error_links = []

    def get_thread_num(self) -> int:
        return self.__thread_num

    def get_process_num(self) -> int:
        return self.__process_num

    def set_thread_num(self, val: int) -> None:
        self.__thread_num = val

    def get_download_links(self) -> List[str]:
        return self.__links

    def get_total_links(self) -> int:
        return self.__total_links

    def get_session(self) -> requests.Session:
        return self.__session

    def get_total_downloaded_links_count(self) -> int:
        return self.__sent

    def set_total_downloaded_links_count(self, val: int) -> None:
        self.__sent = val


def start_processes(download_manager: DownloadProcess, file_link_maps: Dict[str, str], path_prefix: str
                    , progress_bar_queue) -> None:
    process_num: int = download_manager.get_process_num()
    if download_manager.debug:
        print(f"starting {process_num} processes for {len(download_manager.get_download_links())} links")

    with ProcessPoolExecutor(max_workers=process_num) as process_pool_executor:
        try:
            process_pool_executor_handler(process_pool_executor, download_manager, file_link_maps, path_prefix
                                          , progress_bar_queue)
        except (KeyboardInterrupt, Exception):
            sys.exit()


def process_pool_executor_handler(executor: ProcessPoolExecutor, manager: DownloadProcess,
                                  file_maps: Dict[str, str], directory: str, progress_bar_queue) -> None:
    done_queue = JoinableQueue()

    def update_hook(future: Future):
        temp = future.result()
        if temp:
            for failed_links in temp:
                done_queue.put(failed_links)

    while manager.done_retries != manager.max_retries:
        print(f"Starting download {manager.get_total_links() - manager.get_total_downloaded_links_count()} links left")
        available_cpus = list(os.sched_getaffinity(os.getpid())) if platform.system() == "Linux" else [0, 1, 2, 3]
        print(f"available cpu's {available_cpus}, initializing {4 * manager.get_process_num()}"
              f" threads with {manager.get_thread_num()} links per "
              f"process")

        if len(manager.error_links):
            download_links = manager.error_links.copy()
            manager.error_links = []
        else:
            download_links = manager.get_download_links().copy()

        process_futures: List[Future] = []

        start = 0
        for temp_num in range(len(download_links)):
            end = start + manager.get_thread_num()

            if end > len(download_links):
                end = len(download_links)

            cpu_num = available_cpus[temp_num % len(available_cpus)]
            process_futures.append(executor.submit(start_threads, download_links[start:end],
                                                   file_maps, manager.get_session(), directory,
                                                   manager.http2, progress_bar_queue, manager.debug, cpu_num))
            process_futures[-1].add_done_callback(update_hook)
            start = end

            if end >= len(download_links):
                break

        wait(process_futures)

        while not done_queue.empty():
            link = done_queue.get()
            manager.error_links.append(link)

        manager.set_total_downloaded_links_count(manager.get_total_links() - len(manager.error_links))

        if manager.debug:
            print(f"Total downloaded links {manager.get_total_downloaded_links_count()}")
            print(f"Error links generated {len(manager.error_links)}")

        if len(manager.error_links):
            manager.set_thread_num(int(ceil((manager.get_total_links()
                                             - manager.get_total_downloaded_links_count())
                                            / manager.get_process_num())))
            print(f"\n{manager.get_total_links()} was expected but "
                  f"{manager.get_total_downloaded_links_count()} was downloaded.")
            manager.done_retries += 1
            print(f"Trying retry {manager.done_retries}")
        else:
            break


def start_threads(links: List[str], maps: Dict[str, str], session: requests.Session,
                  file_path_prefix: str, http2: bool, progress_bar_queue, debug: bool = False,
                  cpu_num: int = 0) -> List[Optional[str]]:
    failed_links = Queue()
    sessions_queue = Queue()

    def update_hook(future: Future):
        temp = future.result()
        if temp:
            failed_links.put(temp)

    sent_links = {}
    if platform.system() == "Linux":
        os.sched_setaffinity(os.getpid(), {cpu_num})

    THREAD_WORKERS: int = 4

    if http2:
        for _ in range(THREAD_WORKERS):
            sess = requests.Session()
            sess.mount("https://", HTTP20Adapter(max_retries=10))
            sess.headers = copy(session.headers)
            sessions_queue.put(sess)

    with ThreadPoolExecutor(max_workers=THREAD_WORKERS) as executor:
        for link in links:
            temp_path = os.path.join(file_path_prefix, maps[link])
            sent_links[link] = temp_path

            if http2:
                new_session = None
            else:
                new_session = session

            thread_future = executor.submit(download_thread, temp_path, link, new_session,
                                            http2, sessions_queue)
            thread_future.add_done_callback(update_hook)

    failed = []

    for link in failed_links.queue:
        del sent_links[link]
        failed.append(link)

    send_data = pickle.dumps(list(sent_links.values()))
    msg = f"{'POST_FILENAME_QUEUE':<{HEADER_SIZE}}"
    client = Client(IP, PORT)
    client.send_data(msg)
    client.send_data(send_data, "bytes")

    if debug:
        print(f"Sending data to server of size {len(send_data)} bytes")

    progress_bar_queue.put(len(sent_links))
    return failed


def download_thread(file_path: str, link: str, session: requests.Session,
                    http2: bool, s_queue: Queue) -> Optional[str]:
    if os.path.exists(file_path):
        return None

    if not session and http2:
        session = s_queue.get()

    done_url = fetch_data(link, session, 120, file_path, http2)

    if http2 and session:
        s_queue.put(session)

    return done_url

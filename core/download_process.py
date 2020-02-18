from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, Future, wait
from multiprocessing import Manager, current_process
from .common.constants import IP, PORT, HEADER_SIZE
from typing import List, Dict, Optional
from .weblib.fetch import fetch_data
from .common.base import Client
from traceback import print_exc
from time import time, sleep
from threading import Lock
from random import shuffle
import requests
import pickle
import sys
import os

thread_executors = {}


def download_process(links, total_links, session, headers, http2, max_retries,
                     convert, file_link_maps, path_prefix, debug) -> None:
    print(f"Starting Download process {current_process().name}")
    start_time = time()
    try:
        download_manager = DownloadProcess(links, total_links, session, headers, http2,
                                           max_retries, convert, debug)
        for i in range(4, 12):
            thread_executors[f"Process-{i}"] = ThreadPoolExecutor(max_workers=4)

        start_processes(download_manager, file_link_maps, path_prefix)
        try:
            client = Client(IP, PORT)
            client.send_data(f"{'STOP_QUEUE':<{HEADER_SIZE}}{download_manager.get_total_downloaded_links_count()}")
        except:
            pass

        for executor in thread_executors.values():
            executor.shutdown(wait=True)

    except (KeyboardInterrupt, Exception):
        print_exc()

    print(f"Download took {time() - start_time} seconds")
    print(f"Stopped Download process {current_process().name}")


class DownloadProcess:
    def __init__(self, links: List[str], total_links: int, session: requests.Session,
                 headers: Dict[str, str], http2: bool = False, max_retries: int = 5,
                 convert: bool = True, debug: bool = False):
        self.__session: requests.Session = session
        self.__headers: Dict[str, str] = headers
        self.__total_links: int = total_links
        self.__links: List[str] = links
        self.max_retries: int = max_retries
        self.http2: bool = http2
        self.convert = convert
        self.__process_num = 8
        self.__thread_num = 4
        self.__sent = 0
        self.debug = debug
        self.done_retries = 0
        self.error_links = []

    def get_thread_num(self, num: int = 4) -> int:
        if num < self.__thread_num:
            return num
        return self.__thread_num

    def get_process_num(self) -> int:
        return self.__process_num

    def get_download_links(self) -> List[str]:
        return self.__links

    def get_total_links(self) -> int:
        return self.__total_links

    def get_session(self) -> requests.Session:
        return self.__session

    def get_headers(self) -> Dict[str, str]:
        return self.__headers

    def get_total_downloaded_links_count(self) -> int:
        return self.__sent

    def set_total_downloaded_links_count(self, val: int) -> None:
        self.__sent = val


def start_processes(download_manager: DownloadProcess, file_link_maps: Dict[str, str], path_prefix: str) -> None:
    process_num: int = download_manager.get_process_num()
    with ProcessPoolExecutor(max_workers=process_num) as process_pool_executor:
        try:
            process_pool_executor_handler(process_pool_executor, download_manager, file_link_maps, path_prefix)
        except (KeyboardInterrupt, Exception):
            sys.exit()


def process_pool_executor_handler(executor: ProcessPoolExecutor, manager: DownloadProcess,
                                  file_maps: Dict[str, str], directory: str) -> None:
    lock = Manager().Lock()

    def update_hook(future: Future):
        temp = future.result()
        if temp:
            with lock:
                manager.error_links.extend(temp)

    while manager.done_retries != manager.max_retries:
        print(f"Starting download {manager.get_total_links() - manager.get_total_downloaded_links_count()} left")

        if len(manager.error_links):
            shuffle(manager.error_links)
            download_links = manager.error_links.copy()
            manager.error_links = []
        else:
            download_links = manager.get_download_links().copy()
            shuffle(download_links)

        process_futures: List[Future] = []

        start = 0
        for _ in range(len(download_links)):
            end = start + manager.get_thread_num()
            if end > len(download_links):
                end = len(download_links)
            process_futures.append(executor.submit(start_threads, download_links[start:end], file_maps,
                                                   manager.get_session(), manager.get_headers(),
                                                   directory, manager.http2, manager.debug))
            process_futures[-1].add_done_callback(update_hook)
            start = end
            if end >= len(download_links):
                break

        wait(process_futures)

        manager.set_total_downloaded_links_count(manager.get_total_links() - len(manager.error_links))

        if manager.debug:
            print(f"Total downloaded links {manager.get_total_downloaded_links_count()}")
            print(f"Error links generated {len(manager.error_links)}")

        if len(manager.error_links):
            print(f"{manager.get_total_links()} was expected but "
                  f"{manager.get_total_downloaded_links_count()} was downloaded.")
            manager.done_retries += 1
            print(f"Trying retry {manager.done_retries}")
        else:
            break


def start_threads(links: List[str], maps: Dict[str, str], session: requests.Session,
                  headers: Dict[str, str], file_path_prefix: str, http2: bool,
                  debug: bool = False) -> List[Optional[str]]:
    lock = Lock()

    def update_hook(future: Future):
        temp = future.result()
        if temp:
            with lock:
                failed_links.append(temp)

    failed_links = []

    sent_links = {}

    process_name = current_process().name

    executor = thread_executors[process_name]
    thread_futures = []

    for link in links:
        temp_path = os.path.join(file_path_prefix, maps[link])
        sent_links[link] = temp_path
        thread_futures.append(executor.submit(download_thread, temp_path, link, session, headers, http2))
        thread_futures[-1].add_done_callback(update_hook)

    wait(thread_futures)

    for link in failed_links:
        del sent_links[link]

    send_data = pickle.dumps(list(sent_links.values()))
    msg = f"{'POST_FILENAME_QUEUE':<{HEADER_SIZE}}"
    client = Client(IP, PORT)
    client.send_data(msg)
    client.send_data(send_data, "bytes")

    if debug:
        print(f"Sending data to server {send_data}")

    return failed_links


def download_thread(file_path: str, link: str, session: requests.Session,
                    headers: Dict[str, str], http2: bool) -> Optional[str]:
    if os.path.exists(file_path):
        return None

    return fetch_data(link, headers, session, 120, file_path, http2)

from multiprocessing import cpu_count, current_process, Manager, Pipe, Process
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, Future
from typing import Optional, List, Dict, ByteString
from urllib.parse import urlparse, urljoin
from requests.adapters import HTTPAdapter
from threading import Lock as threadLock
from hyper.contrib import HTTP20Adapter
from time import sleep, time
from traceback import print_exc
from shutil import rmtree
from pprint import pprint
from random import shuffle
import subprocess
import argparse
import requests
import logging
import sys
import os

header: Dict[str, str] = {}
links_file_map: Dict[str, str] = {}
logging.basicConfig(filename='app.log', filemode='w',
                    format='%(name)s - %(levelname)s - %(message)s', level=logging.ERROR)
mpLock: threadLock = Manager().Lock()
tLock: threadLock = threadLock()
total_content: int = 0
BASE_URL: str = ""
THREAD_NUM: int = (cpu_count() or 4)

# All unparsed requests content will be stored in this temporary hidden folder
TEMP_FOLDER = ".asdalkshdalskdhalsdhaslk12313123asdllcvsd"

# HTTP/1.1 adapter
ADAPTER1: HTTPAdapter = HTTPAdapter(max_retries=5)

# HTTP/2 adapter
ADAPTER2: HTTP20Adapter = HTTP20Adapter(max_retries=10)

TOTAL_LINKS: int = 0
MAX_RETRIES: int = 5
TOTAL_RETRIES: int = 5

# If HTTP/2 is set to True all requests will be made through HTTP/2 otherwise HTTP/1.1
HTTP2: bool = False

# Request timeout
timeout: int = 100

# error links
error_download_links: List[str] = []


class GraphNode:
    def __init__(self, data):
        self.data = data
        self.adjacent_nodes = {}

    def add_edge(self, data):
        self.adjacent_nodes[data] = 1

    def remove_edge(self, data):
        if data in self.adjacent_nodes:
            del self.adjacent_nodes[data]

    def __len__(self):
        return len(self.adjacent_nodes)

    def __iter__(self):
        for node in self.adjacent_nodes:
            yield node

    def __add__(self, other):
        res = [self.data]
        for key in other:
            res.append(key)
        return res

    def __repr__(self):
        return f"{self.data}--->{self.adjacent_nodes}\n"

    def __str__(self):
        return f"{self.data}--->{self.adjacent_nodes}\n"


class Graph:
    def __init__(self, number_of_nodes: int, nodes: List[str]):
        self.size: int = number_of_nodes
        self.data_list: List[str] = nodes
        self.nodes: Dict[str, GraphNode] = {k: GraphNode(k) for k in nodes}
        self.file_meta_data: Dict[str, float] = {}
        self.construct()

    def construct(self):
        visited: Dict[str, ByteString] = {}

        def generate_file_metadata(current_file) -> ByteString:
            with open(os.path.join(TEMP_FOLDER, current_file), "rb") as data_file:
                file_data = data_file.read().strip()
            visited[current_file] = file_data
            cmd = "ffprobe {} -show_entries format=start_time -v quiet -of csv='p=0'" \
                .format(os.path.join(TEMP_FOLDER, current_file))
            ts_time_stamp = subprocess.check_output(cmd, shell=True)
            self.file_meta_data[current_file] = float(ts_time_stamp.decode("utf-8").strip())
            return file_data

        for index, data in enumerate(self.data_list):
            if data in visited:
                current_data = visited[data]
            else:
                current_data = generate_file_metadata(data)
            for node in self.data_list[index:]:
                if node in visited:
                    node_data = visited[node]
                else:
                    node_data = generate_file_metadata(node)
                if current_data == node_data and node != data \
                        and self.file_meta_data[data] == self.file_meta_data[node]:
                    self.nodes[node].add_edge(data)
                    self.nodes[data].add_edge(node)
        del visited

    def __getitem__(self, key):
        return self.nodes[key]

    def __len__(self):
        return len(self.nodes)

    def __iter__(self):
        for node, val in self.nodes.items():
            yield node, val

    def __repr__(self):
        return str(self.nodes.values())


def directory_validator(string: str) -> str:
    # This code is used to check if passed in headers_path string is valid path to a file
    # if not FileNotFoundError is raised
    if os.path.isfile(string):
        return string
    raise FileNotFoundError(f"{string} does not point to a file")


def construct_headers(header_path: str) -> Dict[str, str]:
    global header, HTTP2
    header: Dict[str, str] = {}
    print("Parsed Request headers\n")
    if os.path.exists(header_path):
        with open(header_path) as file:
            lines = file.readlines()
            lines = [line.strip() for line in lines]
        for line in lines:
            if line[0] == ":":
                # This code checks if the given headers are of HTTP/2, if yes then HTTP2 is set to True
                # and all subsequent requests will be made with HTTP/2
                temp = line.split(":")
                if temp[1] and temp[2:]:
                    header[":" + temp[1]] = ":".join(temp[2:]).strip()
                    HTTP2 = True
            else:
                temp = line.split(":")
                if temp[0] and temp[1:]:
                    header[temp[0]] = ":".join(temp[1:]).strip()
        if "cookie" in header:
            del header["cookie"]
        pprint(header)
        print("press ctrl+c or ctrl+z if parsed headers are incorrect")
        try:
            sleep(10)
        except KeyboardInterrupt:
            logging.error(
                "headers incorrectly parsed check construct_headers() function for debugging")
            sys.exit()
    else:
        print(f"Include headers in {header_path} directory and restart program")
        sys.exit()
    return header


def convert_video(video_input: str, video_output: str) -> None:
    # These arguments will be passed in with ffmpeg for video conversion
    flags = ["ffmpeg", "-i", f"{video_input}.ts", "-acodec", "copy", "-vcodec", "copy", video_output]
    subprocess.Popen(flags).wait()
    os.unlink(f"{video_input}.ts")


# noinspection PyBroadException
def fetch_data(download_url: str, file_name: str, headers: dict, session: requests.Session) -> Optional[str]:
    try:
        global timeout
        if HTTP2:
            timeout += 500
            if ":path" in headers:
                parsed_url_path = urlparse(download_url).path
                headers[":path"] = parsed_url_path

            # if temp_adapter object gets called with the base class __init__ we call the temp_adapter
            # __init__ method.
            temp_adapter = session.get_adapter(download_url)
            if "connections" not in vars(temp_adapter):
                temp_adapter.__init__()

        request_data = session.get(download_url, headers=headers, timeout=timeout)
    except Exception:
        return download_url

    temp_path = os.path.join(TEMP_FOLDER, file_name)
    with open(temp_path, "wb") as video_file:
        video_file.write(request_data.content.strip())
    return None


def download_thread(file_name_maps: dict, link: str, session: requests.Session) -> Optional[str]:
    file_name = file_name_maps[link.split("/")[-1]]
    if os.path.exists(os.path.join(TEMP_FOLDER, file_name)):
        return None
    return fetch_data(link, file_name, header, session)


def initialize_threads(links: List[str], session: requests.Session, link_maps: dict) -> List[str]:
    def calculate_number_of_threads(num: int) -> int:
        if num < THREAD_NUM:
            return num
        return THREAD_NUM

    thread_number: int = calculate_number_of_threads(total_content)
    print(f"Starting process {current_process().name}")
    try:
        failed_links: List[str] = []

        def update_failed_links(future: Future) -> None:
            temp = future.result()
            if temp:
                with tLock:
                    failed_links.append(temp)

        thread_futures: List[Future[Optional[str]]] = []
        with ThreadPoolExecutor(max_workers=thread_number) as executor:
            for link in links:
                thread_futures.append(executor.submit(download_thread, link_maps.copy(), link, session))
                thread_futures[-1].add_done_callback(update_failed_links)

        return failed_links
    except KeyboardInterrupt:
        sys.exit()


def initialize_parallel_threads(links: List[str], session: requests.Session) -> None:
    global error_download_links
    error_download_links: List[str] = []

    if os.path.exists("error_links.txt"):
        os.unlink("error_links.txt")

    os.makedirs(TEMP_FOLDER, exist_ok=True)

    # No: of processes started depend on the number of cores available.
    process_number: int = (cpu_count() or 4) * 2
    print(f"initializing {process_number} processes for {total_content} links")

    def update_failed_links(future: Future) -> None:
        temp = future.result()
        if temp:
            with mpLock:
                error_download_links.extend(temp)

    process_futures: List[Future[List[str]]] = []
    with ProcessPoolExecutor(max_workers=process_number) as pool_executor:
        start = 0
        for _ in range(total_content):
            end = start + THREAD_NUM
            if end > total_content:
                end = total_content
            process_futures.append(pool_executor.submit(initialize_threads,
                                                        links[start:end].copy(),
                                                        session, links_file_map.copy()))
            process_futures[-1].add_done_callback(update_failed_links)
            start = end
            if end == total_content:
                break

    if error_download_links:
        with open("error_links.txt", "w") as file:
            for link in error_download_links:
                file.write(f"{link}\n")


def concat_all_ts(files: List[str], video_file: str) -> None:
    graph: Graph = Graph(len(files), files)
    non_duplicates: List[str] = []
    visited: Dict[str, int] = {}

    def remove(val) -> bool:
        if type(val) == int:
            val = str(val)
        if val in visited:
            return False
        visited[val] = 1
        return True

    for node, adjacent_nodes in graph:
        try:
            non_duplicates.append(min(list(filter(remove, graph.nodes[node] + adjacent_nodes))))
        except ValueError:
            pass

    with open("ts_list.txt", "w") as file:
        for file_name in sorted(non_duplicates, key=lambda f: graph.file_meta_data[f]):
            file.write(f"file '{TEMP_FOLDER}/{file_name}'\n")

    subprocess.Popen(["ffmpeg", "-f", "concat", "-safe", "0", "-i",
                      "ts_list.txt", "-c", "copy", f"{video_file}.ts"]).wait()
    os.unlink("ts_list.txt")


def write_file(video_file: str, session: requests.Session) -> None:
    files: List[str] = []
    for file in os.listdir(TEMP_FOLDER):
        if file.isnumeric():
            files.append(file)

    # The below code is responsible for carrying out 5 retries by default or the retries specified by --retry
    # in case of missing chunks. retries will be carried out by re-downloading links that failed, for every retry
    # the request timeout will increase by 5 seconds.
    global MAX_RETRIES, timeout
    if len(files) != TOTAL_LINKS and MAX_RETRIES and os.path.exists("error_links.txt"):
        MAX_RETRIES -= 1
        timeout += 5
        logging.error(f"{len(files)} chunks was downloaded but {TOTAL_LINKS} chunks was expected,"
                      f"\n downloaded chunk ids {files} retrying with error links")

        with open("error_links.txt") as file:
            temp = [line.strip() for line in file.readlines()]

        shuffle(temp)
        error_links: List[str] = temp.copy()
        global total_content
        total_content = len(error_links)
        print(f"Some download chunks are missing attempting retry {TOTAL_RETRIES - MAX_RETRIES}")
        initialize_parallel_threads(error_links, session)
        return write_file(video_file, session)

    print("Download complete, writing video file")

    concat_all_ts(files, video_file)
    os.unlink("links.txt")
    rmtree(TEMP_FOLDER)


def main(args: argparse.Namespace) -> None:
    global TOTAL_RETRIES, MAX_RETRIES, BASE_URL, TOTAL_LINKS, total_content
    print("Logs for the download will be stored in app.log")

    url = args.url

    if args.header_path:
        path = args.header_path
    else:
        path = "headers.txt"

    if args.retry:
        TOTAL_RETRIES = args.retry
        MAX_RETRIES = args.retry

    # This function is responsible for parsing the headers file provided in path.
    construct_headers(path)

    start_time = time()

    # Mount new connection adapters to the session created.
    sess: requests.Session = requests.Session()
    parsed_prefix = "/".join(url.split("/")[:-1])
    sess.mount(parsed_prefix, ADAPTER1)
    if HTTP2:
        # Mount a parsed prefix to the session, with HTTP/2 adapter
        sess.mount(parsed_prefix, ADAPTER2)

    # Fetching m3u8 playlist from url.
    req: requests.Response = sess.get(url, headers=header, timeout=60)

    # links.txt will contain all the links to be downloaded.
    with open("links.txt", "wb") as file:
        file.write(req.content)

    with open("links.txt") as file:
        temp = file.readlines()
        temp = [link.strip() for link in temp]

    parsed_url = urlparse(url)
    base_url: str = f"{parsed_url.scheme}://{parsed_url.netloc}{'/'.join(parsed_url.path.split('/')[:-1])}/"
    BASE_URL: str = base_url

    # Construct a links list containing the links joined with the base_url.
    # If the link in the m3u8 playlist is already a full link we add that to the result `links list`
    # else we join the base_url with the link partial in the playlist and add that to the `links list`
    links: List[str] = [(link if "https" in link else urljoin(base_url, link))
                        for link in temp if "EXT" not in link]

    # Construct links to file name mappings
    for file_name, link in enumerate(links):
        links_file_map[link.split("/")[-1]] = str(file_name)

    total_content += len(links)
    TOTAL_LINKS = len(links)

    # shuffle the links array
    shuffle(links)

    try:
        if args.name:
            name = args.name
        else:
            name = "video"

        # If the video has already been downloaded the below, re-download will be skipped unless --force or -f
        # is used.
        if not os.path.exists(name) or args.force:
            initialize_parallel_threads(links, sess)
            write_file(name, sess)

        elapsed_time = time() - start_time
        print(f"Download took {elapsed_time} seconds")

        # Begin video conversion if -c or --convert argument is passed in.
        if args.convert:
            print("Beginning conversion to mp4")
            convert_video(name, f"{name}.mp4")
            print("Completed conversion to mp4")

    except Exception as err:
        logging.error(err)
        print_exc()

    sys.exit()


def convert_videos_process_fn():
    pass


if __name__ == "__main__":
    # start the program with -h or --help to get more info on how to use the script.
    parser = argparse.ArgumentParser()
    parser.add_argument("url", help="Pass in a url containing m3u8 playlist", type=str)
    parser.add_argument("-n", "--name", type=str, help="Specify a name to save the downloaded video as, if no name is "
                                                       "specified default name of 'video' will be chosen")
    parser.add_argument("-p", "--header-path", type=directory_validator,
                        help="Specify the path to the file containing headers, if no path is specified the program "
                             "will look for a headers.txt file in the same directory")
    parser.add_argument("-r", "--retry", type=int, help="Specify number of retries by default 5 retries will be "
                                                        "initiated")
    parser.add_argument("-f", "--force", action="store_true", help="If this flag is used and the video has been "
                                                                   "downloaded the download will restart")
    parser.add_argument("-c", "--convert", help="Convert the downloaded video to mp4 using ffmpeg", action="store_true")
    cli_args = parser.parse_args()

    main_process = Process(target=main, args=(cli_args,))
    main_process.start()

    # convert_videos_process = Process(target=convert_videos_process_fn)
    # convert_videos_process.start()

    main_process.join()
    # convert_videos_process.join()

from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
from multiprocessing import cpu_count, current_process, Manager
from traceback import print_exc, format_exc
from urllib.parse import urlparse, urljoin
from requests.adapters import HTTPAdapter
from threading import Lock as threadLock
from hyper.contrib import HTTP20Adapter
from time import sleep, time
from pprint import pprint
import subprocess
import argparse
import requests
import logging
import sys
import os

header = {}
links_file_map = {}
logging.basicConfig(filename='app.log', filemode='w',
                    format='%(name)s - %(levelname)s - %(message)s', level=logging.ERROR)
mpLock = Manager().Lock()
tLock = threadLock()
total_content = 0
BASE_URL = ""
THREAD_NUM = cpu_count()

# All unparsed requests content will be stored in this temporary hidden folder
TEMP_FOLDER = ".asdalkshdalskdhalsdhaslk12313123asdllcvsd"

# HTTP/1.1 adapter
ADAPTER1 = HTTPAdapter(max_retries=5)

# HTTP/2 adapter
ADAPTER2 = HTTP20Adapter(max_retries=5)

TOTAL_LINKS = 0
MAX_RETRIES = 5
TOTAL_RETRIES = 5

# If HTTP/2 is set to True all requests will be made through HTTP/2 otherwise HTTP/1.1
HTTP2 = False

# Request timeout
timeout = 5


def directory_validator(string):
    # This code is used to check if passed in headers_path string is valid path to a file
    # if not FileNotFoundError is raised
    if os.path.isfile(string):
        return string
    raise FileNotFoundError(f"{string} does not point to a file")


def construct_headers(header_path: str):
    global header, HTTP2
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
        pprint(header)
        print("press ctrl+c or ctrl+z if parsed headers are incorrect")
        try:
            sleep(10)
        except:
            logging.error(
                "headers incorrectly parsed check construct_headers() function for debugging")
            sys.exit()
    else:
        print(f"Include headers in {header_path} directory and restart program")
        sys.exit()


def convert_video(video_input: str, video_output: str):
    # These arguments will be passed in with ffmpeg for video conversion
    flags = ["ffmpeg", "-i", video_input, "-f", "mp4", "-vcodec", "libx264", "-preset",
             "ultrafast", "-profile:v", "main", "-acodec", "aac", video_output, "-hide_banner"]
    process = subprocess.Popen(flags)
    process.wait()
    os.unlink(video_input)


def fetch_data(download_url: str, file_name: str, headers: dict, session: requests.Session):
    try:
        if HTTP2:
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
        with mpLock:
            with tLock:
                logging.error(f"{download_url} will be retried later")
                logging.error(str(format_exc()))
                with open("error_links.txt", "a") as error_link_file:
                    error_link_file.write(f"{download_url}\n")
                return

    temp_path = os.path.join(TEMP_FOLDER, file_name)
    with open(temp_path, "wb") as video_file:
        video_file.write(request_data.content)


def download_thread(file_name_maps: dict, link: str, session: requests.Session):
    file_name = file_name_maps[link]
    if os.path.exists(os.path.join(TEMP_FOLDER, file_name)):
        return
    fetch_data(link, file_name, header, session)


def calculate_number_of_threads(num: int):
    if num < THREAD_NUM:
        return num
    return THREAD_NUM


def initialize_threads(links: list, session: requests.Session, link_maps: dict):
    thread_number: int = calculate_number_of_threads(total_content)
    print(f"Starting process {current_process().name}")
    with ThreadPoolExecutor(max_workers=thread_number) as executor:
        for link in links:
            executor.submit(download_thread, link_maps, link, session)


def initialize_parallel_threads(links: list, session: requests.Session):
    if os.path.exists("error_links.txt"):
        os.unlink("error_links.txt")

    global total_content
    os.makedirs(TEMP_FOLDER, exist_ok=True)

    # No: of processes started depend on the number of cores available.
    process_number: int = cpu_count()
    print(f"initializing {process_number} processes for {total_content} links")

    with ProcessPoolExecutor(max_workers=process_number) as processes:
        start = 0
        for _ in range(total_content):
            end = start + THREAD_NUM
            if end > total_content:
                end = total_content
            processes.submit(initialize_threads, links[start:end].copy(), session, links_file_map.copy())
            start = end
            if end == total_content:
                break


def write_file(video_file: str, session: requests.Session):
    files = []
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

        with open("error_links.txt") as file_links:
            error_links = [link.strip() for link in file_links.readlines()]

        global total_content
        total_content = len(error_links)
        print(f"Some download chunks are missing attempting retry {TOTAL_RETRIES - MAX_RETRIES}")
        initialize_parallel_threads(error_links, session)
        return write_file(video_file, session)

    print("Download complete, writing video file")

    with open(video_file, "ab") as movie_file:
        for file in sorted(files, key=int):
            print("Writing file", file)
            with open(os.path.join(TEMP_FOLDER, file), "rb") as movie_chunk:
                movie_file.write(movie_chunk.read().strip())
            # os.unlink(os.path.join(TEMP_FOLDER, file))

    os.unlink("links.txt")
    os.rmdir(TEMP_FOLDER)


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
    args = parser.parse_args()

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
    sess = requests.Session()
    parsed_prefix = "/".join(url.split("/")[:-1])
    sess.mount(parsed_prefix, ADAPTER1)
    if HTTP2:
        # Mount a parsed prefix to the session, with HTTP/2 adapter
        sess.mount(parsed_prefix, ADAPTER2)

    # Fetching m3u8 playlist from url.
    req = sess.get(url, headers=header, timeout=60)

    # links.txt will contain all the links to be downloaded.
    with open("links.txt", "wb") as file:
        file.write(req.content)

    with open("links.txt") as file:
        temp = file.readlines()
        temp = [link.strip() for link in temp]

    parsed_url = urlparse(url)
    base_url: str = f"{parsed_url.scheme}://{parsed_url.netloc}{'/'.join(parsed_url.path.split('/')[:-1])}/"
    BASE_URL = base_url

    # Construct a links list containing the links joined with the base_url.
    # If the link in the m3u8 playlist is already a full link we add that to the result `links list`
    # else we join the base_url with the link partial in the playlist and add that to the `links list`
    links: list = [(link if "https" in link else urljoin(base_url, link))
                   for link in temp if "EXT" not in link]

    # Construct links to file name mappings
    for file_name, link in enumerate(links):
        links_file_map[link] = str(file_name)

    total_content += len(links)
    TOTAL_LINKS = len(links)

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

        sys.exit()

    except Exception as err:
        logging.error(err)
        print_exc()
        sys.exit()

from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
from multiprocessing import cpu_count, current_process, Lock
from urllib.parse import urlparse, urljoin
from requests.adapters import HTTPAdapter
from threading import Lock as threadLock
from traceback import print_exc
from time import sleep, time
from pprint import pprint
import subprocess
import argparse
import requests
import logging
import sys
import os

header = {}
logging.basicConfig(filename='app.log', filemode='w',
                    format='%(name)s - %(levelname)s - %(message)s', level=logging.ERROR)
mpLock = Lock()
tLock = threadLock()
total_content = 0
BASE_URL = ""
THREAD_NUM = cpu_count()
TEMP_FOLDER = ".asdalkshdalskdhalsdhaslk12313123asdllcvsd"
ADAPTER = HTTPAdapter(max_retries=5)
TOTAL_LINKS = 0
MAX_RETRIES = 5
TOTAL_RETRIES = 5


def directory_validator(string):
    if os.path.isfile(string):
        return string
    raise FileNotFoundError(f"{path} does not point to a file")


def construct_headers(header_path: str):
    global header
    print("Request headers\n")
    if os.path.exists(header_path):
        with open(header_path) as file:
            lines = file.readlines()
            lines = [line.strip() for line in lines]
        for line in lines:
            if line[0] == ":":
                temp = line.split(":")
                if temp[1] and temp[2:]:
                    header[":" + temp[1]] = ":".join(temp[2:]).strip()
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


def convert_video(video_input, video_output):
    # These arguments will be passed in with ffmpeg for video conversion
    flags = ["ffmpeg", "-i", video_input, "-f", "mp4", "-vcodec", "libx264", "-preset",
             "ultrafast", "-profile:v", "main", "-acodec", "aac", video_output, "-hide_banner"]
    process = subprocess.Popen(flags)
    process.wait()
    os.unlink(video_input)


def fetch_data(download_url: str, file_name: str, headers: dict, session: requests.Session):
    session.mount(download_url, ADAPTER)
    try:
        request_data = session.get(download_url, headers=headers, timeout=5)
    except Exception:
        with mpLock:
            with tLock:
                logging.error(f"{download_url} will be retried later")
                with open("error_links.txt", "a") as error_link_file:
                    error_link_file.write(f"{download_url}\n")
        return

    temp_path = os.path.join(TEMP_FOLDER, file_name)
    with open(temp_path, "wb") as video_file:
        video_file.write(request_data.content)


def download_thread(i: int, link: str, session: requests.Session):
    file_name = f"{i}"
    if os.path.exists(os.path.join(TEMP_FOLDER, file_name)):
        return
    fetch_data(link, file_name, header, session)


def calculate_number_of_threads(num: int):
    if num < THREAD_NUM:
        return num
    return THREAD_NUM


def initialize_threads(links: list, start: int, session: requests.Session):
    thread_number: int = calculate_number_of_threads(total_content)
    print(f"Starting process {current_process().name}")
    with ThreadPoolExecutor(max_workers=thread_number) as executor:
        for i, link in enumerate(links):
            executor.submit(download_thread, i + start, link, session)


def initialize_parallel_threads(links: list):
    global total_content
    os.makedirs(TEMP_FOLDER, exist_ok=True)

    # No: of processes started depend on the number of cores available
    process_number: int = cpu_count()
    print(f"initializing {process_number} processes for {total_content} links")
    with requests.Session() as session:
        with ProcessPoolExecutor(max_workers=process_number) as processes:
            start = 0
            for _ in range(total_content):
                end = start + THREAD_NUM
                if end > total_content:
                    end = total_content
                processes.submit(initialize_threads, links[start:end], start, session)
                start = end
                if end == total_content:
                    break


def write_file(video_file: str):
    if os.path.exists(video_file):
        os.unlink(video_file)

    with open(video_file, "ab") as movie_file:
        files = []
        for file in os.listdir(TEMP_FOLDER):
            if file.isnumeric():
                files.append(file)

        # The below code is responsible for carrying out 5 retries by default or the retries specified by --retry
        # in case of missing chunks
        global MAX_RETRIES
        if len(files) != TOTAL_LINKS and MAX_RETRIES:
            MAX_RETRIES -= 1
            logging.error(f"{len(files)} chunks was downloaded but {TOTAL_LINKS} chunks was expected,"
                          f"\n downloaded chunk ids {files} retrying with original links")
            with open("links.txt") as file_links:
                original_links = [link.strip() for link in file_links.readlines()]
                original_links = [(link if "https" in link else urljoin(BASE_URL, link))
                                  for link in original_links if "EXT" not in link]
            global total_content
            total_content = len(original_links)
            print(f"Some download chunks are missing attempting retry {TOTAL_RETRIES - MAX_RETRIES}")
            initialize_parallel_threads(original_links)
            return write_file(video_file)

        print("Download complete, writing video file")

        for file in sorted(files, key=int):
            with open(os.path.join(TEMP_FOLDER, file), "rb") as movie_chunk:
                movie_file.write(movie_chunk.read().strip())
            os.unlink(os.path.join(TEMP_FOLDER, file))

    os.unlink("links.txt")
    os.rmdir(TEMP_FOLDER)


if __name__ == "__main__":
    # start the program with -h or --help to get more info on how to use the script
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

    # This function is responsible for parsing the headers file provided in path
    construct_headers(path)

    start_time = time()

    # fetching m3u8 playlist
    req = requests.get(url, headers=header)

    # links.txt will contain all the links to be downloaded
    with open("links.txt", "wb") as file:
        file.write(req.content)

    with open("links.txt") as file:
        temp = file.readlines()
        temp = [link.strip() for link in temp]

    parsed_url = urlparse(url)
    base_url: str = f"{parsed_url.scheme}://{parsed_url.netloc}{'/'.join(parsed_url.path.split('/')[:-1])}/"
    BASE_URL = base_url
    # construct a links array list contains the links joined with the base_url.
    links: list = [(link if "https" in link else urljoin(base_url, link))
                   for link in temp if "EXT" not in link]

    total_content += len(links)
    TOTAL_LINKS = len(links)
    try:
        if args.name:
            name = args.name
        else:
            name = "video"

        # if the video has already been downloaded the below, re-download will be skipped unless --force is used
        if not os.path.exists(name) or args.force:
            initialize_parallel_threads(links)
            write_file(name)

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

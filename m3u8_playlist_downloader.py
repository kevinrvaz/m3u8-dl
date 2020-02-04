from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
from multiprocessing import cpu_count, current_process
from urllib.parse import urlparse, urljoin
from traceback import print_exc
from time import sleep, time
from pprint import pprint
from random import randint
import multiprocessing as mp
import subprocess
import argparse
import requests
import logging
import sys
import os

header = {}
logging.basicConfig(filename='app.log', filemode='w',
                    format='%(name)s - %(levelname)s - %(message)s', level=logging.ERROR)
mpLock = mp.Lock()
total_content = 0
THREAD_NUM = cpu_count()


def construct_headers():
    global header
    print("Request headers\n")
    if os.path.exists("headers.txt"):
        with open("headers.txt") as file:
            lines = file.readlines()
            lines = [line.strip() for line in lines]
        for line in lines:
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
        print("Include headers in a headers.txt file and restart program")
        sys.exit()


def convert_video(video_input, video_output):
    # These arguments will be passed in with ffmpeg for video conversion
    flags = ["ffmpeg", "-i", video_input, "-f", "mp4", "-vcodec", "libx264", "-preset",
            "ultrafast", "-profile:v", "main", "-acodec", "aac", video_output, "-hide_banner"]
    subprocess.Popen(flags)


def fetch_data(base_url: str, file_name: str, header: dict):
    try:
        req = requests.get(base_url, headers=header, timeout=60)
    except:
        try:
            sleep(randint(10, 30))
            req = requests.get(base_url, headers=header, timeout=60)
        except:
            with mpLock:
                with open("error_links.txt", "a") as file:
                    file.write(f"{base_url}\n")
            return

    with open(file_name, "wb") as file:
        file.write(req.content)


def download_thread(i: int, link: str):
    file_name = f"{i}"
    if os.path.exists(file_name):
        return
    fetch_data(link, file_name, header)


def calculate_number_of_threads(num: int):
    if num < THREAD_NUM:
        return num
    return THREAD_NUM


def initialize_threads(links: list, start: int):
    thread_number: int = calculate_number_of_threads(total_content)
    print(f"Starting process {current_process().name}")
    with ThreadPoolExecutor(max_workers=thread_number) as executor:
        for i, link in enumerate(links):
            executor.submit(download_thread, i + start, link)


def initialize_parallel_threads(links: list):
    # No: of processes started depend on the number of cores available
    process_number: int = cpu_count()
    print(f"initializing {process_number} processes")
    with ProcessPoolExecutor(max_workers=process_number) as processes:
        start = 0
        for _ in range(total_content):
            end = start + THREAD_NUM
            if end > total_content:
                end = total_content
            processes.submit(initialize_threads, links[start:end], start)
            start = end
            if end == total_content:
                break


def write_file(name: str):
    if os.path.exists(name):
        os.unlink(name)

    print("Download complete, writing video file")

    with open(name, "ab") as movie_file:
        files = []
        for file in os.listdir():
            if file.isnumeric():
                files.append(file)
        for file in sorted(files, key=int):
            print(f"writing file {file}")
            with open(file, "rb") as movie_chunk:
                movie_file.write(movie_chunk.read().strip())
            os.unlink(file)
    os.unlink("links.txt")


if __name__ == "__main__":
    # start the program with -h or --help to get more info on how to use the script
    parser = argparse.ArgumentParser()
    parser.add_argument("url", help="Pass in a url containing m3u8 playlist", type=str)
    parser.add_argument("-n", "--name", type=str, help="Specify a name to save the downloaded video as, if no name is "
                                                       "specified default name of 'video' will be chosen") 
    parser.add_argument("-c", "--convert", help="Convert the downloaded video to mp4 using ffmpeg", action="store_true")
    args = parser.parse_args()

    print("Logs for the download will be stored in app.log")

    if "url" in args:
        url = args.url
    else:
        url = input("Enter a url containing m3u8 playlist\n")

    # This function is responsible for parsing the headers provided in headers.txt
    construct_headers()

    start_time = time()

    # links.txt will contain all the links to be downloaded
    if not os.path.exists("links.txt"):
        req = requests.get(url, headers=header)

        with open("links.txt", "wb") as file:
            file.write(req.content)

    with open("links.txt") as file:
        temp = file.readlines()
        temp = [link.strip() for link in temp]

    parsed_url: str = urlparse(url)
    base_url: str = f"{parsed_url.scheme}://{parsed_url.netloc}{'/'.join(parsed_url.path.split('/')[:-1])}/"

    # construct a links array list contains the links joined with the base_url.
    links: list = [(link if "https" in link else urljoin(base_url, link))
                   for link in temp if "EXT" not in link]

    total_content += len(links)
    try:
        # This function is responsible initializing the processes that will make the requests to the links.
        initialize_parallel_threads(links)

        if "name" in args:
            name = args.name
        else:
            name = "video"
        # This links is responsible for writing video file
        write_file(name)

        # Begin video conversion if -c or --convert argument is passed in.
        if args.convert:
            convert_video(name, f"{name}.mp4")

        elapsed_time = time() - start_time
        print(f"Elapsed time is {elapsed_time} seconds")
    except Exception as err:
        print_exc()

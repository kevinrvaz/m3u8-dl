from concurrent.futures import ThreadPoolExecutor
from threading import Thread, currentThread, Lock
from urllib.parse import urlparse, urljoin
from pprint import pprint
from time import sleep
import platform
import requests
import logging
import sys
import os

header = {}
logging.basicConfig(filename='app.log', filemode='w',
                    format='%(name)s - %(levelname)s - %(message)s', level=logging.DEBUG)
lock = Lock()
percent_done = 0
total_content = 0


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
            logging.debug(
                "headers incorrectly parsed check construct_headers() function for debugging")
            sys.exit()
    else:
        print("Include headers in a headers.txt file and restart program")
        sys.exit()


def fetch_data(base_url: str, file_name: str, header: dict):
    try:
        req = requests.get(base_url, headers=header, timeout=60)
    except:
        logging.debug("Acquiring lock")
        logging.debug(
            f"An error occured while fetching {base_url} with thread {currentThread().getName()} retrying...\n")
        try:
            req = requests.get(base_url, headers=header, timeout=60)
        except:
            logging.debug(
                f"An error occured while fetching {base_url} debug this issue\n")
            return

    with open(file_name, "wb") as file:
        file.write(req.content)


def download_thread(i: int, link: str):
    logging.debug(f"starting {currentThread().getName()} for link {link}")
    file_name = f"{i}"
    if os.path.exists(file_name):
        logging.debug(f"file exists {link}")
        return
    fetch_data(link, file_name, header)
    on_download_thread_complete()


def calculate_number_of_threads(num: int):
    if num < 50:
        return num
    return 50


def initialize_threads(links: list):
    thread_number: int = calculate_number_of_threads(total_content)

    with ThreadPoolExecutor(max_workers=thread_number) as executor:
        for i, link in enumerate(links):
            executor.submit(download_thread, i, link)

    if os.path.exists("video"):
        os.unlink("video")

    print("Download complete, writing video file")

    with open("video", "ab") as movie_file:
        files = []
        for file in os.listdir():
            if file.isnumeric():
                files.append(file)
        for file in sorted(files, key=int):
            logging.debug(f"writing file {file}")
            with open(file, "rb") as movie_chunk:
                movie_file.write(movie_chunk.read().strip())
            os.unlink(file)
    os.unlink("links.txt")


def on_download_thread_complete():
    with lock:
        global percent_done
        percent_done += 1
        # try:
        #     if platform.system() == "Windows":
        #         os.system("cls")
        #     else:
        #         os.system("clear")
        # except:
        #     pass
        print(f"{(percent_done/total_content) * 100}% done")


if __name__ == "__main__":
    print("Logs for the download will be stored in app.log")
    try:
        url = sys.argv[1]
    except:
        url = input("Enter a url containing m3u8 playlist\n")

    construct_headers()
    if not os.path.exists("links.txt"):
        req = requests.get(url, headers=header)

        with open("links.txt", "wb") as file:
            file.write(req.content)

    with open("links.txt") as file:
        temp = file.readlines()
        temp = [link.strip() for link in temp]

    parsed_url: str = urlparse(url)
    base_url: str = f"{parsed_url.scheme}://{parsed_url.netloc}{'/'.join(parsed_url.path.split('/')[:-1])}/"
    links: list = [(link if "https" in link else urljoin(base_url, link))
                   for link in temp if "EXT" not in link]

    # global total_content
    total_content += len(links)
    try:
        initialize_threads(links)
    except Exception as err:
        print(err)

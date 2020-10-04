from multiprocessing import current_process
from traceback import print_exc
from random import SystemRandom
from time import sleep

from .videolib.convertor import convert_video, concat_all_ts, get_ts_start_time
from .common.constants import PORT,IP
from .common.base import Client

import platform
import sys


def get_task(total_links, file_meta_data, stop=False, debug=False):
    while not stop:
        try:
            while True:
                if platform.system() == "Windows":
                    client = Client(IP, PORT)
                else:
                    client = Client("", PORT)

                client.send_data("GET_FILENAME_QUEUE")
                data = client.receive_data()
                if debug:
                    print(f"begin processing {data}")
                if data:
                    break
                timer = SystemRandom()
                sleep(timer.randrange(1, 10))

            if data.isnumeric():
                if debug:
                    print(f"Processed links {len(file_meta_data)} links downloaded by server {data}")
                break

            if data and not data.isnumeric():
                file_meta_data[data] = get_ts_start_time(data)

            if len(file_meta_data) == total_links:
                stop = True
                continue

            elif not data.isnumeric():
                continue
        except:
            print_exc()
            sys.exit()

    return file_meta_data


def start_process(total_links, file_name, convert, debug):
    file_meta_data = get_task(total_links, {}, False, debug)

    with open("ts_list.txt", "w") as file:
        for file_path in sorted(list(file_meta_data.keys()), key=lambda k: file_meta_data[k]):
            file.write(f"file '{file_path}'\n")

    if platform.system() == "Windows":
        client = Client(IP, PORT)
    else:
        client = Client("", PORT)

    client.send_data("STOP")

    if debug:
        print("Concatenating")
    concat_all_ts(file_name)

    if convert:
        if debug:
            print("Converting to mp4")
        convert_video(file_name, f"{file_name}.mp4")


# video_handling process is responsible for constructing a graph to filter out duplicate video frames,
# concat all .ts files and convert the resulting concatenation to mp4
def video_handling(total_links, file_name, convert, debug=False):
    print(f"Starting video handling process {current_process().name}")

    try:
        sleep(10)
        start_process(total_links, file_name, convert, debug)

    except (KeyboardInterrupt, Exception):
        print_exc()
        sys.exit()

    print(f"Stopping video handling process {current_process().name}")

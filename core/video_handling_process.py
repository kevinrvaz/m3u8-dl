from .videolib.convertor import convert_video, concat_all_ts, get_ts_start_time
from .common.base import Client, Graph
from .common.constants import IP, PORT
from multiprocessing import current_process
from time import sleep
from traceback import print_exc
import sys


def get_task(total_links, file_meta_data, stop=False):
    try:
        data = ""
        while not stop:
            client = Client("", PORT)
            client.send_data("GET_FILENAME_QUEUE")
            data = client.receive_data()
            if data:
                break
            sleep(40)

        if data and not data.isnumeric():
            file_meta_data[data] = get_ts_start_time(data)

        if len(file_meta_data) == total_links:
            return file_meta_data

        elif not data.isnumeric():
            return get_task(total_links, file_meta_data)
        return file_meta_data
    except:
        print_exc()


def start_process(total_links, file_name):
    file_meta_data = get_task(total_links, {})

    # non_duplicates = []
    #
    # visited = {}
    # graph = Graph(len(file_meta_data), list(file_meta_data.values()), directed=True)
    # for file in file_meta_data.keys():
    #     if file_meta_data[file] in visited:
    #         graph.add_edge(str(file_meta_data[file]), file)
    #     else:
    #         graph.add_edge(str(file_meta_data[file]), file)
    #         visited[file_meta_data[file]] = 1
    # print(graph)
    # for _, adjacent_nodes in graph:
    #     non_duplicates.append(adjacent_nodes.keys()[0])

    with open("ts_list.txt", "w") as file:
        for file_path in sorted(list(file_meta_data.keys()), key=lambda k: file_meta_data[k]):
            file.write(f"file '{file_path}'\n")

    client = Client(IP, PORT)
    client.send_data("STOP")

    print("Concatenating")
    concat_all_ts(file_name)
    convert_video(file_name, f"{file_name}.mp4")


# video_handling process is responsible for constructing a graph to filter out duplicate video frames,
# concat all .ts files and convert the resulting concatenation to mp4
def video_handling(total_links, file_name):
    print(f"Starting video handling process {current_process().name}")

    try:
        start_process(total_links, file_name)

    except (KeyboardInterrupt, Exception):
        print_exc()
        sys.exit()

    print(f"Stopping video handling process {current_process().name}")

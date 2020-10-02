from multiprocessing import current_process
from traceback import print_exc
from queue import Queue
from typing import Any

from .common.constants import PORT, HEADER_SIZE,IP
from .common.base import Server

import platform
import pickle
import socket
import sys


def send_data(client: socket.socket, data: str) -> None:
    """
    Abstract the sending of data to the client.

    Parameters
    ----------
    client : socket.socket
        The client socket to which we send data

    data : str
        The data to send to the client socket
    """
    client.send(bytes(data, "utf-8"))
    client.close()


def receive_data(client: socket.socket, d_type: str = "str", debug: bool = False) -> Any:
    """
    Abstract receiving data from client.

    Parameters
    ----------
    client : socket.socket
        The client socket which will receive data

    d_type : str, optional
        A string specifying the expected data type (default is "str")

    debug : bool
        A bool specifying whether to print debug options (default is False)

    Returns
    -------
    str
        The data received from the client socket
    """
    got_data = []
    while True:
        temp = client.recv(4096)
        if len(temp) <= 0 or not temp:
            break
        got_data.append(temp)

    data = b"".join(got_data)

    client.close()

    if debug:
        print(f"Data received by server of size {len(data)} bytes")

    if d_type == "bytes":
        return pickle.loads(data)
    return data.decode("utf-8")


class ProducerServerProcess:
    """
    Producer Server Process.

    A class that models a server that acts as a way of passing messages between download_process and
    video_handling process.

    Attributes
    ----------
    __server : Server
        The socket that listens on the ip and port provided in the __init__() method

    __queue : Queue
        The worker queue that is responsible for passing data between download_process and video_handling process

    __stop : bool
        This variable is used to tell the producer_server_process to stop the server

    __sent : int
        This is used to keep track of the items sent to the video_handling process

    Methods
    -------
    start()
        This method is used to start the ProducerServerProcess server

    process_action(action: str, client: socket.socket)
        This method is used to process the actions received by the download_process and video_handling process
    """

    def __init__(self, ip: str, port: int):
        """
        Initialize object of ProducerServerProcess to ip and port parameters.

        Parameters
        ----------
        ip : str
            The ip address to bind the server with.

        port : int
            The port to bind the server with.
        """
        self.__server: Server = Server(ip, port)
        self.__queue: Queue = Queue()
        self.__update_links: int = 0
        self.__stop_queue = False
        self.__stop: bool = False
        self.__sent: int = 0

    def start(self, debug: bool) -> None:
        """Start the server."""
        soc = self.__server.socket
        while not self.__stop:
            try:

                client, address = soc.accept()
                data = client.recv(HEADER_SIZE)
                action = data.decode("utf-8").split()[0].strip()
                if debug:
                    print(f"Received action {action} from {address}")
                self.process_action(action, client)

            except (KeyboardInterrupt, Exception):
                print_exc()
                sys.exit()

    def process_action(self, action: str, client: socket.socket) -> None:
        """
        Perform actions depending on the flow of file.

        Parameters
        ----------
        action : str
            The action that the server needs to perform

        client : socket.socket
            The socket connected with the client
        """
        # The POST_FILENAME_QUEUE action is used to add a file_name to the work queue, from the
        # download_process
        if action == "POST_FILENAME_QUEUE":
            data = receive_data(client, "bytes")
            for item in data:
                self.__queue.put(item)

        elif action == "STOP_QUEUE":
            data = receive_data(client).strip()
            self.__stop_queue = True
            self.__update_links = int(data)

        # The GET_FILENAME_QUEUE action is used to query the work queue to get the next task to the
        # video_handling process
        elif action == "GET_FILENAME_QUEUE" and not self.__queue.empty():
            self.__sent += 1
            data = self.__queue.get()
            send_data(client, data)

        elif action == "GET_FILENAME_QUEUE" and self.__stop_queue:
            send_data(client, str(self.__update_links))

        elif action == "STOP":
            self.__stop = True


# producer_server_process is responsible for passing of messages between the download_process and
# video_handling process supported actions: - POST_FILENAME_QUEUE, GET_FILENAME_QUEUE, POST_CONVERT_VIDEO,
# GET_CONVERT_VIDEO, POST_CONCAT_TS, GET_CONCAT_TS, STOP
def producer_server_process(debug=False):
    """Start the ProducerServerProcess."""
    print(f"Started Producer Process {current_process().name}")

    if platform.system() == "Windows":
        producer = ProducerServerProcess(IP, PORT)
    else:
        producer = ProducerServerProcess("", PORT)

    try:

        producer.start(debug)

    except (KeyboardInterrupt, Exception):
        print_exc()
        sys.exit()

    print(f"Stopped Producer Server {current_process().name}")

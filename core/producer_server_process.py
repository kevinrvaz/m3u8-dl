from .common.constants import IP, PORT, HEADER_SIZE
from multiprocessing import current_process
from .common.base import Server
from traceback import print_exc
from queue import Queue
from typing import Any
import pickle
import socket
import sys


def send_data(client: socket.socket, data: str) -> None:
    """ A function used to abstract the sending of data to the client

    Parameters
    ----------
    client : socket.socket
        The client socket to which we send data

    data : str
        The data to send to the client socket
    """

    client.send(bytes(data, "utf-8"))


def receive_data(client: socket.socket, d_type: str = "str") -> Any:
    """ A function used to abstract receiving data from client

    Parameters
    ----------
    client : socket.socket
        The client socket which will receive data

    d_type : str, optional
        A string specifying the expected data type (default is "str")

    Returns
    -------
    str
        The data received from the client socket
    """
    if d_type == "bytes":
        data = client.recv(4096)
        return pickle.loads(data)
    return client.recv(4096).decode("utf-8")


class ProducerServerProcess:
    """
    A class that models a server that acts as a way of passing messages between download_process and
    video_handling process

    Attributes
    ----------
    __server : Server
        The socket that listens on the ip and port provided in the __init__() method

    __video_file_name : str
        The video_file_name is passed to the video_handling process

    __queue : Queue
        The worker queue that is responsible for passing data between download_process and video_handling process

    __concat : bool
        This variable is used to tell the video_handling process to start concatenating all .ts files (default is False)

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
        Parameters
        ----------
        ip : str
            The ip address to bind the server with.

        port : int
            The port to bind the server with.
        """

        self.__server: Server = Server(ip, port)
        self.__video_file_name: str = ""
        self.__queue: Queue = Queue()
        self.__update_links: int = 0
        self.__stop_queue = False
        self.__concat: bool = False
        self.__stop: bool = False
        self.__sent: int = 0

    def start(self) -> None:
        """A function used to start the server"""
        soc = self.__server.socket
        while not self.__stop:
            try:

                client, address = soc.accept()
                data = client.recv(HEADER_SIZE)
                action = data.decode("utf-8").split()[0].strip()
                self.process_action(action, client)

                client.close()

            except (KeyboardInterrupt, Exception) as err:
                print_exc()
                sys.exit()

    def process_action(self, action: str, client: socket.socket) -> None:
        """
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
            print(data)
            self.__update_links = int(data)

        # The GET_FILENAME_QUEUE action is used to query the work queue to get the next task to the
        # video_handling process
        elif action == "GET_FILENAME_QUEUE" and not self.__queue.empty():
            self.__sent += 1
            data = self.__queue.get()
            send_data(client, data)

        elif action == "GET_FILENAME_QUEUE" and self.__stop_queue:
            send_data(client, str(self.__update_links))

        # The POST_CONVERT_VIDEO action is used to tell the producer_server_process that it can begin the
        # video conversion to mp4
        elif action == "POST_CONVERT_VIDEO":
            data = receive_data(client)
            self.__video_file_name = data

        # The GET_CONVERT_VIDEO action is used to send the file_name to the video handling process so,
        # that it can begin conversion of the file to mp4
        elif action == "GET_CONVERT_VIDEO" and self.__video_file_name:
            send_data(client, self.__video_file_name)
            self.__video_file_name = ""

        # The POST_CONCAT_TS action is used to tell the producer_server_process that it can begin the
        # concatenation of all the downloaded .ts files
        elif action == "POST_CONCAT_TS":
            self.__concat = True

        # The GET_CONCAT_TS action is used to tell the video_handling process that it can begin the
        # concatenation of all the .ts files
        elif action == "GET_CONCAT_TS" and self.__concat:
            send_data(client, "YES")
            self.__concat = False

        elif action == "STOP":
            self.__stop = True


# producer_server_process is responsible for passing of messages between the download_process and
# video_handling process supported actions: - POST_FILENAME_QUEUE, GET_FILENAME_QUEUE, POST_CONVERT_VIDEO,
# GET_CONVERT_VIDEO, POST_CONCAT_TS, GET_CONCAT_TS, STOP
def producer_server_process():
    """A function that starts the ProducerServerProcess"""
    print(f"Started Producer Process {current_process().name}")
    producer = ProducerServerProcess("", PORT)

    try:

        producer.start()

    except (KeyboardInterrupt, Exception):
        sys.exit()

    print(f"Stopped Producer Server {current_process().name}")

from typing import Optional, Any
import socket


class BaseSocketServer:

    """
    A class used to abstract the sending and receiving of data via a socket.

    ...

    Attributes
    ----------
    socket : socket.socket
        A socket object with which the abstraction needs to be made.

    Methods
    -------
    send_data(data: Any)
        A method to send data to the connected socket.

    receive_data(size: int = 4096)
        A method to receive data from the connected socket.
    """

    def __init__(self, soc: socket.socket):
        """
        Initialize BaseSocketServer Object to soc.

        Parameters
        ----------
        soc : socket.socket
            A socket object with which the abstraction needs to be made.
        """
        self.socket = soc

    def send_data(self, data: Any, d_type: str = "str") -> None:
        """
        Send data to the connected socket.

        Parameters
        ----------
        data : Any
            The data to be sent to the connected socket.

        d_type : str
            The type of data to be sent
        """
        if d_type == "bytes":
            self.socket.send(data)
        else:
            self.socket.send(bytes(data, "utf-8"))

    def receive_data(self, size: int = 4096, data_type: str = str) -> Optional[Any]:
        """
        Receive data to the connected socket.

        Parameters
        ----------
        size : int, optional
            The size of data the socket should accept (default is 4096).

        data_type : str, optional
            The expected data_type of the received data (default is str).

        Returns
        -------
        Optional[Any]
            The data received by the socket
        """
        data = self.socket.recv(size)
        if len(data) <= 0 or data is None:
            return None
        if data_type == bytes:
            return data

        return data.decode("utf-8")


class Server(BaseSocketServer):

    """
    A class used to abstract the socket that will act as the server.

    ....
    """

    def __init__(self, ip, port):
        """
        Initialize Server Object with ip and port parameters.

        Parameters
        ----------
        ip : str
            A string specifying the ip to bind the socket with.

        port: int
            A number specifying the port to bind the socket with.
        """
        super(Server, self).__init__(socket.socket(
            socket.AF_INET, socket.SOCK_STREAM))
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.bind((ip, port))
        self.socket.listen(10)


class Client(BaseSocketServer):

    """
    A class used to abstract the socket that will connect with the server.

    ...
    """

    def __init__(self, ip, port):
        """
        Initialize Client Object with ip and port parameters.

        Parameters
        ----------
        ip : str
            A string specifying the ip to bind the socket with.

        port: int
            A number specifying the port to bind the socket with.
        """
        super(Client, self).__init__(socket.socket(
            socket.AF_INET, socket.SOCK_STREAM))
        self.socket.connect((ip, port))

from typing import Optional, Any, Dict, List
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
        Parameters
        ----------
        soc : socket.socket
            A socket object with which the abstraction needs to be made.
        """

        self.socket = soc

    def send_data(self, data: Any, d_type: str = "str") -> None:
        """
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
    A class used to abstract the socket that will act as the server

    ....
    """

    def __init__(self, ip, port):
        """
        Parameters
        ----------

        ip : str
            A string specifying the ip to bind the socket with.

        port: int
            A number specifying the port to bind the socket with.
        """

        super(Server, self).__int__(socket.socket(socket.AF_INET, socket.SOCK_STREAM))
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.bind((ip, port))
        self.socket.listen(10)


class Client(BaseSocketServer):
    """
    A class used to abstract the socket that will connect with the server

    ...
    """

    def __init__(self, ip, port):
        """
        Parameters
        ----------

        ip : str
            A string specifying the ip to bind the socket with.

        port: int
            A number specifying the port to bind the socket with.
        """

        super(Client, self).__int__(socket.socket(socket.AF_INET, socket.SOCK_STREAM))
        self.socket.connect((ip, port))


class GraphNode:
    """
    A class that defines the satellite data held by each node in a graph

    ...

    Attributes
    ----------
    data: str
        The data held by the node in the graph

    adjacent_nodes: Dict[str, int]
        A dictionary containing all the nodes adjacent to the current node

    Methods
    -------
    add_edge(data: str)
        Add the node data as key in the adjacent_nodes dictionary

    remove_edge(data: str)
        Delete the node with key data from the adjacent_nodes dictionary
    """

    def __init__(self, data: str):
        """
        Parameters
        ----------
        data : str
            The data to be stored in the node
        """

        self.data: str = data
        self.adjacent_nodes: Dict[str, int] = {}

    def add_edge(self, data: str) -> None:
        """
        Parameters
        ----------
        data : str
            The node data to add to the adjacent_nodes dictionary
        """

        self.adjacent_nodes[data] = 1

    def remove_edge(self, data: str) -> None:
        """
        Parameters
        ----------
        data : str
            The node data that needs to be removed from the adjacent_nodes dictionary
        """

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
        return self.data


class Graph:
    """
    A class that defines the graph abstract data-type

    ...

    Attributes
    ----------
    size : int
        The number of nodes in the graph

    nodes : Dict[str, GraphNode]
        A dictionary containing the nodes of the graph

    Methods
    -------
    add_edge(node_1: str, node_2: str)
        Add an edge between node_1 and node_2

    remove_edge(node_1: str, node_2: str)
        Remove an edge between node_1 and node_2
    """
    def __init__(self, number_of_nodes: int, nodes: List[str] = None, directed: bool = False):
        """
        Parameters
        ----------
        number_of_nodes: int
            The number of nodes to be added to the graph

        nodes : List[str], optional
            The list of nodes to create the graph with

        directed : bool, optional
            Specify if the graph is directed or not (default is False)
        """

        self.size: int = number_of_nodes
        self.directed = directed
        if nodes:
            self.nodes: Dict[str, GraphNode] = {str(k): GraphNode(str(k)) for k in nodes}
        else:
            self.nodes: Dict[str, GraphNode] = {str(k): GraphNode(str(k)) for k in range(self.size)}

    def add_edge(self, node_1: str, node_2: str) -> None:
        """
        Parameters
        ---------
        node_1 : str
            The node to which we need to add an edge
        node_2 : str
            The node to which we need to add an edge
        """

        self.nodes[node_1].add_edge(node_2)
        if not self.directed:
            self.nodes[node_2].add_edge(node_1)

    def remove_edge(self, node_1: str, node_2: str) -> None:
        """
        Parameters
        ---------
        node_1 : str
            The node from which we remove an edge
        node_2 : str
            The node from which we remove an edge
        """

        self.nodes[node_1].remove_edge(node_2)
        if not self.directed:
            self.nodes[node_2].remove_edge(node_1)

    def __getitem__(self, key):
        return self.nodes[key]

    def __len__(self):
        return len(self.nodes)

    def __iter__(self):
        for node, val in self.nodes.items():
            yield node, val

    def __repr__(self):
        return str(self.nodes.values())

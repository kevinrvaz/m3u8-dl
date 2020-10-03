from urllib.parse import urlparse
from typing import Optional

import write_file_no_gil
import requests


def fetch_data(download_url: str, session: requests.Session,
               timeout: int, file_path: str, http2: bool) -> Optional[str]:
    """
    Fetch Data from Url.

    Parameters
    ----------
    download_url : str
        The url that hosts the .ts file

    session : requests.Session
        The session using which we can make a request

    timeout : int
        The time period after which the request expires

    file_path : str
        The path where the file needs to be stored

    http2: bool
        A boolean to specify the need for http2 support

    Returns
    -------
    Optional[str]
        Returns a string containing the download link that failed
    """
    try:
        if http2:
            if ":path" in session.headers:
                parsed_suffix = urlparse(download_url).path
                session.headers[":path"] = parsed_suffix

        request_data = session.get(download_url, timeout=timeout)

        if request_data.status_code == 302:
            request_data = redirect_handler(session, request_data.content)

    except (ConnectionResetError, ConnectionRefusedError, ConnectionError,
            TimeoutError, ConnectionAbortedError, OSError):
        return download_url

    if isinstance(request_data, bytes):
        data = request_data
    else:
        data = request_data.content

    write_file_no_gil.write_file(file_path, data)

    return None


def redirect_handler(session: requests.Session, request_body: bytes, retry: int = 5) -> bytes:
    text = request_body.decode().split(" ")
    url = text[-1]
    parsed_url = urlparse(url)

    authority = parsed_url.netloc
    path = parsed_url.path

    temp_auth = session.headers[":authority"]
    temp_path = session.headers[":path"]
    temp_origin = session.headers["origin"]

    session.headers[":authority"] = authority
    session.headers[":path"] = path
    session.headers["origin"] = "null"

    request_data = session.get(url)

    session.headers[":authority"] = temp_auth
    session.headers[":path"] = temp_path
    session.headers["origin"] = temp_origin

    if request_data.status_code == 403:
        raise ConnectionAbortedError("403")
    elif request_data.status_code == 302 and retry:
        return redirect_handler(session, request_data.content, retry - 1)

    return request_data.content

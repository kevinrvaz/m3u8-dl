from urllib.parse import urlparse
from typing import Optional

import requests


def fetch_data(download_url: str, session: requests.Session,
               timeout: int, file_path: str, http2: bool) -> Optional[str]:
    """
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

        request_data: requests.Response = session.get(download_url, timeout=timeout)
    except (ConnectionResetError, ConnectionRefusedError, ConnectionError,
            TimeoutError, ConnectionAbortedError, OSError):
        return download_url

    with open(file_path, "wb") as video_file:
        video_file.write(request_data.content.strip())

    return None

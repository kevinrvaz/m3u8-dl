from urllib.parse import urlparse
from typing import Optional
import requests


# noinspection PyBroadException
def fetch_data(download_url: str, headers: dict, session: requests.Session,
               timeout: int, file_path: str, http2: bool = False) -> Optional[str]:
    """
    Parameters
    ----------
    download_url : str
        The url that hosts the .ts file

    headers : dict
        The request headers for the download url

    session : requests.Session
        The session using which we can make a request

    timeout : int
        The time period after which the request expires

    file_path : str
        The path where the file needs to be stored

    http2 : bool, optional
        Specify whether to use HTTP/2 adapters to make the request (default is False)

    Returns
    -------
    Optional[str]
        Returns a string containing the download link that failed
    """

    try:
        if http2:
            timeout += 500
            if ":path" in headers:
                parsed_url_path = urlparse(download_url).path
                headers[":path"] = parsed_url_path

            # if temp_adapter object gets called with the base class __init__ we call the temp_adapter
            # __init__ method.
            temp_adapter = session.get_adapter(download_url)
            if "connections" not in vars(temp_adapter):
                temp_adapter.__init__()

        request_data: requests.Response = session.get(download_url, headers=headers, timeout=timeout)
    except Exception:
        return download_url

    with open(file_path, "wb") as video_file:
        video_file.write(request_data.content.strip())

    return None

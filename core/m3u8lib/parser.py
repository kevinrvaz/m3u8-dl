from urllib.parse import urlparse, urljoin
from typing import List, Dict
import os
import requests


def fetch_playlist_links(session: requests.Session, playlist_url: str
                         , keep: bool = False) -> List[str]:
    """Fetch the m3u8 playlist from the playlist_url.

    Parameters
    ----------
    session : requests.Session
        The session via which the request will be made
    playlist_url : str
        The url where the m3u8 playlist is hosted

    Returns
    -------
    List[str]
        A list with all the urls where the .ts files are hosted
    """
    res: requests.Response = session.get(playlist_url, timeout=60)

    with open("links.txt", "wb") as file:
        file.write(res.content)

    with open("links.txt") as file:
        temp = file.readlines()
        temp = [link.strip() for link in temp]

    if not keep:
        os.unlink("links.txt")

    parsed_url = urlparse(playlist_url)
    base_url: str = f"{parsed_url.scheme}://{parsed_url.netloc}{'/'.join(parsed_url.path.split('/')[:-1])}/"

    # Construct a links list containing the links joined with the base_url.
    # If the link in the m3u8 playlist is already a full link we add that to the result `links list`
    # else we join the base_url with the link partial in the playlist and add that to the `links list`
    links: List[str] = [(link if "https" in link else urljoin(base_url, link))
                        for link in temp if "EXT" not in link]

    return links


def construct_file_name_links_map(links: List[str]) -> Dict[str, str]:
    """Construct a dictionary with link to file name mappings.

    Parameters
    ----------
    links : List[str]
        A list with all the urls of the hosted .ts files

    Returns
    -------
    Dict[str, str]
        A dictionary containing link as key and the corresponding file name as value
    """
    link_file_map = {}

    for file_name, link in enumerate(links):
        link_file_map[link] = str(file_name)

    return link_file_map

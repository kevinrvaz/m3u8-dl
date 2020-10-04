import pathlib
from typing import List, Dict
from urllib.parse import urlparse, urljoin

import requests


def fetch_playlist_links(session: requests.Session, playlist_url: str,
                         keep: bool = False) -> List[str]:
    """Fetch the m3u8 playlist from the playlist_url.

    Parameters
    ----------
    session : requests.Session
        The session via which the request will be made
    playlist_url : str
        The url where the m3u8 playlist is hosted
    keep : bool
        Keep file with links on disk.

    Returns
    -------
    List[str]
        A list with all the urls where the .ts files are hosted
    """
    filename = "links.txt"
    p = pathlib.Path(playlist_url)
    if p.is_file():
        with open(playlist_url) as file:
            temp = file.readlines()
        links: List[str] = [link.strip() for link in temp if not link.startswith("#")]
    else:
        res: requests.Response = session.get(playlist_url, timeout=60)
        temp = [link.strip() for link in res.text.splitlines()]
        parsed_url = urlparse(playlist_url)
        base_url: str = f"{parsed_url.scheme}://{parsed_url.netloc}{'/'.join(parsed_url.path.split('/')[:-1])}/"
        # Construct a links list containing the links joined with the base_url.
        # If the link in the m3u8 playlist is already a full link we add that to the result `links list`
        # else we join the base_url with the link partial in the playlist and add that to the `links list`
        links: List[str] = [(link if parsed_url.scheme in link else urljoin(base_url, link))
                            for link in temp if not link.startswith("#")]
    if keep:
        with open(filename, "w") as file:
            for link in links:
                file.write(f"{link}\n")

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

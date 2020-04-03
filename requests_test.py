from hyper.contrib import HTTP20Adapter
from core.weblib.parse import construct_headers
from core.m3u8lib.parser import fetch_playlist_links
import requests
import pickle

url = input()
headers, _ = construct_headers("headers.txt")

s = requests.Session()
s.mount("https://", HTTP20Adapter(max_retries=10))
s.headers = headers
links = fetch_playlist_links(s, url, True)

with open("links", "wb") as file:
    pickle.dump(links, file)

req_url = links[0]



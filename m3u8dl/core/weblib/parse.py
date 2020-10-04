from typing import Dict, Tuple
from pprint import pprint
from time import sleep

import sys
import os


def construct_headers(header_path: str) -> Tuple[Dict[str, str], bool]:
    """
    Construct headers from Header file.

    Parameters
    ----------
    header_path: str
        The path to the file containing the headers

    Returns
    -------
    Tuple[Dict[str, str], bool]
        Returns a tuple containing the headers and http2 variable
    """
    http2 = False
    header: Dict[str, str] = {}

    print("Parsed Request headers\n")

    if os.path.exists(header_path):
        with open(header_path) as file:
            lines = file.readlines()
            if not lines:
                lines.append("Access-Control-Allow-Origin: *")
                lines.append("User-Agent: Mozilla/5.0 (X11; Linux x86_64) "
                             "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.121 Safari/537.36")

            lines = [line.strip() for line in lines]

        for line in lines:
            if line[0] == ":":

                # This code checks if the given headers are of HTTP/2, if yes then HTTP2 is set to True
                # and all subsequent requests will be made with HTTP/2

                temp = line.split(":")
                if temp[1] and temp[2:]:
                    header[":" + temp[1]] = ":".join(temp[2:]).strip()
                    http2 = True
            else:
                temp = line.split(":")
                if temp[0] and temp[1:]:
                    header[temp[0]] = ":".join(temp[1:]).strip()

        if "cookie" in header:
            del header["cookie"]

        pprint(header)
        print(f"press ctrl+c or ctrl+z if parsed headers of type http2 {http2} are incorrect")

        try:
            sleep(10)
        except KeyboardInterrupt:
            print("headers incorrectly parsed check construct_headers() function for debugging")
            sys.exit()
    else:
        header["Access-Control-Allow-Origin"] = "*"
        header["User-Agent"] = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 " \
                               "(KHTML, like Gecko) Chrome/85.0.4183.121 Safari/537.36"

    return header, http2

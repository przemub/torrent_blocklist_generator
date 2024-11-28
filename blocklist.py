import argparse
import datetime
import email.utils
import http.server
import io
import ipaddress
import logging
import gzip
import os
import shutil
import sys
import threading
import time
import typing

import iso3166
import requests

# Variables shared between threads
global_lock = threading.Lock()
compressed: bool = None
last_blocklist: bytes = None
last_update_time: datetime.datetime = None
next_update_time: datetime.datetime = None
etag: str = None

logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


# Exit program on exceptions within threads
def custom_excepthook(args):
    old_excepthook(args)
    os._exit(1)  # Exit the program with an error code


old_excepthook = threading.excepthook
threading.excepthook = custom_excepthook


class HttpRequestHandler(http.server.BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def _send_headers(self):
        self.send_header("Server", self.version_string())
        self.send_header("Date", self.date_time_string())
        self.send_header(
            "Content-Type", "application/gzip" if compressed else "text/plain"
        )
        self.send_header(
            "Content-Disposition",
            'attachment; filename="blocklist.gz"' if compressed else "inline",
        )
        self.send_header(
            "Last-Modified", email.utils.format_datetime(last_update_time)
        )
        next_update_secs = next_update_time - datetime.datetime.now()
        self.send_header(
            "Cache-Control",
            f"max-age={int(next_update_secs.total_seconds())+10}",
        )
        self.send_header("Content-Length", str(len(last_blocklist)))
        self.send_header("ETag", etag)
        self.end_headers()

    def do_HEAD(self):
        """
        Implement HEAD method that can be used for healthchecks.
        These requests won't be logged.
        """
        if self.path != "/":
            self.send_error(404)
            return

        self.send_response_only(200)
        with global_lock:
            self._send_headers()

    def do_GET(self):
        if self.path != "/":
            self.send_error(404)
            return

        with global_lock:
            self.log_request(200, len(last_blocklist))
            self.send_response_only(200)
            self._send_headers()
            shutil.copyfileobj(io.BytesIO(last_blocklist), self.wfile)

    @classmethod
    def serve(cls, host: str, port: int) -> typing.NoReturn:
        httpd = http.server.HTTPServer((host, port), cls)
        logger.info("Listening on %s, port %d", host, port)
        httpd.serve_forever()


def generate_blacklist(args: argparse.Namespace) -> None:
    global compressed, last_blocklist, last_update_time, etag

    logger.info("Started generating blocklist")
    output = b""

    for country in args.country or []:
        r = requests.get(
            f"http://www.ipdeny.com/ipblocks/data/countries/{country.alpha2.lower()}.zone"
        )
        r.raise_for_status()
        for line in r.text.splitlines():
            network = ipaddress.ip_network(line)
            output += f"{country.name}:{network.network_address}-{network.broadcast_address}\n".encode()

    compressed = not args.no_compress
    if args.no_compress is False:
        output = gzip.compress(output)

    for url in args.gzip_url or []:
        with requests.get(url, stream=True) as r:
            r.raise_for_status()
            if args.no_compress:
                # Decompress
                f = gzip.open(r.raw, mode="r")
                output += f.read()
            else:
                # Append directly
                output += r.raw.read()

    last_blocklist = output
    last_update_time = datetime.datetime.now()
    etag = f'"{hex(hash(last_update_time))}"'

    logger.info("Finished generating blocklist")


def update_loop(args: argparse.Namespace):
    global next_update_time
    while True:
        next_update_time = datetime.datetime.now() + datetime.timedelta(days=1)
        logger.info("Next update at %s", next_update_time)
        time.sleep(86400)

        logger.info("Starting update")
        with global_lock:
            generate_blacklist(args)
        logger.info("Finished update")


def main():
    parser = argparse.ArgumentParser(
        prog="blocklist",
        description="Generate bittorrent peer IP blocklist in PeerGuardian v2 format.\n"
        "\nThis tool can also serve the blocklist from HTTP server and update it\n"
        "every 24 hours. This is useful for clients that can auto-update\n"
        "from an HTTP server, like Transmission.",
        formatter_class=argparse.RawTextHelpFormatter,
    )

    parser.add_argument(
        "-gu",
        "--gzip-url",
        nargs="*",
        help="Link to a GZIP compressed PGv2 blacklist to include",
    )
    parser.add_argument(
        "-c",
        "--country",
        nargs="*",
        type=iso3166.countries.get,
        help="Country code or name to block",
    )

    parser.add_argument(
        "-n",
        "--no-compress",
        action="store_true",
        help="Don't compress the output as GZIP",
    )

    output_group = parser.add_mutually_exclusive_group()

    output_group.add_argument(
        "-o",
        "--output",
        type=argparse.FileType("wb"),
        default=sys.stdout.buffer,
        help="The filename to which we should write the blocklist",
    )

    output_group.add_argument(
        "-s",
        "--serve",
        help="Instead of writing to a file, start a HTTP server hosting the blocklist.\n"
        "The blocklist will be auto-updated every 24 hours.\n"
        "This flag takes the address to listen at in host:port format.\n"
        "For example, to serve on all devices on port 8080, pass --server 0.0.0.0:8000.",
    )

    args = parser.parse_args()

    if args.gzip_url is None and args.country is None:
        logger.fatal(
            "Please provide at least one source (--gzip-url and/or --country)."
        )
        parser.print_help()
        sys.exit(1)

    if args.serve is not None:
        host, port = args.serve.split(":")

        generate_blacklist(args)

        update_thread = threading.Thread(target=update_loop, args=(args,))
        serve_thread = threading.Thread(
            target=HttpRequestHandler.serve, args=(host, int(port))
        )

        update_thread.start()
        serve_thread.start()

        try:
            update_thread.join()
            serve_thread.join()
        except KeyboardInterrupt:
            os._exit(1)

    else:
        if args.output == sys.stdout.buffer:
            print(
                'No output file passed - writing uncompressed list to stdout. Pass "-o -" to force compression.',
                file=sys.stderr,
            )
            args.no_compress = True

        generate_blacklist(args)

        try:
            args.output.write(last_blocklist)
        finally:
            args.output.close()


if __name__ == "__main__":
    main()

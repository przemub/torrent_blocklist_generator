import argparse
import ipaddress
import gzip
import sys

import iso3166
import requests


def main():
    parser = argparse.ArgumentParser(
        prog="blocklist",
        description="Generate bittorrent peer IP blocklist in PeerGuardian v2 format.",
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

    parser.add_argument(
        "-o",
        "--output",
        type=argparse.FileType("wb"),
        default=sys.stdout.buffer,
        help="The filename to which we should write the blocklist",
    )

    args = parser.parse_args()

    if args.gzip_url is None and args.country is None:
        parser.print_help()
        sys.exit(1)

    try:
        if args.output == sys.stdout.buffer:
            print(
                'No output file passed - writing uncompressed list to stdout. Pass "-o -" to force compression.',
                file=sys.stderr,
            )
            args.no_compress = True

        if args.no_compress is True:
            orig_file = None
            file = args.output
        else:
            orig_file = args.output
            file = gzip.open(args.output, mode="wb")

        for url in args.gzip_url or []:
            with requests.get(url, stream=True) as r:
                r.raise_for_status()
                f = gzip.open(r.raw, mode="r")
                for line in f:
                    file.write(line)

        for country in args.country or []:
            r = requests.get(
                f"http://www.ipdeny.com/ipblocks/data/countries/{country.alpha2.lower()}.zone"
            )
            r.raise_for_status()
            for line in r.text.splitlines():
                network = ipaddress.ip_network(line)
                file.write(
                    f"{country.name}:{network.network_address}-{network.broadcast_address}\n".encode()
                )
    finally:
        file.close()
        if orig_file is not None:
            orig_file.close()


if __name__ == "__main__":
    main()

# BitTorrent blocklist generator

This is a little script that combines existing blocklists
and country IP lists to output blocklists in a format 
compatible with, for example, Transmission.

## Usage

```
usage: blocklist [-h] [-gu [GZIP_URL ...]] [-c [COUNTRY ...]] [-n] [-o OUTPUT | -s SERVE]

Generate bittorrent peer IP blocklist in PeerGuardian v2 format.

This tool can also serve the blocklist from HTTP server and update it
every 24 hours. This is useful for clients that can auto-update
from an HTTP server, like Transmission.

options:
  -h, --help            show this help message and exit
  -gu, --gzip-url [GZIP_URL ...]
                        Link to a GZIP compressed PGv2 blacklist to include
  -c, --country [COUNTRY ...]
                        Country code or name to block
  -n, --no-compress     Don't compress the output as GZIP
  -o, --output OUTPUT   The filename to which we should write the blocklist
  -s, --serve SERVE     Instead of writing to a file, start a HTTP server hosting the blocklist.
                        The blocklist will be auto-updated every 24 hours.
                        This flag takes the address to listen at in host:port format.
                        For example, to serve on all devices on port 8080, pass --server 0.0.0.0:8000.
```

## Links
- [An example blocklist you could use](https://github.com/Naunter/BT_BlockLists)

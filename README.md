# BitTorrent blocklist generator

This is a little script that combines existing blocklists
and country IP lists to output blocklists in a format 
compatible with, for example, Transmission.

## Usage

```
usage: blocklist [-h] [-gu [GZIP_URL ...]] [-c [COUNTRY ...]] [-n] [-o OUTPUT]

Generate bittorrent peer IP blocklist in PeerGuardian v2 format.

options:
  -h, --help            show this help message and exit
  -gu, --gzip-url [GZIP_URL ...]
                        Link to a GZIP compressed PGv2 blacklist to include
  -c, --country [COUNTRY ...]
                        Country code or name to block
  -n, --no-compress     Don't compress the output as GZIP
  -o, --output OUTPUT   The filename to which we should write the blocklist
```

## Links
- [An example blocklist you could use](https://github.com/Naunter/BT_BlockLists)



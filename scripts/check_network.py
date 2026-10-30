"""Check TCP reachability of the desktop ingest listener; sends no image data."""

import argparse
import socket
import sys


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("host", help="desktop LAN address")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--timeout", type=float, default=3.0)
    args = parser.parse_args()
    if not 1 <= args.port <= 65535 or args.timeout <= 0:
        parser.error("port must be 1..65535 and timeout must be positive")

    try:
        with socket.create_connection((args.host, args.port), timeout=args.timeout):
            print(f"TCP_REACHABLE: {args.host}:{args.port}")
            return 0
    except OSError as exc:
        print(f"TCP_UNREACHABLE: {args.host}:{args.port}: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

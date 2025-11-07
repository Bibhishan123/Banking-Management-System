
import json
import sys
from typing import Any, Dict, Optional

import requests

BASE = "http://127.0.0.1:5000/api/v1"


def _url(path: str) -> str:
    return BASE.rstrip("/") + "/" + path.lstrip("/")


def _print_response(r: requests.Response) -> None:
    try:
        print(json.dumps(r.json(), indent=2))
    except Exception:
        print(r.text)
    print("HTTP", r.status_code)


def usage() -> None:
    print("Usage:")
    print("  python client/cli.py [--base=URL] command [args...]")
    print("Commands:")
    print("  create NAME NUMBER [BALANCE]")
    print("  get ID")
    print("  list [LIMIT] [OFFSET]")
    print("  update ID key=value [key=value ...]   (keys: name,number,balance)")
    print("  delete ID")
    sys.exit(1)


def main(argv: Optional[list] = None) -> int:
    global BASE
    if not argv:
        usage()

    if argv[0].startswith("--base="):
        BASE = argv[0].split("=", 1)[1] or BASE
        argv = argv[1:]
    if not argv:
        usage()

    cmd = argv[0].lower()
    args = argv[1:]

    try:
        if cmd == "create":
            if len(args) < 2:
                print("create requires NAME and NUMBER")
                return 2
            name = args[0]
            number = args[1]
            payload = {"name": name, "number": number}
            if len(args) >= 3:
                try:
                    payload["balance"] = float(args[2])
                except Exception:
                    print("balance must be numeric")
                    return 2
            r = requests.post(_url("/accounts"), json=payload, timeout=5)
            _print_response(r)
            return 0 if r.ok else 1

        if cmd == "get":
            if len(args) != 1:
                print("get requires ID")
                return 2
            r = requests.get(_url(f"/accounts/{args[0]}"), timeout=5)
            _print_response(r)
            return 0 if r.ok else 1

        if cmd == "list":
            params = {}
            if len(args) >= 1:
                params["limit"] = args[0]
            if len(args) >= 2:
                params["offset"] = args[1]
            r = requests.get(_url("/accounts"), params=params or None, timeout=5)
            _print_response(r)
            return 0 if r.ok else 1

        if cmd == "update":
            if len(args) < 2:
                print("update requires ID and at least one key=value")
                return 2
            ident = args[0]
            payload = {}
            for kv in args[1:]:
                if "=" not in kv:
                    print("invalid pair:", kv)
                    return 2
                k, v = kv.split("=", 1)
                k = k.strip().lower()
                if k == "balance":
                    try:
                        payload[k] = float(v)
                    except Exception:
                        print("balance must be numeric")
                        return 2
                else:
                    payload[k] = v
            r = requests.put(_url(f"/accounts/{ident}"), json=payload, timeout=5)
            _print_response(r)
            return 0 if r.ok else 1

        if cmd == "delete":
            if len(args) != 1:
                print("delete requires ID")
                return 2
            r = requests.delete(_url(f"/accounts/{args[0]}"), timeout=5)
            _print_response(r)
            return 0 if r.ok else 1

        print("Unknown command:", cmd)
        usage()

    except requests.RequestException as exc:
        print("Request failed:", exc)
        return 3


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))

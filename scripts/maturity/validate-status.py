#!/usr/bin/env python3
import argparse
import sys

from status_contract import load_json, validate_history, validate_status


def main():
    parser = argparse.ArgumentParser(description="Validate a sanitized SisTer maturity document")
    parser.add_argument("document")
    parser.add_argument("--history", action="store_true")
    arguments = parser.parse_args()
    try:
        payload = load_json(arguments.document)
        errors = validate_history(payload) if arguments.history else validate_status(payload)
    except (OSError, ValueError) as error:
        errors = [str(error)]
    if errors:
        for error in errors:
            print(f"invalid maturity document: {error}", file=sys.stderr)
        return 1
    print("maturity document validation ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

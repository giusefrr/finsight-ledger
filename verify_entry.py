#!/usr/bin/env python3
"""Recomputes the entry_hash of ONE line of entries.jsonl and compares it
against the one declared in the line itself — the same formula used to
build the entire ledger (SHA-256 of prev_hash + b'\\0' + entry_type + b'\\0' +
payload_raw, NEVER a re-serialization of `payload`), reimplemented here from
scratch in ~15 lines of standard library: no dependency on finsight, no
module of this repository imported.

Usage:
    python3 verify_entry.py <seq> [entries.jsonl]

Exit 0 and "MATCH" if the declared hash matches what this script
recomputes, reading only prev_hash/entry_type/payload_raw of the row with
that `seq`; exit 1 and "MISMATCH" (with the two hashes side by side)
otherwise — a MISMATCH means either that row was altered after being
written, or the file is corrupted.

Note: a MATCH on its own only proves that this row is internally
consistent with itself. It does not prove that its prev_hash is really the
entry_hash of the preceding row (that's what verify_chain.py checks, over
the whole file), nor that the entire chain traces back to an RFC 3161
anchor signed by an external authority (that's what `openssl ts -verify`
checks, see README.md).
"""

from __future__ import annotations

import hashlib
import json
import sys


def compute_entry_hash(prev_hash: str, entry_type: str, payload_raw: str) -> str:
    digest = hashlib.sha256()
    digest.update(prev_hash.encode("utf-8"))
    digest.update(b"\0")
    digest.update(entry_type.encode("utf-8"))
    digest.update(b"\0")
    digest.update(payload_raw.encode("utf-8"))
    return digest.hexdigest()


def main(argv: list[str]) -> int:
    if len(argv) < 1:
        print("usage: python3 verify_entry.py <seq> [entries.jsonl]", file=sys.stderr)
        return 2
    seq_wanted = int(argv[0])
    path = argv[1] if len(argv) > 1 else "entries.jsonl"

    with open(path, encoding="utf-8") as f:
        for line in f:
            entry = json.loads(line)
            if entry["seq"] == seq_wanted:
                break
        else:
            print(f"seq={seq_wanted} not found in {path}", file=sys.stderr)
            return 1

    computed = compute_entry_hash(entry["prev_hash"], entry["entry_type"], entry["payload_raw"])
    declared = entry["entry_hash"]

    print(f"seq        = {entry['seq']}")
    print(f"entry_type = {entry['entry_type']}")
    print(f"prev_hash  = {entry['prev_hash']}")
    print(f"computed   = {computed}")
    print(f"declared   = {declared}")
    if computed == declared:
        print("MATCH")
        return 0
    print("MISMATCH — this entry does not match its declared entry_hash")
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

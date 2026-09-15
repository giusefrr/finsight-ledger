#!/usr/bin/env python3
"""Re-verifies the ENTIRE hash chain of entries.jsonl, line by line, from
the first (prev_hash = 64 zeros) to the last, and prints the final
head_hash.

No dependency on finsight: the formula (SHA-256 of prev_hash + b'\\0' +
entry_type + b'\\0' + payload_raw) is reimplemented here from scratch, with
only Python's standard library, reading exclusively this file.

Usage:
    python3 verify_chain.py entries.jsonl [expected_head_hash]

Without the second argument, prints how many entries were verified and the
final head_hash. With the second argument (e.g. the contents of one of the
anchors/*.head_hash.txt files, or the "head_hash" field of a line of
anchors_index.jsonl), also compares that head_hash against the one just
recomputed: a MATCH ties the chain re-verified this way to an RFC 3161
anchor verifiable with `openssl ts -verify` (see README.md) — the two
verifications together are what proves the entries up to that point in the
chain existed, unchanged, no later than the date signed by that anchor.

Exits with an explicit error (never a silent "looks fine") at the first
point where:
- the prev_hash declared in a row is not the entry_hash of the preceding
  row (the chain has been reordered, or an entry is missing);
- the entry_hash declared in a row does not match what is recomputed from
  that row's prev_hash/entry_type/payload_raw (the row was altered after
  being written).
"""

from __future__ import annotations

import hashlib
import json
import sys

GENESIS_HASH = "0" * 64


def compute_entry_hash(prev_hash: str, entry_type: str, payload_raw: str) -> str:
    digest = hashlib.sha256()
    digest.update(prev_hash.encode("utf-8"))
    digest.update(b"\0")
    digest.update(entry_type.encode("utf-8"))
    digest.update(b"\0")
    digest.update(payload_raw.encode("utf-8"))
    return digest.hexdigest()


def main(argv: list[str]) -> int:
    path = argv[0] if argv else "entries.jsonl"
    expected_final = argv[1].strip() if len(argv) > 1 else None

    prev_hash = GENESIS_HASH
    n = 0
    with open(path, encoding="utf-8") as f:
        for line in f:
            entry = json.loads(line)
            if entry["prev_hash"] != prev_hash:
                print(
                    f"CHAIN BROKEN at seq={entry['seq']}: declared prev_hash "
                    f"({entry['prev_hash']}) is not the entry_hash of the preceding entry "
                    f"({prev_hash})",
                    file=sys.stderr,
                )
                return 1
            computed = compute_entry_hash(
                entry["prev_hash"], entry["entry_type"], entry["payload_raw"]
            )
            if computed != entry["entry_hash"]:
                print(
                    f"TAMPERED: seq={entry['seq']} — declared entry_hash "
                    f"({entry['entry_hash']}) does not match recomputed value "
                    f"({computed})",
                    file=sys.stderr,
                )
                return 1
            prev_hash = entry["entry_hash"]
            n += 1

    print(f"Chain intact: {n} entries verified, from the first (prev_hash=64 zeros) to seq={n}.")
    print(f"final head_hash (seq={n}) = {prev_hash}")
    if expected_final is not None:
        if prev_hash == expected_final:
            print(f"MATCH with expected head_hash ({expected_final})")
        else:
            print(f"does NOT match expected head_hash ({expected_final})", file=sys.stderr)
            return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

#!/usr/bin/env python3
"""Riverifica l'INTERA hash chain di entries.jsonl, riga per riga, dalla
prima (prev_hash = 64 zeri) all'ultima, e stampa l'head_hash finale.

Nessuna dipendenza da finsight: la formula (SHA-256 di prev_hash + b'\\0' +
entry_type + b'\\0' + payload_raw) è reimplementata qui da zero, con la sola
libreria standard di Python, leggendo esclusivamente questo file.

Uso:
    python3 verify_chain.py entries.jsonl [head_hash_atteso]

Senza il secondo argomento, stampa quante entry sono state verificate e
l'head_hash finale. Con il secondo argomento (es. il contenuto di uno dei
file anchors/*.head_hash.txt, o il campo "head_hash" di una riga di
anchors_index.jsonl), confronta anche quell'head_hash con quello appena
ricalcolato: un MATCH lega la catena così riverificata a un anchor RFC 3161
verificabile con `openssl ts -verify` (vedi README.md) — le due verifiche
insieme sono ciò che dimostra che le entry fino a quel punto della catena
esistevano, invariate, non oltre la data firmata da quell'anchor.

Esce con un errore esplicito (mai un "sembra a posto" silenzioso) al primo
punto in cui:
- il prev_hash dichiarato in una riga non è l'entry_hash della riga
  precedente (la catena è stata riordinata, o manca una entry);
- l'entry_hash dichiarato in una riga non corrisponde a quanto ricalcolato
  da prev_hash/entry_type/payload_raw di quella riga (la riga è stata
  alterata dopo essere stata scritta).
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
                    f"CATENA ROTTA a seq={entry['seq']}: prev_hash dichiarato "
                    f"({entry['prev_hash']}) non è l'entry_hash della entry precedente "
                    f"({prev_hash})",
                    file=sys.stderr,
                )
                return 1
            computed = compute_entry_hash(
                entry["prev_hash"], entry["entry_type"], entry["payload_raw"]
            )
            if computed != entry["entry_hash"]:
                print(
                    f"MANOMESSA: seq={entry['seq']} — entry_hash dichiarato "
                    f"({entry['entry_hash']}) non corrisponde a quanto ricalcolato "
                    f"({computed})",
                    file=sys.stderr,
                )
                return 1
            prev_hash = entry["entry_hash"]
            n += 1

    print(f"Catena intatta: {n} entry verificate, dalla prima (prev_hash=64 zeri) a seq={n}.")
    print(f"head_hash finale (seq={n}) = {prev_hash}")
    if expected_final is not None:
        if prev_hash == expected_final:
            print(f"MATCH con l'head_hash atteso ({expected_final})")
        else:
            print(f"NON corrisponde all'head_hash atteso ({expected_final})", file=sys.stderr)
            return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

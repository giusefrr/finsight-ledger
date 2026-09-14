#!/usr/bin/env python3
"""Ricalcola l'entry_hash di UNA riga di entries.jsonl e lo confronta con
quello dichiarato nella riga stessa — la stessa formula usata per costruire
l'intero registro (SHA-256 di prev_hash + b'\\0' + entry_type + b'\\0' +
payload_raw, MAI una ri-serializzazione di `payload`), qui reimplementata da
zero in ~15 righe di libreria standard: nessuna dipendenza da finsight,
nessun modulo di questo repository importato.

Uso:
    python3 verify_entry.py <seq> [entries.jsonl]

Uscita 0 e "MATCH" se l'hash dichiarato corrisponde a quanto ricalcolato da
questo script, leggendo solo prev_hash/entry_type/payload_raw della riga con
quel `seq`; uscita 1 e "MISMATCH" (con i due hash affiancati) altrimenti —
un MISMATCH significa che quella riga è stata alterata dopo essere stata
scritta, oppure che il file è corrotto.

Nota: un MATCH da solo prova solo che questa riga è internamente coerente
con se stessa. Non prova che il suo prev_hash sia davvero l'entry_hash della
riga precedente (quello lo controlla verify_chain.py, sull'intero file), né
che l'intera catena risalga fino a un anchor RFC 3161 firmato da un'autorità
esterna (quello lo controlla `openssl ts -verify`, vedi README.md).
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
        print("uso: python3 verify_entry.py <seq> [entries.jsonl]", file=sys.stderr)
        return 2
    seq_wanted = int(argv[0])
    path = argv[1] if len(argv) > 1 else "entries.jsonl"

    with open(path, encoding="utf-8") as f:
        for line in f:
            entry = json.loads(line)
            if entry["seq"] == seq_wanted:
                break
        else:
            print(f"seq={seq_wanted} non trovato in {path}", file=sys.stderr)
            return 1

    computed = compute_entry_hash(entry["prev_hash"], entry["entry_type"], entry["payload_raw"])
    declared = entry["entry_hash"]

    print(f"seq         = {entry['seq']}")
    print(f"entry_type  = {entry['entry_type']}")
    print(f"prev_hash   = {entry['prev_hash']}")
    print(f"ricalcolato = {computed}")
    print(f"dichiarato  = {declared}")
    if computed == declared:
        print("MATCH")
        return 0
    print("MISMATCH — questa entry non corrisponde al proprio entry_hash dichiarato")
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

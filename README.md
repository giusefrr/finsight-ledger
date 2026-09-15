# FinSight Public Ledger — Live QuestionSet, September 14, 2026

This directory contains **only data and verification tools**, not the
code that produced them. Every command below was actually run, inside
this very directory, without importing anything from the FinSight
project: if you run it yourself, right now, on your own machine, with
only `python3` (standard library) and `openssl`, it must produce the
same result. If a command doesn't work exactly as written, that is a bug
in this README, not something to fix by eye.

## What's in this ledger

- **405 questions** ("this quarter, will [company]'s revenue/margin be
  above/below [threshold]?"), across **28 listed issuers** (full list
  below), sealed into a single `question_set` on **September 14, 2026**.
- Each question was submitted to **3 mechanical baseline engines**
  (`baseline-persistence-v1`, `baseline-persistence-v2`,
  `baseline-baserate-v1` — no LLM in this ledger), for a total of
  405 × 3 = 1215 attempts: **1197 predictions** actually written and
  **18 declines** declared (an engine that explicitly refuses to answer
  when it doesn't have enough history — never a random guess). 1
  `question_set` + 1197 `prediction` + 18 `decline` = **1216 entries**,
  all written on the same day, September 14, 2026 (UTC).
- The questions resolve between **September 26, 2026** and
  **February 28, 2027**, when each company files the quarter in question
  with the SEC. No question in this set resolves before September 26,
  2026 — verified mechanically at generation time, not by eye (see
  `generation_procedure` in the `question_set` entry).
- The 28 companies: AAPL, NVDA, AMD, QCOM, TXN, ORCL, CRM, NFLX, TSLA, HD, MA,
  MCD, SBUX, TGT, WMT, KHC, CL, MO, JNJ, UNH, GILD, ABBV, TMO, DHR, LMT,
  HON, CAT, VZ.

## Files

```
entries.jsonl          # all 1216 ledger entries, one per JSON line, in seq order
anchors_index.jsonl    # human-readable index of the 4 RFC 3161 anchors (see below)
anchors/
  1_freetsa.tsr             2_digicert.tsr             3_freetsa.tsr             4_digicert.tsr
  1_freetsa.head_hash.txt   2_digicert.head_hash.txt   3_freetsa.head_hash.txt   4_digicert.head_hash.txt
  1_freetsa.pem             2_digicert.pem             3_freetsa.pem             4_digicert.pem
verify_entry.py         # recomputes the hash of ONE entry (new script, ~15 lines, standard library only)
verify_chain.py         # re-verifies the entire hash chain from entries.jsonl (same idea)
LICENSE                 # CC BY 4.0 — data only, see the file for the exact scope
```

Why 4 anchors and not 2: anchors 1 (FreeTSA) and 2 (DigiCert) cover only
`seq=1` — the `question_set`, i.e. the 405 questions and their
thresholds, anchored BEFORE any engine saw them (so the thresholds
cannot have been picked with hindsight). Anchors 3 and 4, same two
services, cover `seq=1216` — the entire ledger, predictions and declines
included. See "What this does NOT prove" below for what this actually
implies.

## Verifying an anchor (RFC 3161), a service independent of us

Each line of `anchors_index.jsonl` is an anchor: an external
timestamping authority (FreeTSA.org or DigiCert) signed "this exact hash
existed no later than this moment". `anchors/` already contains, for
each anchor, the three files `openssl ts -verify` requires — nothing
else is needed beyond `openssl` (verified with OpenSSL 3.6.4; any modern
OpenSSL will do).

Exact command, one per anchor — replace `<pair>` with one of the four
prefixes (`1_freetsa`, `2_digicert`, `3_freetsa`, `4_digicert`):

```bash
openssl ts -verify -in anchors/<pair>.tsr \
  -data anchors/<pair>.head_hash.txt \
  -CAfile anchors/<pair>.pem
```

Concrete example, ready to copy and paste as-is (the anchor covering the
ENTIRE ledger, DigiCert service):

```bash
openssl ts -verify -in anchors/4_digicert.tsr \
  -data anchors/4_digicert.head_hash.txt \
  -CAfile anchors/4_digicert.pem
```

Expected output: `Verification: OK`. All 4 anchors in this directory
were verified this way, one by one, on the day this README was
published — none returns anything other than `Verification: OK`.

To verify all four in one shot (no dependency beyond `openssl` — no
`jq`):

```bash
for tsr in anchors/*.tsr; do
  base="${tsr%.tsr}"
  echo "=== $base ==="
  openssl ts -verify -in "${base}.tsr" -data "${base}.head_hash.txt" -CAfile "${base}.pem"
done
```

`Verification: OK` means: this exact `head_hash` was signed by a
certificate that chains up to the CA in that `.pem`, at the time
recorded inside the token — verified by `openssl`, a tool you don't
have to trust us to trust. **On its own it does not yet say that this
`head_hash` actually corresponds to the head of the ledger in
`entries.jsonl`** — that's the next step.

## Recomputing the hash chain by hand, from `entries.jsonl`

Every line of `entries.jsonl` is an entry with these fields: `seq`
(progressive integer, never reordered), `entry_type`, `prev_hash`,
`entry_hash`, `payload` (human-readable) and `payload_raw` (the EXACT
string, byte for byte, used to compute `entry_hash` — never `payload`,
which is only for human reading and can differ in formatting).

The formula, identical for every entry of every type:

```
entry_hash = SHA256( prev_hash + b'\0' + entry_type + b'\0' + payload_raw )
```

— three fields concatenated as UTF-8 bytes, with `\0` **only between**
the three fields, never after the last one. The `prev_hash` of the very
first entry (`seq=1`) is 64 zeros; from there on, the `prev_hash` of
every entry is the `entry_hash` of the entry immediately before it — a
chain verifiable line by line by reading only this file, no database
required.

### Concrete example, on a real line of the file

The line with `seq=245` (a `decline`, not a `prediction`, chosen on
purpose because its `payload_raw` is short enough to read here in full):

```
prev_hash   = 1ae9b0d72bc2e5aae63f3b03c1f619b78693867726c08d1c24bd3c2bbec772b0
entry_type  = decline
payload_raw = {"anchor_period_end":"2026-08-31","cik":"0001341439","created_at":"2026-09-14T14:12:06.403906Z","decline_id":"75350375-afe7-4207-a59f-d33071a43a3e","engine_id":"baseline-persistence-v1","horizon_quarters":1,"metric":"GROSS_MARGIN","operator":"GT","period_form":"QUARTERLY","question_set_id":"a1e58752-b054-40f2-9818-d51d7448624f","reason":"storia insufficiente: servono almeno 8 osservazioni storiche, disponibili 7","threshold":0.8829117727074218,"ticker":"ORCL"}
entry_hash  = d4f171c3728466501939f661132805712892117587d19bc089f231854423140b   (declared in the file)
```

The `payload_raw` above is left exactly as it appears in the file, in
Italian (the ledger's original working language), so you can compare it
character for character against the real line in `entries.jsonl`. Its
`reason` field, `"storia insufficiente: servono almeno 8 osservazioni
storiche, disponibili 7"`, translates as: "insufficient history: at
least 8 historical observations required, 7 available".

Recomputing by hand, with plain `python3` (required for a byte-exact
concatenation with `\0` separators — `printf`/`echo` alone are not
reliable across every shell for this):

```bash
python3 -c "
import hashlib, sys
prev_hash, entry_type, payload_raw = sys.argv[1], sys.argv[2], sys.argv[3]
h = hashlib.sha256()
h.update(prev_hash.encode('utf-8')); h.update(b'\0')
h.update(entry_type.encode('utf-8')); h.update(b'\0')
h.update(payload_raw.encode('utf-8'))
print(h.hexdigest())
" \
  "1ae9b0d72bc2e5aae63f3b03c1f619b78693867726c08d1c24bd3c2bbec772b0" \
  "decline" \
  '{"anchor_period_end":"2026-08-31","cik":"0001341439","created_at":"2026-09-14T14:12:06.403906Z","decline_id":"75350375-afe7-4207-a59f-d33071a43a3e","engine_id":"baseline-persistence-v1","horizon_quarters":1,"metric":"GROSS_MARGIN","operator":"GT","period_form":"QUARTERLY","question_set_id":"a1e58752-b054-40f2-9818-d51d7448624f","reason":"storia insufficiente: servono almeno 8 osservazioni storiche, disponibili 7","threshold":0.8829117727074218,"ticker":"ORCL"}'
```

Output: `d4f171c3728466501939f661132805712892117587d19bc089f231854423140b`
— identical to the value declared above. Run exactly as written above,
right before this README was delivered.

### Doing this for any line, without hand-copying a huge string

`prediction` entries have a `payload_raw` much longer than the `decline`
above — copying it by hand into a command line is doable but fragile
(lose one character and the comparison fails without telling you why).
`verify_entry.py`, in this same directory, does exactly the same
computation by reading the line directly from `entries.jsonl` instead of
requiring you to retype it:

```bash
python3 verify_entry.py 245 entries.jsonl   # the same example as above
python3 verify_entry.py 2 entries.jsonl     # any real prediction
```

To re-verify the ENTIRE chain, all 1216 entries, in one shot —
`verify_chain.py`, also in this directory, ~30 lines, standard library
only:

```bash
python3 verify_chain.py entries.jsonl
```

Expected output: `Chain intact: 1216 entries verified, from the first
(prev_hash=64 zeros) to seq=1216.` followed by the final `head_hash`. To
tie this result to a concrete RFC 3161 anchor (closing the loop with the
previous section), pass as a second argument the `head_hash` read from
one of the `anchors/*.head_hash.txt` files (or from the `head_hash`
field of `anchors_index.jsonl`):

```bash
python3 verify_chain.py entries.jsonl "$(cat anchors/4_digicert.head_hash.txt)"
```

Expected output: in addition to the line above, `MATCH with expected
head_hash (...)`. Run exactly as written: the chain recomputed from
`entries.jsonl` alone lands exactly on the head_hash that anchor 4 had
DigiCert sign — the two verifications together (this one + `openssl ts
-verify` above) are what proves that the 1216 entries existed, unchanged,
no later than the moment signed by that anchor.

## Field schema of an entry

Every line of `entries.jsonl`:

| field | meaning |
|---|---|
| `seq` | progressive position in the chain, starting at 1, never reordered |
| `entry_type` | `question_set`, `prediction`, or `decline` (no `resolution` yet: questions resolve starting late September 2026) |
| `prev_hash` | `entry_hash` of the preceding entry (64 zeros for `seq=1`) |
| `entry_hash` | SHA-256 of `prev_hash` + `entry_type` + `payload_raw`, see above |
| `payload` | the entry's content, reformatted for human reading |
| `payload_raw` | the exact string used to compute `entry_hash` — use this, not `payload`, to re-verify |

Inside `payload`, by type:

- **`question_set`** (a single entry, `seq=1`): `question_set_id`,
  `generator_id`, `generation_procedure` (the method used to generate the
  405 questions, in prose — not cryptographically verifiable, only its
  EXISTENCE at this date is), and `questions[]`, the list of the 405
  questions: `ticker`/`cik` (the company), `metric` (`REVENUE`,
  `GROSS_MARGIN` or `OPERATING_MARGIN`), `period_form` (always
  `QUARTERLY` here), `anchor_period_end` (the last quarter already
  filed, the starting point), `horizon_quarters` (1 or 2 quarters
  ahead), `operator` (always `GT`, "greater than") and `threshold` (the
  numeric threshold).
- **`prediction`**: `prediction_id`, `question_set_id` (which question
  it answers), `engine_id` (which of the 3 baseline engines), the same
  identifying fields as the question (`ticker`, `metric`, `threshold`,
  ...), `probability` (the actual prediction, 0–1), `rationale` (a
  textual explanation of the computation, in prose), `resolution_deadline`
  (the date by which it resolves), `status` (`PENDING` for all of them
  here — none resolved yet), and the `resolved_at`/`resolved_value`/
  `resolution_note` fields, all `null` while `status` stays `PENDING`.
- **`decline`**: like `prediction` but without `probability`/`rationale`
  — in their place, `reason`: why that engine explicitly refused to
  answer that question (typically insufficient history).

## What this ledger proves — and what it does NOT prove

**It proves**: that these 405 questions, their thresholds, and the 1197
predictions (with their respective probabilities) **existed, textually
identical to how you read them here, no later than the dates signed by
the four anchors** — September 14, 2026, 14:12 UTC for the
questions/thresholds (anchors 1–2, before any engine saw them) and the
same day, 21:07 UTC, for the entire ledger including all predictions
(anchors 3–4). This is not a claim we're making: it is what `openssl ts
-verify` — an independent tool, one that doesn't require trusting this
code — confirms above, combined with the hash chain recomputed by hand
from this same file. No line could have been altered after that date
without breaking the chain at a point detectable by anyone, with the
same two commands.

**It does NOT prove**:

- **That an engine running on infrastructure we don't control used only
  the declared inputs.** `rationale` and `generation_procedure` are
  text: the anchor certifies that this text existed, not that it
  honestly describes how the prediction was actually computed, nor that
  the process that produced it had no access to information other than
  what was declared. This ledger proves the existence and integrity of a
  claim, not the faithfulness of the process that generated it.
- **That the predictions are correct, well calibrated, or useful.** Only
  that they existed, unchanged, at that date — their quality is judged
  when they resolve (from late September 2026 onward), not here.
- **That the code published elsewhere corresponds exactly to the code
  that actually generated these predictions** — this directory contains
  no source code (see below).
- **That this is the only ledger with these questions**, nor that no
  other prediction on the same question was ever written elsewhere: that
  constraint (never the same question twice to the same engine) lives in
  the code, and is not verifiable from these files alone.
- **An exact time**, only an upper bound: an RFC 3161 anchor proves "no
  later than" the signed time, never "exactly at that moment".
- **Anything about what happens after `covered_seq`**: an anchor covers
  the chain only up to the entry it covered when it was requested. If
  this ledger is extended in the future with new predictions, those new
  entries remain without this guarantee until they too are anchored by a
  subsequent anchor (ideally included in the same export that publishes
  them).
- **The resolutions**: no question here is resolved yet (all `PENDING`);
  the accuracy of the three engines can only be judged once the actual
  resolutions arrive, in a future update to this ledger — not covered by
  this export.

## Source code

This directory deliberately contains **only data and verification tools
independent of the code that produced them** — no module of the project
that generates questions, runs the prediction engines, or produces this
very export.

Source code available on request — open an issue on this repository.

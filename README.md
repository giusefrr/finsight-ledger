# Registro pubblico FinSight — QuestionSet live del 14 settembre 2026

Questa directory contiene **solo dati e strumenti di verifica**, non il
codice che li ha prodotti. Ogni comando qui sotto è stato eseguito
davvero, dentro questa stessa directory, senza importare nulla del
progetto FinSight: se lo lanci tu ora, sulla tua macchina, con solo
`python3` (libreria standard) e `openssl`, deve produrre lo stesso
risultato. Se un comando non funziona così com'è scritto, è un bug di
questo README, non qualcosa da aggiustare a occhio.

## Cosa c'è in questo registro

- **405 domande** ("questo trimestre, il ricavo/margine di [azienda] sarà
  sopra/sotto [soglia]?"), su **28 emittenti quotati** (elenco completo più
  sotto), sigillate in un unico `question_set` il **14 settembre 2026**.
- Ogni domanda è stata sottoposta a **3 motori baseline meccanici**
  (`baseline-persistence-v1`, `baseline-persistence-v2`,
  `baseline-baserate-v1` — nessun LLM in questo registro), per un totale di
  405 × 3 = 1215 tentativi: **1197 previsioni** effettivamente scritte e
  **18 declini** dichiarati (un motore che rifiuta esplicitamente di
  rispondere quando non ha abbastanza storico — mai una previsione a
  caso). 1 `question_set` + 1197 `prediction` + 18 `decline` = **1216
  entry**, tutte scritte lo stesso giorno, 14 settembre 2026 (UTC).
- Le domande si risolvono tra il **26 settembre 2026** e il **28 febbraio
  2027**, quando ciascuna azienda deposita il trimestre in questione presso
  la SEC. Nessuna domanda di questo set si risolve prima del 26 settembre
  2026 — verificato meccanicamente al momento della generazione, non a
  occhio (vedi `generation_procedure` nella entry `question_set`).
- Le 28 aziende: AAPL, NVDA, AMD, QCOM, TXN, ORCL, CRM, NFLX, TSLA, HD, MA,
  MCD, SBUX, TGT, WMT, KHC, CL, MO, JNJ, UNH, GILD, ABBV, TMO, DHR, LMT,
  HON, CAT, VZ.

## File

```
entries.jsonl          # tutte le 1216 entry del registro, una per riga JSON, in ordine di seq
anchors_index.jsonl    # indice leggibile dei 4 anchor RFC 3161 (vedi sotto)
anchors/
  1_freetsa.tsr             2_digicert.tsr             3_freetsa.tsr             4_digicert.tsr
  1_freetsa.head_hash.txt   2_digicert.head_hash.txt   3_freetsa.head_hash.txt   4_digicert.head_hash.txt
  1_freetsa.pem             2_digicert.pem             3_freetsa.pem             4_digicert.pem
verify_entry.py         # ricalcola l'hash di UNA entry (nuovo script, ~15 righe, solo libreria standard)
verify_chain.py         # riverifica l'intera hash chain da entries.jsonl (idem)
LICENSE                 # CC BY 4.0 — solo per i dati, vedi il file per lo scope esatto
```

Perché 4 anchor e non 2: gli anchor 1 (FreeTSA) e 2 (DigiCert) coprono solo
`seq=1` — il `question_set`, cioè le 405 domande e le loro soglie, ancorate
PRIMA che un motore le vedesse (così le soglie non possono essere state
scelte con il senno di poi). Gli anchor 3 e 4, stessi due servizi, coprono
`seq=1216` — l'intero registro, previsioni e declini inclusi. Vedi
"Cosa NON dimostra" più sotto per cosa questo implica davvero.

## Verificare un anchor (RFC 3161), un servizio indipendente da noi

Ogni riga di `anchors_index.jsonl` è un anchor: un'autorità di timestamping
esterna (FreeTSA.org o DigiCert) ha firmato "questo esatto hash esisteva non
più tardi di questo momento". `anchors/` contiene già, per ciascun anchor,
i tre file che `openssl ts -verify` richiede — non serve altro che
`openssl` (verificato con OpenSSL 3.6.4; qualunque OpenSSL moderno va bene).

Comando esatto, uno per anchor — sostituisci `<coppia>` con uno dei quattro
prefissi (`1_freetsa`, `2_digicert`, `3_freetsa`, `4_digicert`):

```bash
openssl ts -verify -in anchors/<coppia>.tsr \
  -data anchors/<coppia>.head_hash.txt \
  -CAfile anchors/<coppia>.pem
```

Esempio concreto, copiabile e incollabile così com'è (l'anchor che copre
l'INTERO registro, servizio DigiCert):

```bash
openssl ts -verify -in anchors/4_digicert.tsr \
  -data anchors/4_digicert.head_hash.txt \
  -CAfile anchors/4_digicert.pem
```

Output atteso: `Verification: OK`. Tutti e 4 gli anchor di questa directory
sono stati verificati così, uno per uno, il giorno di pubblicazione di
questo README — nessuno restituisce altro che `Verification: OK`.

Per verificarli tutti e quattro in un colpo solo (nessuna dipendenza oltre
`openssl` — niente `jq`):

```bash
for tsr in anchors/*.tsr; do
  base="${tsr%.tsr}"
  echo "=== $base ==="
  openssl ts -verify -in "${base}.tsr" -data "${base}.head_hash.txt" -CAfile "${base}.pem"
done
```

`Verification: OK` significa: questo esatto `head_hash` è stato firmato da
un certificato che risale alla CA in quel `.pem`, al tempo registrato dentro
il token — verificato da `openssl`, uno strumento che non devi fidarti di
noi per fidarti. **Da solo non dice ancora che quell'`head_hash` corrisponda
davvero alla testa del registro in `entries.jsonl`** — quello è il prossimo
passo.

## Ricalcolare la hash chain a mano, da `entries.jsonl`

Ogni riga di `entries.jsonl` è una entry con questi campi: `seq` (intero
progressivo, mai riordinato), `entry_type`, `prev_hash`, `entry_hash`,
`payload` (leggibile) e `payload_raw` (la stringa ESATTA, byte per byte,
usata per calcolare `entry_hash` — mai `payload`, che è solo per la
lettura umana e può differire nella formattazione).

La formula, identica per ogni entry di ogni tipo:

```
entry_hash = SHA256( prev_hash + b'\0' + entry_type + b'\0' + payload_raw )
```

— tre campi concatenati come byte UTF-8, con `\0` **solo tra** i tre campi,
mai dopo l'ultimo. Il `prev_hash` della primissima entry (`seq=1`) è 64
zeri; da lì in poi il `prev_hash` di ogni entry è l'`entry_hash` di quella
immediatamente precedente — una catena verificabile riga per riga leggendo
solo questo file, nessun database necessario.

### Esempio concreto, su una riga reale del file

La riga con `seq=245` (un `decline`, non una `prediction`, scelta apposta
perché il suo `payload_raw` è abbastanza corto da leggere qui per intero):

```
prev_hash   = 1ae9b0d72bc2e5aae63f3b03c1f619b78693867726c08d1c24bd3c2bbec772b0
entry_type  = decline
payload_raw = {"anchor_period_end":"2026-08-31","cik":"0001341439","created_at":"2026-09-14T14:12:06.403906Z","decline_id":"75350375-afe7-4207-a59f-d33071a43a3e","engine_id":"baseline-persistence-v1","horizon_quarters":1,"metric":"GROSS_MARGIN","operator":"GT","period_form":"QUARTERLY","question_set_id":"a1e58752-b054-40f2-9818-d51d7448624f","reason":"storia insufficiente: servono almeno 8 osservazioni storiche, disponibili 7","threshold":0.8829117727074218,"ticker":"ORCL"}
entry_hash  = d4f171c3728466501939f661132805712892117587d19bc089f231854423140b   (dichiarato nel file)
```

Ricalcolo a mano, con `python3` puro (richiesto per una concatenazione
byte-esatta con separatori `\0` — `printf`/`echo` da soli non sono
affidabili su ogni shell per questo):

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

Output: `d4f171c3728466501939f661132805712892117587d19bc089f231854423140b` —
identico al valore dichiarato sopra. Eseguito così com'è scritto, appena
prima di consegnare questo README.

### Farlo per qualunque riga, senza copiare a mano una stringa enorme

Le `prediction` hanno un `payload_raw` molto più lungo del `decline` sopra
— copiarlo a mano in una riga di comando è pratico ma fragile (un carattere
perso e il confronto fallisce senza dirti perché). `verify_entry.py`, in
questa stessa directory, fa esattamente lo stesso calcolo leggendo la riga
direttamente da `entries.jsonl` invece di richiedere di ritrascriverla:

```bash
python3 verify_entry.py 245 entries.jsonl   # lo stesso esempio di sopra
python3 verify_entry.py 2 entries.jsonl     # una prediction reale, a scelta
```

Per riverificare l'INTERA catena, tutte le 1216 entry, in un colpo solo —
`verify_chain.py`, anch'esso in questa directory, ~30 righe, solo libreria
standard:

```bash
python3 verify_chain.py entries.jsonl
```

Output atteso: `Catena intatta: 1216 entry verificate, dalla prima
(prev_hash=64 zeri) a seq=1216.` seguito dall'`head_hash` finale. Per
legare questo risultato a un anchor RFC 3161 concreto (chiudendo il cerchio
con la sezione precedente), passa come secondo argomento l'`head_hash` letto
da uno dei file `anchors/*.head_hash.txt` (o dal campo `head_hash` di
`anchors_index.jsonl`):

```bash
python3 verify_chain.py entries.jsonl "$(cat anchors/4_digicert.head_hash.txt)"
```

Output atteso: oltre alla riga di sopra, `MATCH con l'head_hash atteso
(...)`. Eseguito così com'è scritto: la catena ricalcolata da
`entries.jsonl` da sola arriva esattamente all'`head_hash` che l'anchor 4
ha fatto firmare a DigiCert — le due verifiche insieme (questa + `openssl
ts -verify` sopra) sono ciò che dimostra che le 1216 entry esistevano,
invariate, non oltre il momento firmato da quell'anchor.

## Schema dei campi di una entry

Ogni riga di `entries.jsonl`:

| campo | significato |
|---|---|
| `seq` | posizione progressiva nella catena, a partire da 1, mai riordinata |
| `entry_type` | `question_set`, `prediction`, o `decline` (nessuna `resolution` ancora: le domande si risolvono da fine settembre 2026 in poi) |
| `prev_hash` | `entry_hash` della entry precedente (64 zeri per `seq=1`) |
| `entry_hash` | SHA-256 di `prev_hash` + `entry_type` + `payload_raw`, vedi sopra |
| `payload` | il contenuto della entry, riformattato per la lettura umana |
| `payload_raw` | la stringa esatta usata per calcolare `entry_hash` — usa questa, non `payload`, per riverificare |

Dentro `payload`, per tipo:

- **`question_set`** (una sola entry, `seq=1`): `question_set_id`,
  `generator_id`, `generation_procedure` (il metodo con cui le 405 domande
  sono state generate, in prosa — non verificabile crittograficamente, solo
  la sua ESISTENZA a questa data lo è), e `questions[]`, la lista delle 405
  domande: `ticker`/`cik` (l'azienda), `metric` (`REVENUE`, `GROSS_MARGIN`
  o `OPERATING_MARGIN`), `period_form` (sempre `QUARTERLY` qui),
  `anchor_period_end` (l'ultimo trimestre già depositato, punto di
  partenza), `horizon_quarters` (1 o 2 trimestri più avanti), `operator`
  (sempre `GT`, "maggiore di") e `threshold` (la soglia numerica).
- **`prediction`**: `prediction_id`, `question_set_id` (a quale domanda
  risponde), `engine_id` (quale dei 3 motori baseline), gli stessi campi
  identificativi della domanda (`ticker`, `metric`, `threshold`, ...),
  `probability` (la previsione vera e propria, 0–1), `rationale` (una
  spiegazione testuale del calcolo, in prosa), `resolution_deadline` (la
  data entro cui si risolve), `status` (`PENDING` per tutte, qui — nessuna
  ancora risolta), e i campi `resolved_at`/`resolved_value`/
  `resolution_note`, tutti `null` finché `status` resta `PENDING`.
- **`decline`**: come `prediction` ma senza `probability`/`rationale` — al
  loro posto, `reason`: perché quel motore ha rifiutato esplicitamente di
  rispondere a quella domanda (tipicamente storico insufficiente).

## Cosa questo registro dimostra — e cosa NON dimostra

**Dimostra**: che queste 405 domande, le loro soglie, e le 1197 previsioni
(con le rispettive probabilità) **esistevano, testualmente identiche a come
le leggi qui, non più tardi delle date firmate dai quattro anchor** — il
14 settembre 2026, 14:12 UTC per le domande/soglie (anchor 1–2, prima che
qualunque motore le vedesse) e lo stesso giorno, 21:07 UTC, per l'intero
registro incluse tutte le previsioni (anchor 3–4). Non è una nostra
affermazione: è quello che `openssl ts -verify` — uno strumento
indipendente, che non richiede di fidarsi di questo codice — conferma
sopra, combinato con la hash chain ricalcolata a mano da questo stesso
file. Nessuna riga può essere stata alterata dopo quella data senza
rompere la catena in un punto rilevabile da chiunque, con gli stessi due
comandi.

**NON dimostra**:

- **Che un motore su infrastruttura che non controlliamo abbia usato solo
  gli input dichiarati.** `rationale` e `generation_procedure` sono testo:
  l'anchor certifica che quel testo esisteva, non che descriva onestamente
  come la previsione sia stata davvero calcolata, né che il processo che
  l'ha prodotta non avesse accesso a informazioni diverse da quelle
  dichiarate. Questo registro prova l'esistenza e l'integrità di
  un'affermazione, non la fedeltà del processo che l'ha generata.
- **Che le previsioni siano corrette, ben calibrate o utili.** Solo che
  esistevano, invariate, a quella data — la loro qualità si giudica quando
  si risolvono (da fine settembre 2026), non qui.
- **Che il codice pubblicato altrove corrisponda esattamente al codice che
  ha davvero generato queste previsioni** — questa directory non contiene
  codice sorgente (vedi sotto).
- **Che questo sia l'unico registro esistente con queste domande**, né
  che nessun'altra previsione sulla stessa domanda sia mai stata scritta
  altrove: quel vincolo (mai la stessa domanda due volte allo stesso
  motore) vive nel codice, non è verificabile da questi soli file.
- **Un'ora esatta**, solo un limite superiore: un anchor RFC 3161 prova
  "non più tardi di" il tempo firmato, mai "esattamente in quel momento".
- **Nulla su ciò che accade dopo `covered_seq`**: un anchor copre la catena
  solo fino alla entry che copriva quando è stato richiesto. Se in futuro
  questo registro viene esteso con nuove previsioni, quelle nuove entry
  restano prive di questa garanzia finché non vengono ancorate a loro
  volta con un anchor successivo (idealmente incluso nello stesso export
  che le pubblica).
- **Le risoluzioni**: nessuna domanda qui è ancora risolta (tutte
  `PENDING`); l'accuratezza dei tre motori si potrà giudicare solo quando
  arriveranno le risoluzioni reali, in un futuro aggiornamento di questo
  registro — non coperte da questo export.

## Codice sorgente

Questa directory contiene deliberatamente **solo dati e strumenti di
verifica indipendenti dal codice che li ha prodotti** — nessun modulo del
progetto che genera domande, esegue i motori di previsione o produce
questo stesso export.

Source code available on request — open an issue on this repository.

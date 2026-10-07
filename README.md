# Standort-Agent: AI:AT Challenge

Schön, dass du dabei bist. Dieses Repo enthält alles, was du zum Loslegen brauchst: Aufgabenstellung, Daten und (für die Dev-Rolle) das Code-Snippet.

> Das hier ist kein Trick-Test. Es ist ein kleines, echtes Stück Venture-Studio-Arbeit: mit KI schnell etwas Wertvolles bauen bzw. eine Idee auf Marktreife prüfen. Es gibt keine Musterlösung, die du treffen musst. Wir schauen, wie du ein unscharf spezifiziertes Problem zerlegst, Entscheidungen triffst und KI sinnvoll einsetzt.

## Das Szenario: „Standort-Agent"

Eine Standortentscheidung ist für ein expandierendes österreichisches Unternehmen (Filialist, Händler, Logistiker, Gastro-Kette) ein **€500K+-Commitment**, und wird heute oft aus dem Bauch oder über teure Beratung getroffen. „Standort-Agent" ist ein KI-System, das ein Business-Profil nimmt und in Sekunden zeigt, welche österreichischen Gemeinden/Bezirke am besten passen und warum, bewertet über mehrere Signale (Demografie, POI-/Umfeld-Dichte, Mietkosten, ÖV-Anbindung).

## Wähle deine Challenge

| Rolle | Worum geht's | Start hier |
|---|---|---|
| **AI Developer** | Bau den Standort-Agent-PoC (Python Multi-Agent) + ein kurzes Code-Review | [`dev/`](./dev/) |
| **AI Business Analyst & Venture Builder** | Ist das ein Geschäft? Business Case + Go-to-Market | [`business/`](./business/) |

> Du weißt aus dem Gespräch mit uns, welche Rolle deine ist, leg einfach im passenden Ordner los. Falls unklar, frag kurz per Mail nach. (Neugierig auf die andere Seite? Gern reinschauen, für deine Abgabe zählt nur dein Ordner.)

## Die Daten (`data/`)

Beide Rollen teilen sich dieselbe Datengrundlage:

- [`data/municipalities.json`](./data/municipalities.json): 20 Gemeinden/Bezirke aus allen 9 Bundesländern (Felder dokumentiert in [`data/README.md`](./data/README.md))
- [`data/municipalities.csv`](./data/municipalities.csv): dieselben Daten, bequem in Excel/Sheets zu öffnen
- [`data/examples/`](./data/examples/): 2–3 Beispiel-Profile als Ausgangspunkt

> ⚠️ Synthetisch / vereinfacht, Stand 2026-06, keine offizielle AI:AT-Position. Kein Domänenwissen nötig, die Gemeinde-Daten sind selbsterklärend. *(Business-Rolle: die Markt-/Preis-Zahlen fürs Sizing stecken nicht in den Daten, die recherchierst du frei, siehe deinen Brief.)*

## Das Wichtigste in Kürze

- **Aufwand:** ~4–6 fokussierte Stunden. Du hast 7 Kalendertage ab Erhalt; das Fenster ist für Flexibilität da, nicht zum Durchgrinden.
- **KI:** Nutze jede KI, jede Library, google frei. Das wird erwartet, nicht nur erlaubt.
- **Abgabe:** per E-Mail an aiandbusinessgrowth@ai-at.eu. Für deinen Code/deine Doku erstellst du ein eigenes Repo (z. B. `git init` in deinem Arbeitsordner oder dieses Repo als Vorlage klonen und zu deinem GitHub/GitLab pushen) und schickst uns den Link. Die konkreten Daten (Abgabedatum, ggf. Upload-Link) stehen in deiner Begleit-E-Mail.
- **Bewertung:** transparent, die Gewichtung findest du in deinem Rollen-Brief.
- **Wichtig:** Ein rauer Kern mit klarem Denken schlägt eine polierte, oberflächliche Umsetzung. Mehr Stunden bedeuten bei uns nicht mehr Punkte.

## Fair & transparent

AI Factory Austria steht für Chancengleichheit. Ob Uni, Bootcamp oder self-taught: es zählt, wie du denkst und mit KI arbeitest. Brauchst du Unterstützung oder Anpassungen im Prozess, sag uns Bescheid. Die Challenge ist unbezahlt. Dafür zeigen wir dir nach dem Debrief unsere eigene Lösung (mit echten Entscheidungen, Prompts und Trade-offs) und geben strukturiertes, ehrliches Feedback an jede:n. Kein Ghosting, nie.

> Was du hier nicht findest, ist unsere eigene Referenzlösung. Die heben wir bewusst für den gemeinsamen Debrief auf, damit du frei und ohne Anchoring an die Aufgabe gehst.

*AI:AT Hiring Team*

## Groq LLM specialists

The LangGraph workflow computes numerical scores in Python, then uses four
Groq-backed specialist roles (demographics, surroundings, affordability and
transport) to interpret the top five results. A fifth call synthesizes the
customer recommendation. The LLM cannot change scores or reorder rankings.
Structured JSON responses are validated before any explanation is applied.
Model text still needs factual review; schema validation alone does not prove
that every interpretation is correct.

Install the updated dependencies:

```bash
uv pip install -e '.[dev]'
```

Create a replacement key in the Groq console. Copy `.env.example` to `.env`
in the project root and replace the placeholder locally:

```dotenv
GROQ_API_KEY=your-new-key
GROQ_MODEL=openai/gpt-oss-20b
STANDORT_LLM_MODE=groq
```

The app automatically reads this file regardless of the working directory.
Explicit shell environment variables take precedence. `.env` is ignored by Git;
never commit API keys. Restart the app after changing settings.

```bash
PYTHONPATH="$PWD/src" python -m standort_agent.ui.app
```

The default model is listed in Groq's free-plan limits:
https://console.groq.com/docs/rate-limits . Account access and limits can change.
Each analysis makes five sequential API calls; repeated analyses may hit the
free-plan request or token limits. There are no automatic retries.

`groq` mode shows an error if the API cannot complete the analysis. `auto`
(the default) uses clearly labelled rule-based explanations if no key is set
or Groq fails. `offline` makes no API calls and satisfies the challenge's
requirement for a run without credentials. The UI and downloaded report show
which mode actually produced the explanations. Inputs and shortlisted data
are sent to Groq in live mode. No key is stored in source code or reports.

Run tests without network calls:

```bash
STANDORT_LLM_MODE=offline pytest -q
```

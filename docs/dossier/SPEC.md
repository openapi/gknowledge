# The Dossier format

**Version 0.1, draft, 27 October 2026.** Maintained in [openapi/gknowledge](https://github.com/openapi/gknowledge). Comments and implementations from other projects are welcome; open an issue.

A **dossier** is a folder of evidence together with the knowledge compiled from it. Every compiled statement says which evidence it comes from, and anyone can check whether that evidence is still current. This document defines the model, the on-disk layout and the rules that let any program (a desktop app, an editor plugin, a command-line tool, an AI agent) read, compile and audit the same dossier without depending on the software that created it.

gknowledge is the reference implementation. The format belongs to no single program: nothing in it requires gknowledge, and the names in it are not gknowledge's names.

## 1. Why a folder

The folder is the unit of work people already use. A case, a client, a project, a thesis, a house purchase: on every computer, each one already lives in a folder. What the folder has never had is meaning. It holds files, but it cannot say what it knows, where that knowledge came from, or whether it still holds.

The spreadsheet did not invent its object: accountants already worked on paper spreadsheets, and VisiCalc made that paper compute. The dossier follows the same path. People already *compile a dossier* when they gather documents on a subject so that they, or someone else, can decide. This format makes the folder do the compiling, keep the citations and notice when a source has moved on.

Three properties follow, and the rest of the document makes them precise:

1. **The folder is the truth.** Everything that matters is plain files inside the folder. Databases, search indexes and caches are derived from those files and can always be rebuilt.
2. **Every compiled statement has provenance.** A page lists the sources it was compiled from, and each source is identified by the hash of its content.
3. **The dossier travels.** It can be copied, zipped, put under version control, opened in a Markdown editor or handed to an agent, and it keeps working. It contains no secrets and no paths that only make sense on one machine, except where this document marks them as optional and local.

## 2. Conventions

The key words MUST, MUST NOT, SHOULD, SHOULD NOT and MAY are to be read as described in [RFC 2119](https://www.rfc-editor.org/rfc/rfc2119) and [RFC 8174](https://www.rfc-editor.org/rfc/rfc8174) when, and only when, they appear in capitals.

- All text files are UTF-8, with LF line endings.
- Paths inside records are relative to the dossier root and use `/` as separator.
- Timestamps are [RFC 3339](https://www.rfc-editor.org/rfc/rfc3339) strings in UTC (`2026-10-27T18:10:12Z`).
- Hashes are lowercase hexadecimal SHA-256 of the exact bytes of a file.
- Identifiers are opaque strings, unique within the dossier. A random UUID in lowercase hex without dashes is RECOMMENDED.
- JSON Schemas for every record are in [`schema/`](schema/) and are normative.

## 3. The model

The format has a small vocabulary. Implementations SHOULD use these names in their user interfaces, APIs and code, so that a user moving between programs meets the same concepts.

| Term | Definition |
|---|---|
| **Dossier** | The folder, identified by its manifest. It has an id, a name and a format version. |
| **Source** | One piece of evidence: a file copied into the dossier and never modified afterwards. Its identity is the hash of its bytes. |
| **Ledger** | The list of all sources with their hashes and, optionally, where they came from. |
| **Page** | One unit of compiled knowledge: a Markdown file with a header that states its kind, its sources and its links. |
| **Kind** | What a page is about: `source`, `entity`, `concept`, `topic`, `synthesis` or `answer` (§5.3). |
| **Provenance** | The list of sources a page was compiled from. A page with no provenance is not compiled knowledge; it is a note. |
| **Link** | A reference from one page to another, written as `[[slug]]` in the body and listed in the header. |
| **Citation** | A reference from a statement, typically in an answer, to the page or source that supports it. |
| **Note** | Text written by a person. Compilers read notes and never overwrite them. |
| **Index** | `knowledge/index.md`: the catalogue of pages, the entry point for people and agents. |
| **Log** | `knowledge/log.md`: the append-only record of what was done to the dossier, and when. |
| **Drift** | The state of a source whose original has changed since it was copied into the dossier. Pages that cite it are **stale**. |
| **Compiler** | A program that turns sources into pages. Any program can be one: an LLM pipeline, a heuristic engine, a person with an editor. |

The relationships:

```
Dossier ─┬─ Ledger ── Source ◄────────┐ provenance (by source id)
         │                            │
         ├─ knowledge/ ── Page ───────┘
         │                 │  ▲
         │                 └──┘ links (by slug)
         ├─ notes/ ── Note         (human, never overwritten)
         ├─ index.md, log.md       (navigation and history)
         └─ .dossier/              (derived state, rebuildable)
```

### 3.1 The three operations

A dossier supports three operations. They correspond to the *ingest*, *query* and *lint* operations of the LLM-wiki pattern described by Andrej Karpathy ([gist](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f)); the format gives them names that fit the object.

| Operation | LLM-wiki name | What it does | Writes |
|---|---|---|---|
| **Compile** | ingest | Adds a source to the ledger and turns it into pages, or updates existing pages with it. | `sources/`, ledger, `knowledge/`, index, log |
| **Consult** | query | Answers a question from the pages, with citations. An answer MAY be saved as a page of kind `answer`. | nothing, or one `answer` page and a log line |
| **Audit** | lint | Checks that the knowledge still matches its evidence: drift, missing sources, broken links, orphan pages. | nothing, or a report; never pages |

## 4. Layout

```
<dossier>/
├── dossier.json             # manifest (REQUIRED)
├── sources.jsonl            # ledger (REQUIRED once a source exists)
├── sources/                 # source files, immutable (REQUIRED)
├── knowledge/               # compiled pages (REQUIRED)
│   ├── index.md             # catalogue (REQUIRED)
│   ├── log.md               # operation log (REQUIRED)
│   ├── overview.md          # global summary (OPTIONAL)
│   └── sources/ entities/ concepts/ topics/ synthesis/ answers/
├── notes/                   # human-written notes (OPTIONAL)
├── .dossier/                # derived and local state (OPTIONAL, never shared)
└── .gitignore               # SHOULD exclude .dossier/
```

- A folder is a dossier if and only if it contains a valid `dossier.json`.
- Implementations MUST ignore files and folders they do not know, and MUST NOT delete them.
- Pages MAY be placed in the subfolders above, which are RECOMMENDED for interoperability, or anywhere under `knowledge/`. The kind of a page is stated in its header, not inferred from its folder.
- `.dossier/` holds everything that can be rebuilt (search indexes, databases, parse caches, job queues) and everything that belongs to one machine. A dossier copied without `.dossier/` MUST lose nothing but speed.

## 5. Records

### 5.1 Manifest: `dossier.json`

```json
{
  "dossier": "0.1",
  "id": "4a0931f7c2a446d18634254e20825a01",
  "name": "Lease of the Via Roma warehouse",
  "created": "2026-10-27T09:26:17Z",
  "language": "it"
}
```

| Field | Required | Meaning |
|---|---|---|
| `dossier` | yes | Version of this format the dossier follows (§10). |
| `id` | yes | Stable identifier of the dossier. It does not change when the folder is renamed or copied. |
| `name` | yes | Human name. Defaults to the folder name at creation. |
| `created` | yes | Creation time. |
| `language` | no | [BCP 47](https://www.rfc-editor.org/info/bcp47) tag for the language compilers SHOULD write pages in. |
| `description` | no | One paragraph on what the dossier is for. Compilers and agents SHOULD read it as context. |

### 5.2 Ledger: `sources.jsonl`

One JSON object per line, one line per source. The format is line-based so that version control can merge it.

```json
{"id":"82aa5b465ca44e458f36e82d1947ec35","path":"sources/energy-storage.pdf","sha256":"9f2c…","size":48211,"media_type":"application/pdf","title":"Energy Storage","added":"2026-10-13T09:26:17Z","origin":"file:///home/ana/Documents/energy-storage.pdf"}
```

| Field | Required | Meaning |
|---|---|---|
| `id` | yes | Identifier used in page provenance. |
| `path` | yes | Location of the copy, under `sources/`. |
| `sha256` | yes | Hash of the copy. This is the identity of the evidence. |
| `size` | yes | Size in bytes. |
| `media_type` | yes | [IANA media type](https://www.iana.org/assignments/media-types/). |
| `title` | no | Human title. |
| `added` | yes | When the source entered the dossier. |
| `origin` | no | URI of the original (`file:`, `https:`). Used only to detect drift (§6). It is a hint: on another machine it may not resolve, and that is not an error. |

Rules:

- A file in `sources/` MUST NOT be modified after it has been added. A new version of a document is a new source, with a new id and a new hash; the old one MAY then be removed (§6.2).
- The `sha256` in the ledger MUST match the bytes of the file at `path`. A mismatch means the dossier is damaged, and implementations MUST report it.
- Processing state (queued, parsed, failed) is not part of the ledger. It is local and belongs in `.dossier/`. Whether a source has been compiled can be read from the pages: it has been if a page of kind `source` cites it.

### 5.3 Pages

A page is a Markdown file ([CommonMark](https://commonmark.org/)) with a YAML header. The header is the page record.

```markdown
---
id: 964a152f7a2f40ce9491eebda9c50933
kind: source
title: Energy Storage
slug: energy-storage
sources: [82aa5b465ca44e458f36e82d1947ec35]
links: [battery, lithium, tesla]
generated: true
created: 2026-10-13T09:26:17Z
updated: 2026-10-13T09:26:17Z
---
# Energy Storage

Grid-scale storage balances intermittent generation [[battery]] …
```

| Field | Required | Meaning |
|---|---|---|
| `id` | yes | Stable identifier of the page. |
| `kind` | yes | One of the kinds below. |
| `title` | yes | Human title. |
| `slug` | yes | Unique within the dossier; the target of `[[links]]`. Lowercase ASCII letters, digits and `-`. |
| `sources` | yes | Provenance: ids of ledger entries. MAY be empty only for `answer` pages that cite pages instead, and for pages with `generated: false`. |
| `links` | no | Slugs of the pages this page links to. It MUST agree with the `[[…]]` links in the body. |
| `generated` | yes | `true` if a compiler owns the page, `false` if a person does (§7). |
| `confidence` | no | The compiler's confidence, from 0 to 1. Informative only. |
| `created`, `updated` | yes | Timestamps. |

The kinds:

| Kind | A page about… |
|---|---|
| `source` | one source: what it says. Exactly one per compiled source. |
| `entity` | a person, organisation, place, product or other named thing. |
| `concept` | an idea, method, rule or definition. |
| `topic` | a theme that groups entities and concepts. |
| `synthesis` | an analysis across several sources: comparisons, contradictions, timelines. |
| `answer` | a saved answer to a question, with its citations. |

Implementations MAY define more kinds, prefixed with `x-` (§10).

### 5.4 Index and log

`knowledge/index.md` lists every page, grouped by kind, as `[[slug]]` links with a one-line summary. It is the first file an agent SHOULD read. Compilers MUST keep it up to date after every compile.

`knowledge/log.md` is append-only. Each operation adds one line:

```markdown
- 2026-10-27T09:26:17Z compile energy-storage.pdf → 4 pages (1 new, 3 updated)
- 2026-10-27T09:31:02Z consult "Which storage options fit a 2 MW site?" → saved [[answer-2mw-site]]
- 2026-10-27T10:00:00Z audit 1 drifted source, 3 stale pages
```

Lines MUST NOT be edited or removed after they are written.

## 6. Provenance and drift

### 6.1 Drift

A source has **drifted** when its `origin` resolves and the hash of the original differs from the ledger `sha256`. Every page whose `sources` include a drifted source is **stale**.

- Drift detection is local and best-effort: it depends on the origin being reachable. An unreachable origin is reported as *unknown*, not as drift.
- The copy in `sources/` never changes, so the evidence a page was compiled from stays available even after the original has changed or disappeared.
- Audit MUST NOT modify pages. It reports; recompiling is a separate, explicit compile.

### 6.2 Recompiling and removing

Recompiling a drifted source adds the new version as a new source, compiles it, updates the pages that cited the old one so that they cite the new one, and logs the change. The old source and its copy MAY then be removed.

Removing a source MUST remove its id from every page's provenance. A generated page left with no provenance MUST be deleted. A page with `generated: false` is never deleted; it is left with fewer sources.

## 7. Ownership

The boundary between machine and person is part of the format:

- A page with `generated: true` belongs to compilers. A compiler MAY rewrite it.
- A page with `generated: false`, and every file in `notes/`, belongs to a person. Compilers MUST NOT modify or delete it. They MAY read it, link to it and cite it.
- When a person edits a generated page, the implementation SHOULD set `generated: false`, so the edit is never overwritten.

## 8. Portability rules

A conforming dossier:

1. MUST keep all knowledge in plain files: the manifest, the ledger, the pages, the index and the log. Nothing that matters may live only in `.dossier/`.
2. MUST NOT contain secrets. API keys, tokens and account credentials belong to the user, in the user's own configuration, never inside the folder.
3. MUST NOT depend on absolute paths, except in the optional `origin` field.
4. SHOULD be readable as an ordinary Markdown vault: `[[slug]]` links resolve by file name or by slug in tools such as Obsidian, and the YAML headers are valid frontmatter.
5. SHOULD be friendly to version control: line-based ledger, append-only log, stable ids, no binary files outside `sources/` and `.dossier/`.

Settings that describe the dossier and that every user should share, such as `language` and `description`, go in the manifest. Settings that describe a user or a machine (which model to use, which endpoint, which key) go outside the dossier, or in `.dossier/` if they must be per dossier and never shared.

## 9. Conformance

Programs conform at one or more levels. A program SHOULD state the levels it supports.

| Level | A conforming program… |
|---|---|
| **Reader** | opens a dossier, lists and reads pages, follows links and shows the provenance of each page. |
| **Auditor** | as Reader, and verifies ledger hashes, detects drift and stale pages, broken links and orphan pages. |
| **Compiler** | as Reader, and adds sources, writes pages, keeps index and log, and follows the ownership rules (§7). |

A text editor is a Reader of the pages. An agent connected through the reference MCP server is a Reader and a Compiler. gknowledge aims to be all three.

### 9.1 Agents

Implementations that expose a dossier to AI agents SHOULD offer at least these operations, and SHOULD name them after the model:

| Operation | Returns |
|---|---|
| `search` | pages matching a query, with slugs and summaries |
| `read_page` | a page's body and header, provenance included |
| `list_pages` | pages, optionally filtered by kind |
| `consult` | an answer with citations to pages and sources |
| `add_source` | the new ledger entry; compiles it |
| `audit` | drifted sources, stale pages, broken links |
| `log` | the most recent log lines |

## 10. Versions and extensions

- The manifest field `dossier` holds the format version as `MAJOR.MINOR`. A program MUST refuse to write to a dossier with a higher major version than it knows, and MAY read it.
- Minor versions only add optional fields or kinds. Programs MUST ignore fields they do not know and MUST preserve them when rewriting a record.
- Extensions use the `x-` prefix, optionally followed by a project name: `x-gknowledge-review`, `x-confidence-model`. A field or kind that several implementations adopt can enter a later version without the prefix.

## 11. Prior art

The format stands on earlier work that gave folders meaning:

- **Application and document bundles** on macOS, where a folder is presented as a single document ([Apple](https://developer.apple.com/library/archive/documentation/CoreFoundation/Conceptual/CFBundles/Introduction/Introduction.html)).
- **Git repositories**, where a hidden folder turns a directory into a history ([git](https://git-scm.com/book/en/v2/Git-Internals-Plumbing-and-Porcelain)).
- **BagIt**, the Library of Congress packaging format, where a folder carries a manifest of hashes so that its contents can be verified after transfer ([RFC 8493](https://www.rfc-editor.org/rfc/rfc8493)).
- **RO-Crate**, which describes a research folder with a JSON-LD metadata file ([RO-Crate](https://www.researchobject.org/ro-crate/)).
- **Obsidian vaults**, which made a folder of Markdown files with `[[links]]` a widely used knowledge base ([Obsidian](https://obsidian.md/)).
- **IDE workspaces**, which tried to give a folder, or a group of folders, project meaning, and which tie that meaning to one editor's configuration.

The dossier differs in one respect: its subject is *compiled knowledge with provenance*. BagIt verifies that files arrived intact; the dossier verifies that what was concluded from them still holds. A dossier is designed to be packaged as a BagIt bag or described as an RO-Crate without changes, and a later version of this document may define those mappings.

## 12. Status of the reference implementation

gknowledge 0.3 predates this document and does not yet conform. The gaps, all planned:

| Rule | gknowledge 0.3 | Change |
|---|---|---|
| Manifest `dossier.json` | `gknowledge.json` with `format_version` | write `dossier.json`; read both |
| Ledger in plain files (§5.2, §8.1) | source records only in SQLite (`index/knowledge.db`) | write `sources.jsonl`; SQLite becomes a cache in `.dossier/` |
| No secrets in the folder (§8.2) | API key in `settings/settings.json` | move user and machine settings to the user configuration |
| Derived state in `.dossier/` (§4) | `index/` and `cache/` at the root | move them; add `.gitignore` |
| Header field `kind` | `type` | write `kind`; read both |
| Timestamps without microseconds | microseconds and `+00:00` | write `Z` form; read both |
| Origin as URI | absolute path | write `file:` URIs; read both |
| Name in UI, API and code | "project" | "dossier" |

## 13. Open questions

1. **Citations in body text.** Answers cite pages today; a standard inline syntax for citing a source and a location within it (page, paragraph) would let any Reader verify a single statement.
2. **Source granularity.** Whether a ledger entry may describe a part of a file (a chapter, a table) or a non-file source such as a web page snapshot or an API response.
3. **Signed sources.** Whether the ledger should carry an optional signature or certification reference for sources that come from authoritative providers, so that the trust in a source can be checked as well as its integrity.
4. **Packaging.** Mappings to BagIt and RO-Crate, and a single-file archive form for sending a dossier by email.

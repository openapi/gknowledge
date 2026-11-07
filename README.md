<p align="center">
  <img src="data/icons/hicolor/scalable/apps/io.github.openapi.Gknowledge.svg" alt="" width="96">
</p>

<h1 align="center">gknowledge</h1>

<p align="center"><b>English</b> · <a href="README.zh-CN.md">简体中文</a> · <a href="README.it.md">Italiano</a> · <a href="README.fr.md">Français</a> · <a href="README.pt-BR.md">Português (BR)</a> · <a href="README.es.md">Español</a></p>

<p align="center">
  <b>Karpathy's LLM Wiki as a native GNOME app.</b><br>
  Drop in your documents. Get a linked wiki that an LLM keeps up to date.<br>
  A native GNOME app. Offline by default, plain Markdown on disk, Obsidian-compatible.<br>
  Bring your own brain: a local model, any OpenAI-compatible endpoint, or your own ChatGPT plan.
</p>

<p align="center">
  <a href="LICENSE"><img alt="License: MIT" src="https://img.shields.io/github/license/openapi/gknowledge?style=for-the-badge&color=3584e4"></a>
  <img alt="GTK 4" src="https://img.shields.io/badge/GTK-4-4a86cf?style=for-the-badge&logo=gtk&logoColor=white">
  <img alt="Libadwaita" src="https://img.shields.io/badge/Libadwaita-1.5%2B-4a86cf?style=for-the-badge&logo=gnome&logoColor=white">
  <img alt="Ubuntu 24.04+" src="https://img.shields.io/badge/Ubuntu-24.04%2B-E95420?style=for-the-badge&logo=ubuntu&logoColor=white">
</p>

<p align="center">
  <a href="https://github.com/openapi/gknowledge/actions/workflows/ci.yml"><img alt="CI" src="https://img.shields.io/github/actions/workflow/status/openapi/gknowledge/ci.yml?branch=main&style=flat-square&label=CI"></a>
  <a href="https://github.com/openapi/gknowledge/stargazers"><img alt="Stars" src="https://img.shields.io/github/stars/openapi/gknowledge?style=flat-square&logo=github"></a>
  <a href="https://github.com/openapi/gknowledge/issues"><img alt="Issues" src="https://img.shields.io/github/issues/openapi/gknowledge?style=flat-square"></a>
  <img alt="Last commit" src="https://img.shields.io/github/last-commit/openapi/gknowledge?style=flat-square">
  <a href="https://github.com/openapi/gknowledge/releases/latest"><img alt="Latest release" src="https://img.shields.io/github/v/release/openapi/gknowledge?style=flat-square&color=E95420"></a>
  <img alt="Python 3.10+" src="https://img.shields.io/badge/python-3.10%2B-3776AB?style=flat-square&logo=python&logoColor=white">
  <img alt="Offline first" src="https://img.shields.io/badge/offline-first-2ea043?style=flat-square">
  <img alt="No API key needed" src="https://img.shields.io/badge/API%20key-not%20required-2ea043?style=flat-square">
  <img alt="Obsidian compatible" src="https://img.shields.io/badge/Obsidian-compatible-7C3AED?style=flat-square&logo=obsidian&logoColor=white">
  <img alt="Karpathy LLM Wiki pattern" src="https://img.shields.io/badge/pattern-Karpathy%20LLM%20Wiki-f59e0b?style=flat-square">
  <img alt="Sign in with ChatGPT" src="https://img.shields.io/badge/Sign%20in%20with-ChatGPT-10a37f?style=flat-square&logo=openai&logoColor=white">
  <img alt="Ollama" src="https://img.shields.io/badge/Ollama-supported-000000?style=flat-square">
  <img alt="Flatpak" src="https://img.shields.io/badge/Flatpak-available-4a86cf?style=flat-square&logo=flatpak&logoColor=white">
  <img alt="PRs welcome" src="https://img.shields.io/badge/PRs-welcome-ff69b4?style=flat-square">
</p>

<p align="center">
  <img src="docs/gknowledge-demo.svg" alt="gknowledge in action: drop in AI research papers, get a linked wiki, ask a question and get an answer with citations" width="880">
</p>

<p align="center"><sub>
  Real output of the offline engine on six AI papers (<code>data/demo/papers</code>), no API key.
  Regenerate with <code>make demo-svg</code>.
</sub></p>

## Install

**One line, on Ubuntu 24.04+ and Debian 13+.** It adds the signed gknowledge APT repository, so updates arrive with `apt upgrade` (other distributions get a per-user install):

```bash
curl -fsSL https://github.com/openapi/gknowledge/releases/latest/download/install.sh | bash
```

**Or add the APT repository yourself.** apt also pulls GTK 4, Libadwaita and PyGObject:

```bash
sudo curl -fsSLo /usr/share/keyrings/gknowledge.gpg https://openapi.github.io/gknowledge/gknowledge.gpg
sudo curl -fsSLo /etc/apt/sources.list.d/gknowledge.sources https://openapi.github.io/gknowledge/gknowledge.sources
sudo apt update && sudo apt install gknowledge
```

**On any distribution, with Flatpak** (the GNOME runtime comes from Flathub):

```bash
flatpak install --user https://openapi.github.io/gknowledge/io.github.openapi.Gknowledge.flatpakref
```

Both repositories are described at [openapi.github.io/gknowledge](https://openapi.github.io/gknowledge).

Then open **gknowledge** from the app grid. To remove it: `sudo apt remove gknowledge` (or `flatpak uninstall io.github.openapi.Gknowledge`).

<details>
<summary>Other distributions, from source, and release builds</summary>

- **Fedora, Arch and others:** install PyGObject, GTK 4 and Libadwaita with your package manager, then run the one-line installer above. It installs into `~/.local` without root.
- **From source:** `git clone https://github.com/openapi/gknowledge && cd gknowledge && make install`.
- **Single files:** every version's `.deb` and Flatpak bundle is on the [Releases page](https://github.com/openapi/gknowledge/releases), e.g. `sudo apt install ./gknowledge_all.deb` after downloading [gknowledge_all.deb](https://github.com/openapi/gknowledge/releases/latest/download/gknowledge_all.deb).

</details>

## Why gknowledge

If you have used [LLM Wiki](https://github.com/nashsu/llm_wiki), [Tolaria](https://github.com/refactoringhq/tolaria), [OpenKnowledge](https://github.com/inkeep/open-knowledge), [Reor](https://github.com/reorproject/reor) or [Khoj](https://github.com/khoj-ai/khoj), you already know the loop: **ingest sources, let the model build and maintain a wiki, then ask questions against it.** gknowledge does the same thing as a real GNOME application.

- **Native, not a web view.** GTK 4 and Libadwaita, built to follow the GNOME HIG. No Electron, no Tauri, no browser engine.
- **Works with no account.** A built-in heuristic engine ingests and answers offline. Add a model when you want better synthesis.
- **Your data stays yours.** Markdown with YAML frontmatter plus a readable SQLite index. Open the folder in Obsidian or any editor.
- **Cited, reviewable, incremental.** Every generated page records its sources, answers cite pages, and a review queue keeps you in control.

## The workflow you already know

| You know this from… | What it is | In gknowledge |
|---|---|---|
| Karpathy's LLM Wiki, LLM Wiki | **Ingest**: read a new source, update the pages it touches | Done: two-step extraction with provenance |
| Reor, Khoj | **Ask**: questions answered from your notes, with citations | Done: lexical search plus graph expansion, citations, saved answers |
| LLM Wiki, OpenKnowledge | `index.md` and `log.md`, `[[wikilinks]]`, Obsidian-compatible vault | Done |
| LLM Wiki, Tolaria | **Review** AI changes before they stick | Review queue done, Git diff planned |
| Karpathy's LLM Wiki, OpenKnowledge | **Lint**: orphans, contradictions, stale pages | Planned |
| LLM Wiki | Knowledge graph, clusters, gaps | Planned |
| Tolaria, OpenKnowledge, LLM Wiki | MCP server so agents can read and write the wiki | Done: `gknowledge-mcp` |
| LLM Wiki | Web clipper, folder watch, deep research | Planned |

See [`ROADMAP.md`](ROADMAP.md) for dates and [`TODO.md`](TODO.md) for the backlog.

## Karpathy's LLM Wiki, native on GNOME

In April 2026 Andrej Karpathy described the [LLM Wiki pattern](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f): instead of re-reading raw documents on every question, an LLM builds and maintains a persistent wiki that compounds over time. gknowledge implements it as a desktop app.

**What we kept**

- Three layers: immutable `sources/`, the generated `knowledge/` wiki, and settings that tell the engine how to work.
- The operations: **ingest** (read a source, update the pages it touches) and **query** (answer from the wiki, with citations). **Lint** is next.
- `index.md` as the catalogue and `log.md` as the append-only history.
- Plain Markdown with `[[wikilinks]]` and YAML frontmatter, so the folder opens in Obsidian.
- The human curates, the model maintains.

**What we changed and added**

- **A native app instead of an idea file.** GTK 4 and Libadwaita, with sources, wiki, assistant and review in one window.
- **Works with no model at all.** An offline engine ingests and answers; a model makes it better.
- **Bring your own brain.** Your ChatGPT plan through *Sign in with ChatGPT*, Ollama, or any OpenAI-compatible endpoint.
- **Two-step ingest with provenance.** Analysis first, then pages; every page records its sources.
- **No empty pages, no duplicates.** Pages are created only with real content, names are merged across sources ("Kasparov" and "Garry Kasparov"), minor names stay as mentions until a second source cites them.
- **A review queue** for what the model is unsure about.
- **An MCP server**, so Claude Code, Codex or Cursor can search, read and grow the same wiki.

## Use your wiki from Claude Code, Codex or Cursor

gknowledge ships an MCP server. Point any agent at a project folder:

```bash
claude mcp add gknowledge -- gknowledge-mcp ~/Knowledge/my-project     # Claude Code
codex mcp add gknowledge -- gknowledge-mcp ~/Knowledge/my-project      # Codex CLI
```

For Cursor or other clients, add this to the MCP configuration:

```json
{ "mcpServers": { "gknowledge": { "command": "gknowledge-mcp", "args": ["/home/you/Knowledge/my-project"] } } }
```

| Tool | What the agent can do |
|---|---|
| `search_wiki` | find pages by keyword |
| `read_page` | read a page with its sources and backlinks |
| `list_pages` | list pages by type |
| `ask` | get a cited answer, optionally saved back into the wiki |
| `add_source` | import and ingest a file |
| `recent_activity` | see what changed recently |

## Try it from source

```bash
sudo apt install python3-gi gir1.2-gtk-4.0 gir1.2-adw-1   # Ubuntu / Debian
git clone https://github.com/openapi/gknowledge && cd gknowledge
make start      # opens a demo project with six AI papers already ingested
```

`make start` also restarts the app whenever you edit the source, which makes it the fastest way to hack on gknowledge. Install it for daily use with `make install`.

## Bring your own brain

| Provider | Needs | Notes |
|---|---|---|
| **Offline** (default) | nothing | Heuristic extraction and extractive answers. Fully private. |
| **ChatGPT plan** | A Plus or Pro account | Preferences, Provider, *Sign in with ChatGPT*. Usage is charged to your own plan, no API key. |
| **Ollama / LM Studio / vLLM** | A local server | Any OpenAI-compatible endpoint on your machine. |
| **OpenAI-compatible cloud** | An API key | OpenAI, OpenRouter, Together, and similar. |

Nothing is sent anywhere unless you pick a provider that is not offline.

## How it compares

| | gknowledge | LLM Wiki | Tolaria | OpenKnowledge | Reor (archived) | Khoj |
|---|---|---|---|---|---|---|
| Native GNOME / GTK 4 | **yes** | Tauri | Tauri | Electron | Electron | web + Electron |
| Works offline, no key | **yes** | needs a model | AI optional | agent-driven | local model | self-host |
| Plain Markdown vault | **yes** | yes | yes | yes | yes | reads yours |
| Linux packaging | `.deb`, Flatpak | `.deb`, AppImage | AppImage, `.deb` | `.deb`, `.rpm` | AppImage | pip, Docker |
| License | MIT | GPL-3.0 | AGPL-3.0 | GPL-3.0 | AGPL-3.0 | AGPL-3.0 |

Details and history of each project are in [`DISTRIBUTING.md`](DISTRIBUTING.md).

## gknowledge is an alternative to…

`gknowledge` sits at the intersection of *LLM-powered knowledge bases*, *local-first note tools*, and *document RAG systems*. If you have used any of the tools below, you already understand the shape of the problem — `gknowledge` addresses it as a **native GNOME/GTK application** that is **local-first, provider-agnostic, and usable fully offline** (no API key required, thanks to a built-in heuristic extraction engine).

**LLM wiki / auto-knowledge-base builders** (the closest peers, several studied in [`NOTES.md`](NOTES.md)):

- [LLM Wiki (`nashsu/llm_wiki`)](https://github.com/nashsu/llm_wiki) — Tauri desktop app implementing Karpathy's incremental "LLM builds and maintains a wiki" pattern
- [Tolaria](https://github.com/refactoringhq/tolaria) — files-first, git-first Markdown knowledge base with AI-assisted editing
- [WeKnora (Tencent)](https://github.com/Tencent/WeKnora) — enterprise RAG + agents + auto-wiki framework
- [OpenKnowledge (Inkeep)](https://openknowledge.ai) — WYSIWYG Markdown editor with agent/MCP integrations for LLM wikis
- [Reor](https://github.com/reorproject/reor) — local-first AI note-taking that auto-links related notes
- [Khoj](https://github.com/khoj-ai/khoj) — self-hostable AI "second brain" over your documents

_Not a peer: [Google NotebookLM](https://notebooklm.google.com) offers a similar cited-notebook experience but is closed-source and cloud-only._

**Document RAG / "chat with your knowledge" engines:**

- [AnythingLLM](https://github.com/Mintplex-Labs/anything-llm), [Onyx (formerly Danswer)](https://github.com/onyx-dot-app/onyx), [Quivr](https://github.com/QuivrHQ/quivr), [PrivateGPT](https://github.com/zylon-ai/private-gpt), [GPT4All](https://github.com/nomic-ai/gpt4all), [Cherry Studio](https://github.com/CherryHQ/cherry-studio), [Verba (Weaviate)](https://github.com/weaviate/Verba)

**Local-first / networked-thought note tools** (which `gknowledge` complements with automated ingestion and provenance):

- [Obsidian](https://obsidian.md) (+ Smart Connections / Copilot plugins), [Logseq](https://logseq.com), [SiYuan](https://github.com/siyuan-note/siyuan), [Trilium Notes](https://github.com/zadam/trilium), [Zettlr](https://www.zettlr.com), [Foam](https://foambubble.github.io/foam/), [Dendron](https://www.dendron.so), [Joplin](https://joplinapp.org), [Notion](https://notion.so), [Tana](https://tana.inc), [Capacities](https://capacities.io), [Heptabase](https://heptabase.com), [RemNote](https://remnote.com)

**Document / reference managers with growing AI features:**

- [Zotero](https://www.zotero.org), [Paperless-ngx](https://github.com/paperless-ngx/paperless-ngx)

### How gknowledge differs

- **Native to GNOME, not Electron/Tauri or web-first** — GTK 4 + Libadwaita, HIG-aligned, Flatpak-friendly.
- **Offline-first and provider-agnostic** — a local heuristic engine ships in the box; OpenAI-compatible endpoints (OpenAI, Ollama, LM Studio, vLLM, OpenRouter, …) are optional, swappable, and configured per project.
- **Inspectable, user-owned format** — knowledge is plain Markdown with YAML frontmatter (Obsidian-compatible) plus a readable SQLite index; nothing is locked behind a sync service.
- **Incremental, not stateless RAG** — sources are ingested once into a persistent, cross-linked knowledge space with provenance, rather than re-retrieved from scratch on every question.
- **Human-in-the-loop** — generated content is clearly marked and a review queue keeps you in editorial control.

## Project docs

- [`ROADMAP.md`](ROADMAP.md) — milestones and the features we are borrowing from peers
- [`TODO.md`](TODO.md) — actionable backlog
- [`DISTRIBUTING.md`](DISTRIBUTING.md) — positioning and distribution study of comparable projects (Italian)
- [`CONTRIBUTING.md`](CONTRIBUTING.md) — how to contribute
- [`docs/DESIGN.md`](docs/DESIGN.md) — the original product and design document
- [`CHANGELOG.md`](CHANGELOG.md) — what changed in each release

## License

[MIT](LICENSE). Contributions are welcome, see [`CONTRIBUTING.md`](CONTRIBUTING.md).

## Star history

<a href="https://star-history.com/#openapi/gknowledge&Date">
  <img src="https://api.star-history.com/svg?repos=openapi/gknowledge&type=Date" alt="Star history" width="600">
</a>

If gknowledge is useful to you, a star helps other GNOME users find it.


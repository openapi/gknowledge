---
title: I wanted Karpathy's LLM Wiki as a real Linux app, so we built one in GTK 4
published: false
description: gknowledge turns your documents into a linked Markdown wiki that an LLM keeps up to date. Native GNOME, offline by default, Obsidian-compatible, with an MCP server for coding agents.
tags: linux, gnome, opensource, ai
cover_image: https://raw.githubusercontent.com/openapi/gknowledge/main/docs/launch/social-preview.png
canonical_url: https://github.com/openapi/gknowledge
---

<!--
Publishing notes (remove before posting):
- dev.to: paste as is; the front matter above is dev.to's format. Set `published: true` when ready.
- Medium: drop the front matter, import the dev.to URL via "Import a story" so Medium sets the canonical link back.
  Good publications to submit to: Stackademic, Level Up Coding, ITNEXT.
- Post on a weekday morning, US time, ideally the same day as Show HN and the TWIG item (see README.md in this folder).
-->

In April 2026 Andrej Karpathy published a short "idea file" called [LLM Wiki](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f). The idea is simple: instead of having a model re-read your raw documents every time you ask a question (classic RAG), let it **build and maintain a persistent wiki** from them. Every new source updates the pages it touches. The knowledge compounds.

Within a week there were thousands of implementations. Most of them are agent skills, Obsidian plugins or CLI scripts. The desktop apps that exist are Electron or Tauri, and Linux is usually the platform that gets the AppImage and a shrug.

I use GNOME every day, and I wanted this as a real GNOME app. So we built **[gknowledge](https://github.com/openapi/gknowledge)**: MIT-licensed, GTK 4 and Libadwaita, written in Python.

![A wiki page generated from a set of AI papers, with its sources listed](https://raw.githubusercontent.com/openapi/gknowledge/main/docs/screenshots/wiki-page.png)

## What it does

1. **Drop in documents.** PDFs, Markdown, text. They are copied into `sources/` and never modified.
2. **It builds the wiki.** A two-step ingest first analyses each source, then writes or updates pages for entities, concepts and topics, linked with `[[wikilinks]]`.
3. **Ask questions.** Answers come from the wiki, cite the pages they used, and can be saved back as new pages.
4. **Review what the model is unsure about.** Uncertain merges and new pages go to a review queue instead of silently landing in your knowledge base.

![An answer with citations to wiki pages](https://raw.githubusercontent.com/openapi/gknowledge/main/docs/screenshots/cited-answer.png)

## What we kept from Karpathy's gist

- **Three layers**: immutable sources, the generated wiki, and settings that tell the engine how to work.
- **The operations**: ingest and query today, lint (orphans, contradictions, stale pages) next.
- **`index.md` as the catalogue and `log.md` as the append-only history.**
- **Plain Markdown with YAML frontmatter**, so the `knowledge/` folder opens in Obsidian or any editor. There is also a readable SQLite index next to it, but nothing important lives only there.
- **The human curates, the model maintains.**

## What we changed

**It works with no model at all.** This was the decision I am happiest about. A built-in heuristic engine ingests and answers fully offline, with no account and no API key. It is not as good as an LLM at synthesis, but it means the app is useful the second you open it, and it never stops working because a provider changed its pricing.

**Bring your own brain.** When you want better synthesis, point it at Ollama, LM Studio, vLLM, any OpenAI-compatible endpoint, or sign in with your existing ChatGPT plan. The provider is set per project, and nothing leaves your machine unless you pick one that is not offline.

**Provenance everywhere.** Every generated page records which sources it came from. Names are merged across sources ("Kasparov" and "Garry Kasparov" become one page), and minor names stay as mentions until a second source cites them, so you do not end up with hundreds of empty stubs.

**An MCP server.** The same wiki is available to coding agents:

```bash
claude mcp add gknowledge -- gknowledge-mcp ~/Knowledge/my-project   # Claude Code
codex mcp add gknowledge -- gknowledge-mcp ~/Knowledge/my-project    # Codex CLI
```

Agents can `search_wiki`, `read_page` (with sources and backlinks), `ask` for a cited answer, and `add_source` to grow the wiki. You curate in the app; your agent reads the same pages.

## Why native GTK and not Electron

Partly taste: I want an app that looks and behaves like the rest of my desktop, follows the GNOME HIG, respects dark mode and keyboard navigation, and starts instantly.

Partly lessons from the projects that came before. Reor, the closest earlier local-first AI notes app, had Linux crashes at launch and an AppImage that needed `--no-sandbox` on Ubuntu 24.04. Tauri apps depend on the distribution's WebKitGTK. A GTK 4 app on GNOME has none of those problems, and it fits the distribution channel Linux users actually use: packages today, Flathub next.

## How it compares

| | gknowledge | LLM Wiki (nashsu) | Tolaria | OpenKnowledge | Reor (archived) |
|---|---|---|---|---|---|
| Toolkit | GTK 4 + Libadwaita | Tauri | Tauri | Electron | Electron |
| Works offline, no key | yes | needs a model | AI optional | agent-driven | local model |
| Plain Markdown vault | yes | yes | yes | yes | yes |
| MCP server | yes | yes | yes | yes | no |
| License | MIT | GPL-3.0 | AGPL-3.0 | GPL-3.0 | AGPL-3.0 |

All of these are good projects, and if you are on macOS or Windows they are probably what you want. gknowledge is for people who live on the Linux desktop.

## Try it

On Ubuntu 24.04+ and Debian 13+:

```bash
curl -fsSL https://github.com/openapi/gknowledge/releases/latest/download/install.sh | bash
```

Or grab the `.deb` from the [releases page](https://github.com/openapi/gknowledge/releases). On other distributions the installer falls back to a per-user install. From source, `make start` opens a demo project with six AI papers already ingested.

## What's next

Lint (orphans, contradictions, stale pages), a knowledge graph view, folder watching, Flathub, and a Git-backed history of every change the model makes.

The project is young and moving fast. If you try it, I would love to hear what breaks, what you would ingest first, and what you think the offline engine should do better. Issues and PRs are welcome on [GitHub](https://github.com/openapi/gknowledge), and a ⭐ helps other Linux users find it.

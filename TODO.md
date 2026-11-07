# TODO

Actionable backlog derived from [`ROADMAP.md`](ROADMAP.md). Ordered by what unblocks the first 100 stars. `[ ]` open, `[x]` done.

## Feedback from dev.to: Flatpak first, drift over hallucination (2026-10-17)

Source: [comment by Justin (@fromthearchitect)](https://dev.to/fromthearchitect/comment/3i4d5) on the launch article. Data/AI architect on Fedora, writing a GNOME photo app in Rust; starred the repo and will try gknowledge "once a Flatpak is available". Follow-up is tracked in `DISTRIBUTING.md` §8.1 (dev.to row).

Flatpak (the `.deb` and `install.sh` do nothing for Fedora, Arch or openSUSE users)
- [x] Flatpak build is green in CI (`appstreamcli compose` succeeds since the GNOME 51 bump); every release attaches a bundle and `repos.yml` publishes the remote at `openapi.github.io/gknowledge` (closes #24).
- [x] `flatpak install --user https://openapi.github.io/gknowledge/io.gknowledge.Gknowledge.flatpakref` works on Ubuntu (2026-10-19): pulls GNOME 51 from Flathub, installs 0.2.2, the app launches.
- [x] Inside the Flatpak, New Project failed with "disk I/O error" (SQLite WAL needs shared memory the document portal does not provide); the store no longer uses WAL and converts old databases. Project creation, PDF/Markdown import, ingest, query and drift check verified on a portal path (2026-10-19).
- [x] Inside the Flatpak, by hand: create a project, import through the file chooser, ingest, reopen after a restart (2026-10-19).
- [x] Verify on a non-Ubuntu distro: Justin installed the Flatpak on Fedora 44 and reported it works, no issues ([comment of 2026-10-27](https://dev.to/fromthearchitect/comment/3iek7)). Still triage first anything he opens as `justinf555`.
- [x] README: badge and comparison table no longer say "Flatpak planned" (install section left as is).
- [x] Vendor `pypdf` 6.19.0 in the manifest (the 0.2.2 bundle has `No module named 'pypdf'`, so PDF import fails). Builds green on PR #42.
- [x] Release 0.3.0, tagged 2026-10-19: `.deb` and `.flatpak` on the release, `gknowledge-mcp` 0.3.0 on PyPI. A fresh install from the Pages flatpakref works, and the old ID's ref carries the end-of-life-rebase to the new one.
- [x] CI and release Flatpak jobs are blocking (no `continue-on-error`); CI uploads an installable `gknowledge-dev.flatpak` artifact for every PR.
- [ ] Flathub itself stays paused (AI-assisted code policy, see P0 below); say so plainly if asked, and point to the Pages remote.

Develop against the runtime users get
- [x] `make start-flatpak`: the `make start` loop run inside `org.gnome.Platform` (version read from the manifest), so host GTK/libadwaita differences show up before release.
- [x] CONTRIBUTING documents `make start-flatpak`.
- [x] With Justin's permission ([reply of 2026-10-19](https://dev.to/fromthearchitect/comment/3ia9i)), CONTRIBUTING links his GNOME SDK setup write-up (Part 1 of his GNOME + Rust series); since 2026-10-27 it links the whole series page, now at Part 6.

Drift, not hallucination
- [x] `core/lint.py`: `ChangeDetector` flags ingested sources whose original file no longer matches the ingested hash, with the pages that cite them.
- [x] `IngestionManager.refresh_source()`: copy the new version, update hash and size, re-ingest (builds on #30's `reingest_source`).
- [x] UI: changed sources show "changed since ingest" with a warning icon; the Re-ingest button becomes "Update"; a toast on project open and when the window regains focus.
- [x] MCP tool `stale_sources` so agents can run the lint step of Karpathy's pattern.
- [x] Design written up in PR #42, crediting the suggestion; invite Justin to review it when replying.
- [ ] Mark affected pages as possibly outdated in the Knowledge pane (badge on the page, note in the page header).
- [ ] Trigger the check from `Gio.FileMonitor` on origin files (#3) instead of only on open and focus.
- [ ] Sources imported through the document portal: confirm `origin_path` stays readable across sessions inside the Flatpak.
- [ ] Emit drift as review items once the Review queue is split (#17).

## UX review with a real ChatGPT plan (2026-10-13)

Test: 6 short AI-paper notes (about 300 words each), provider "ChatGPT plan", model picked automatically (gpt-6.1-sol).
Ingest took 102 s (about 17 s per source, serial) and produced 114 pages and 18 review items. Answers were accurate and cited, 7 to 8 s each.

Blocking or misleading
- [x] Ask crashed in the UI (SQLite used from a worker thread). Fixed with a shared, locked connection.
- [ ] Ingest with descriptions is slower: 163 s for 6 sources (27 s each) instead of 102 s. Parallelise.
- [x] Saved model `gpt-4o-mini` is rejected for ChatGPT plans (HTTP 400) and ingest silently fell back to offline heuristics. Fixed: models come from the account's `/models` list (`models[].slug`, `visibility == "list"`).
- [x] Tell the user when extraction falls back to heuristics (toast plus a mark on the source); today it is silent.
- [x] Preferences: replace the free-text Model field with a dropdown filled from the provider's model list; show the active model in the sidebar subtitle.
- [ ] "Ingest Queued" looks like an error (orange, disabled) when nothing is queued. Hide it or make it neutral.

Reading the wiki
- [x] Render Markdown (headings, bold, lists) instead of showing raw `#`, `**`, `_…_` in a monospace view.
- [x] Make `[[wikilinks]]` clickable and navigate to the page; show backlinks.
- [x] Group the Knowledge list by type (Sources, Entities, Concepts, Topics), add search, drop the "AI" badge from every row.
- [ ] Source detail: button to open the original file.

Wiki quality
- [x] (2026-10-13: 114 pages became 64 with ChatGPT, 100 became 10 offline) Too many stub pages: 83 of 114 are one-line entity or concept pages ("Concept discussed in the knowledge base."). Create pages only above a mention threshold, or merge stubs into the source page.
- [x] Deduplicate near-identical pages ("Retrieval-Augmented Generation", "Retrieval-Augmented Generation (RAG)", "Chain-of-thought prompting" vs the source page) by normalised title and aliases.
- [x] Fix title casing ("Llm wiki", "Bleu").
- [x] Deduplicate citations in answers (the same page appeared three times).

Review queue
- [ ] The 18 items are "open questions" tagged `deep_research`, not things to review. Separate "Questions to explore" from "Needs review", and offer actions (ask, research, dismiss) instead of a single "Resolve".
- [ ] Review rows wrap badly in the narrow sidebar; show the full item in the content pane with its actions.

Assistant
- [ ] Stream answers token by token (the provider already streams) instead of "Thinking…" for 8 s.
- [ ] Empty state with suggested questions generated from the wiki.
- [ ] Keep a conversation history, not a single answer.

Speed and feedback
- [ ] Ingest is serial at about 17 s per short source; run 2 to 3 sources in parallel within plan limits and show per-source progress with an estimate.
- [ ] Add a Cancel button for ingestion (the core already supports cancel).
- [ ] Re-ingest and delete actions for a source.

## P0: before any public announcement

### Repository and positioning
- [x] Fix the Tolaria link in `README.md` (`https://github.com/refactoringhq/tolaria`).
- [x] Move NotebookLM out of the peer list; keep it as a one-line "cloud-only, not open source" aside.
- [ ] Add a "What we kept from Karpathy's LLM Wiki / what we changed" section.
- [ ] Add a short comparison table against nashsu/llm_wiki, Tolaria, OpenKnowledge, Reor.
- [ ] Add GitHub topics: `llm-wiki`, `llm-wiki-karpathy`, `gnome`, `gtk4`, `libadwaita`, `pkm`, `knowledge-base`, `local-first`.
- [ ] Capture 3 to 5 screenshots and a 60-second demo GIF.
- [ ] Ship `examples/sample-vault/` that ingests offline in under a minute.
- [x] Add `CONTRIBUTING.md`, issue and PR templates (Code of Conduct is a section of CONTRIBUTING; `good first issue` label and seeded issues done).
- [ ] Publish a statement on AI-assisted code (Flathub and GNOME Circle have an AI-code policy since May 2026; this repo is developed with AI assistance and must say so plainly).

### Flatpak and Flathub (paused: kept warm, do not submit until policy allows AI-assisted code)
- [x] App ID is `io.github.openapi.Gknowledge` since 0.3.0 (`io.gknowledge.*` used gknowledge.io, which nobody owns). The Pages remote rebases the old ID with end-of-life-rebase; `.desktop` has `X-Flatpak-RenamedFrom`, MetaInfo has `<replaces>`.
- [x] Bump the runtime to GNOME 51 (current stable on Flathub). Not yet built in CI.
- [x] Replace `--filesystem=home` with FileChooser / Documents portals; keep only `--share=network`. Done in the manifest, untested in a real Flatpak build.
- [ ] Build from `git`/`archive` sources instead of `type: dir` (`pypdf` vendored).
- [ ] Complete MetaInfo: screenshots (URLs still missing; developer, urls, branding added), `developer`, `url`, branding colors, release notes, summary of 35 characters or fewer.
- [ ] Make `flatpak-builder-lint` pass with no exceptions.
- [ ] Add a `.doap` file. (CI workflows for tests, metadata validation and Flatpak build exist; Flatpak job is blocking since 0.3.0.)
- [ ] Open the `flathub/flathub` submission PR; verify the developer at merge.

## P0b: GNOME and Ubuntu integration (gedit-style)

- [x] Keyboard accelerators for new/open/preferences/quit.
- [x] Desktop entry advertises Markdown, text, PDF and HTML; files passed by the file manager are imported into the current project.
- [x] About dialog points to the real repository and issue tracker.
- [ ] GSettings schema (`io.github.openapi.Gknowledge`): window size, maximized, last project, provider; install and compile it in `make install` and the Flatpak.
- [ ] Register projects with `Gtk.RecentManager`.
- [ ] `Gio.Notification` when ingestion finishes or fails.
- [ ] Drag and drop of files and folders onto the Sources pane.
- [ ] Primary menu and shortcuts window (`Ctrl+?`); `Adw.ShortcutsDialog` when libadwaita allows.
- [ ] `gettext` setup: wrap UI strings, `po/`, `POTFILES`, meson or Makefile rules.
- [ ] D-Bus activation file and `DBusActivatable=true`.
- [ ] GNOME Shell search provider (`org.gnome.Shell.SearchProvider2`) over the wiki index.
- [ ] Verify on Ubuntu 24.04 LTS (GNOME 46, libadwaita 1.5, Yaru) and on the current Ubuntu LTS; avoid APIs newer than libadwaita 1.5, or guard them.
- [ ] Replace `Adw.AboutWindow` with `Adw.AboutDialog` behind a version check.
- [ ] Debian packaging (`debian/`) and a CI job producing a `.deb`.
- [ ] Launchpad PPA for `apt install`.
- [ ] `snapcraft.yaml` using the GNOME extension; test in Ubuntu Software.
- [ ] Document enabling Flatpak/Flathub on Ubuntu in the README.

## P1: the "wow" features (v0.3)

### Graph and structure
- [ ] Read links from the SQLite store and render a graph view (Gtk drawing area or Cairo; no web view).
- [ ] Community detection (Louvain or label propagation) with colored clusters.
- [ ] "Insights" panel: weakly connected pages, hubs, suggested missing topics.

### Lint
- [ ] `core/lint.py`: orphan pages, duplicate titles, missing sources, broken `[[links]]` (stale sources done, see the dev.to feedback section).
- [ ] Optional LLM contradiction check.
- [ ] Emit lint findings as review items.
- [ ] Append every lint run to `knowledge/log.md` using the parseable `## [date] op | title` prefix.

### History and trust
- [ ] Optional per-project Git repo: commit after each ingest and each accepted review.
- [ ] In-app diff for a generated page ("what changed since last ingest").
- [ ] Show provenance (source list with open-at-source) on every generated page.
- [ ] Show similarity or relevance score next to each citation.

### Ingestion
- [ ] Watch `sources/` and linked folders; reprocess on change (Gio.FileMonitor).
- [ ] Per-job progress and a visible cancel/retry in the UI (core already supports both).

## ChatGPT plan provider (OpenAI "Sign in with ChatGPT", announced 2026-09-29)

Facts from OpenAI's docs (read 2026-10-13; the program is two weeks old, re-check before building):
- Open-source and locally run apps are eligible; paid or hosted SaaS must join a waitlist. Only Plus and Pro plans can grant plan usage.
- Endpoints: authorize `https://auth.openai.com/api/accounts/authorize`, token `https://auth.openai.com/api/accounts/oauth/token`, discovery `https://auth.openai.com/.well-known/openid-configuration`.
- Public client, no secret. First sign-in uses `client_id=dynamic_agent_client` plus `agent_name_hint` and a stable per-install `ext_agent_host_id`; the callback returns an issued `client_id` that must be saved and reused.
- PKCE `S256`, fresh `state` and `nonce`, redirect `http://127.0.0.1:<port>/auth/callback` (not `localhost`), same URI in authorize and token requests.
- Scopes: `openid profile email offline_access resource.invoke chatgpt.tokens.use.direct`, `resource=https://api.openai.com/v1`. Signing in alone does not authorise spending: check the granted scope.
- Access token 1 hour, refresh token 30 days and rotating. Responses API only, with `store: false`, `stream: true`, no explicit system-role items, no `temperature` or `max_output_tokens`. No image generation, file search, code interpreter or hosted MCP.
- Users set weekly caps per app in ChatGPT Settings > Usage. Errors: 429 `subscription_sharing_usage_limit_exceeded`, 403 `subscription_sharing_user_not_eligible`. There is no automatic fallback; the app must provide one.

Tasks:
- [ ] Read the "errors and recovery" and terms pages; confirm that a Python implementation of the raw OAuth flow (no JS DevKit) is allowed.
- [x] `gknowledge/providers/chatgpt.py`: OAuth flow (loopback listener, PKCE, id-token claims check), refresh, revoke, Responses API client with streaming. JWKS signature verification is skipped on purpose (token comes straight from the token endpoint over TLS, OIDC Core 3.1.3.7); add it if a crypto dependency is ever accepted.
- [x] Open the browser through `Gtk.UriLauncher`; Preferences shows waiting, signed-in and error states. Cancel on dialog save/close is basic.
- [ ] Move tokens from `~/.config/gknowledge/chatgpt.json` (0600, atomic write, outside projects) to libsecret / the Secret portal. Sign-out already revokes and clears.
- [x] Persist `ext_agent_host_id` and the issued `client_id` per install, in the app config (not in project folders).
- [x] Adapt requests to the Responses API rules (system text goes in `instructions`, no temperature, stream, store false).
- [x] Cap-reached and not-eligible errors are reported; extraction falls back to the offline engine automatically.
- [ ] Show a persistent "Using ChatGPT plan" indicator in the main window and a "Manage usage" link.
- [ ] Verify against the real service with a Plus or Pro account (model list, default model, `store: false` behaviour). Only fake servers were tested so far.
- [x] Tests with fake OAuth and Responses servers (`tests/test_chatgpt.py`); no network in CI.
- [ ] Document the privacy model: documents are sent to OpenAI only when this provider is selected.

## P2: agent-ready (v0.4)

- [x] `gknowledge-mcp`: stdio MCP server exposing search_wiki, read_page, list_pages, ask, add_source, recent_activity (v0.2.0).
- [ ] Write-approval mode: MCP writes land in the review queue, not directly in `knowledge/`.
- [ ] Optimistic concurrency guard (mtime check) to avoid clobbering concurrent edits.
- [ ] `AGENTS.md` shipped inside each project describing the wiki schema.
- [x] Docs recipes for Claude Code, Cursor, Codex (README).
- [ ] Optional `.obsidian/` scaffold and documented vault compatibility.

## P3: daily driver (v0.5)

- [ ] Built-in Markdown editor with live preview for notes and generated pages.
- [ ] Related-notes sidebar (lexical + graph first; embeddings optional).
- [ ] Optional embeddings via the OpenAI-compatible `/embeddings` endpoint.
- [ ] Ollama detection and one-click setup in Preferences.
- [ ] Browser clipper (companion extension posting to a local-only endpoint).
- [ ] Extra parsers: DOCX, HTML clean-up, EPUB.

## P4: research and hardening (v0.6 to 1.0)

- [ ] Opt-in deep research with explicit consent per query; ingest results into the review queue.
- [ ] Schema versioning and migrations for `gknowledge.json` and the SQLite store.
- [ ] Crash-recovery tests for the ingestion queue.
- [ ] Accessibility audit (Orca, high contrast, large text) and translation setup.
- [ ] GNOME Circle application when intake reopens.

## Independent distribution (current priority)

- [ ] Run the launch playbook in `docs/launch/README.md` (Show HN, X, Reddit, TWIG, lists) and upload `docs/launch/social-preview.png` as the repository social preview.

- [x] `build-aux/deb/build-deb.sh` builds a `.deb` with `dpkg-deb`; CI builds and installs it; release workflow attaches it.
- [x] `build-aux/arch/PKGBUILD` ready for AUR (needs a tag and `updpkgsums`).
- [x] `build-aux/snap/snapcraft.yaml` draft (untested).
- [x] First release `v0.1.0` (2026-10-13) with `.deb`, version-independent `gknowledge_all.deb` and `install.sh` (`curl … | bash`).
- [x] Fix the Flatpak build: `appstreamcli compose` succeeds in CI since 2026-10-19 (run 39223882741).
- [ ] Test `sudo apt install ./gknowledge_all.deb` on a clean Ubuntu 24.04 VM.
- [ ] Publish a signed APT repository on GitHub Pages (reprepro or aptly) and document `curl | gpg --dearmor` setup.
- [x] Publish a Flatpak OSTree repo on GitHub Pages with a `.flatpakrepo` file; document `flatpak remote-add` (README documents the `.flatpakref` install).
- [ ] Register `gknowledge` on the Snap Store and test the snap on Ubuntu 24.04; decide on `home` plug vs portals.
- [ ] Create a Launchpad account and PPA; upload a source package (`debian/` with debhelper).
- [ ] Submit AUR package.
- [ ] Add Fedora COPR spec and a Nix flake.
- [ ] Write the launch post (thesis, demo GIF, install one-liners) and the Show HN title.
- [ ] Draft per-community posts: r/gnome, r/Ubuntu, r/ObsidianMD, r/LocalLLaMA, Mastodon, Planet GNOME feed.

## Distribution and community

- [x] Release workflow exists (`.github/workflows/release.yml`, builds a `.flatpak` bundle on `v*` tags); first verified Flatpak release is v0.3.0.
- [ ] AUR package (`gknowledge`), ideally maintained by a second person.
- [ ] Release notes in MetaInfo for every release; monthly cadence at least.
- [ ] Announce on This Week in GNOME via `#thisweek:gnome.org` the week of the Flathub merge.
- [ ] Show HN with the thesis in the title; Phoronix and OMG! Ubuntu tips.
- [ ] Recruit a co-maintainer with release rights before 1.0.
- [ ] Track installs weekly from the Flathub stats API.

## Known gaps in the current MVP

- [ ] Offline entity extraction is noisy on prose (for example SAN move fragments such as `Ba4 Nf6`, sentence-initial verbs, generic nouns, `Entity referenced by ingested sources.` boilerplate in answers). Filter chess/move patterns and stopword-led capitalised words, and improve extractive answers.
- [ ] Demo animation (`docs/gknowledge-demo.svg`) currently shows the offline engine; re-record with an LLM provider once the ChatGPT flow is verified.

- [ ] No UI for editing or deleting knowledge pages.
- [ ] Offline heuristics are keyword-based; add language detection beyond English.
- [ ] `reviews/` directory is reserved but unused.
- [ ] Test coverage is core-only; add a smoke test that opens the window under a headless display.

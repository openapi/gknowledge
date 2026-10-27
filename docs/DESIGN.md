# gknowledge design document

The original product and design document, kept as the long-term direction. The user-facing overview is in the [README](../README.md).

The on-disk format is specified separately, as an open format other programs can implement: [The Dossier format](dossier/SPEC.md).

## Status

This repository contains **a working MVP** of the native application plus the
product/design document below (kept as the long-term direction).

Implemented so far (README Development Priorities 1–6):

1. ✅ **Project format** — deterministic, human-readable on-disk layout (Markdown + SQLite index)
2. ✅ **Native app shell** — GTK 4 + Libadwaita, four-pane workspace (Sources / Knowledge / Assistant / Review)
3. ✅ **Source import + persistent ingestion state** — cache-aware (SHA-256) queue with retry and crash recovery
4. ✅ **LLM extraction pipeline** — two-step analysis→generation, provider-agnostic, with an offline heuristic engine
5. ✅ **Generated knowledge with provenance** — every page records its sources and cross-links
6. ✅ **Query & retrieval** — lexical search + graph expansion + cited answers, savable back into the wiki

### Running the app

Requirements: **Python 3.10+**, **GTK 4**, **Libadwaita**, **PyGObject** (`python3-gi`).
On Debian/Ubuntu: `sudo apt install python3-gi gir1.2-gtk-4.0 gir1.2-adw-1`.
Optional: `pip install --user pypdf` for PDF sources.

```bash
make start            # run from source on a pre-ingested demo project (./sandbox, isolated config)
make run              # run from the source tree (opens your last project)
make test             # run the headless core test suite
make install          # install locally into ~/.local (adds a `gknowledge` launcher + .desktop entry)
make install PREFIX=/usr/local   # system-wide (use with sudo)
make uninstall        # remove a local install
make flatpak          # build/install a Flatpak (needs flatpak-builder + org.gnome.Sdk 51)
```

After `make install`, launch **gknowledge** from your app grid, or run `gknowledge`
from a terminal (ensure `~/.local/bin` is on your `PATH`).

No API key is needed: new projects default to the **offline** provider. To use a
cloud or local model, open **Preferences** and pick an OpenAI-compatible endpoint
(OpenAI, Ollama, LM Studio, vLLM, OpenRouter, …).

### On-disk project layout

```
my-project/
├── gknowledge.json          # manifest (format version, id, name)
├── sources/                 # imported raw files (immutable copies)
├── knowledge/
│   ├── index.md             # catalog of pages
│   ├── log.md               # human-readable operation log
│   ├── overview.md          # global summary (regenerated on ingest)
│   ├── sources/  entities/  concepts/  topics/  answers/  synthesis/
├── notes/                   # user-authored notes
├── index/knowledge.db       # SQLite index (metadata, provenance, links, jobs, reviews)
├── cache/
└── settings/settings.json   # provider + language settings
```

### Architecture (implemented)

- `gknowledge/core/` — headless domain layer (no GTK): project format, SQLite store, parsers, hashing, heuristics, two-step extraction, ingestion queue, query engine.
- `gknowledge/providers/` — provider abstraction: `offline` (local heuristics) and `openai_compatible` (any OpenAI-style HTTP endpoint), selected from project settings.
- `gknowledge/ui/` — GTK 4 / Libadwaita interface (window, panes, preferences).
- `tests/` — end-to-end core tests that run fully offline.

The README below remains the product/design document and long-term roadmap.

## Vision

Modern knowledge tools are converging around a strong idea:

- users bring their own sources
- the system reads and organizes them
- an LLM helps connect, summarize, expand, and maintain the knowledge over time
- the resulting knowledge base becomes more useful with every interaction

`gknowledge` exists to bring that model to the GNOME ecosystem with a native, distribution-friendly application designed for Ubuntu and other Linux environments.

The project aims to be:

- native to GNOME in behavior, look, and integration
- useful offline-first where possible, with optional cloud LLM integrations
- open and inspectable, with files and data formats the user can understand
- extensible, so different LLM providers and local pipelines can be integrated cleanly
- robust enough for official distribution channels

## Why This Project Exists

The current landscape has powerful ideas but weak alignment with the Linux desktop:

- many tools are web-first or Electron-heavy
- many are generic AI shells instead of knowledge systems
- many hide the data model behind opaque sync services
- many do not respect GNOME conventions, Linux packaging constraints, or user control

`gknowledge` is meant to close that gap.

It should feel like a real GNOME application:

- coherent with GNOME Human Interface Guidelines
- packaged for Flatpak and distro channels
- integrated with the file system, portals, notifications, and background tasks
- reliable for long-running ingestion and indexing workflows

## Product Mission

The mission of `gknowledge` is to help users build a durable knowledge base from their own material through a workflow of:

1. collecting sources
2. extracting structured knowledge
3. organizing and linking concepts
4. querying and expanding the knowledge base
5. keeping the system aligned with user intent over time

The app should support researchers, engineers, writers, students, analysts, and knowledge workers who need more than search and more than chat.

## Core Product Thesis

`gknowledge` is based on a simple thesis:

> Knowledge work improves when the system does not answer from scratch every time, but incrementally maintains a persistent, inspectable, user-owned knowledge structure.

This leads to a different kind of desktop application:

- source-centric instead of prompt-centric
- incremental instead of stateless
- inspectable instead of opaque
- curated instead of fully automatic
- native and durable instead of disposable

## Design Principles

### 1. Native First

The application should be built for GNOME, not merely shipped on GNOME.

This implies:

- GTK / Libadwaita interface patterns
- responsive layouts for laptop and desktop use
- accessibility from the start
- portal-friendly file, network, and notification flows
- good behavior under Flatpak constraints

### 2. User-Owned Knowledge

Users must be able to understand what the app knows and where that knowledge comes from.

This implies:

- explicit source attribution
- readable exportable formats where possible
- durable project structure
- no forced lock-in to a hosted backend

### 3. LLM as Knowledge Engine, Not Just Chat

The LLM layer should power:

- ingestion
- classification
- summarization
- linking
- contradiction detection
- research expansion
- query assistance

Chat is one interface, not the whole product.

### 4. Human-in-the-Loop by Design

The app should help the user think better, not silently replace editorial judgment.

This implies:

- review queues
- confidence indicators
- editable generated content
- user-controlled approval for major changes

### 5. Strong Separation of Concerns

The system should distinguish clearly between:

- raw sources
- extracted structure
- generated knowledge artifacts
- user-authored notes and corrections
- machine configuration and policies

That separation is essential for trust, debuggability, and long-term maintainability.

## Problem Statement

People accumulate PDFs, notes, bookmarks, documents, transcripts, and snippets across many folders and apps.
Those materials are hard to reuse because:

- they remain fragmented
- relationships between sources are implicit
- search is shallow
- insight depends on memory
- LLM chats lose continuity unless context is reconstructed repeatedly

`gknowledge` should solve this by turning a pile of material into an evolving workspace where the system can:

- ingest sources
- derive entities, themes, concepts, claims, and references
- maintain links across knowledge artifacts
- answer questions against a persistent project memory
- suggest gaps and new directions for research

## Non-Goals

To keep the product focused, `gknowledge` should not start as:

- a general-purpose note-taking replacement for every workflow
- a fully autonomous agent that modifies user data without review
- a cloud-only SaaS product
- a social collaboration platform
- a generic model playground with no knowledge architecture

## Target Users

Primary users:

- technical researchers
- software engineers
- students and academics
- writers and editors
- analysts and independent investigators

Secondary users:

- teams that want a local-first research workstation
- advanced Linux users who want inspectable AI-assisted tooling

## Experience Goals

Using `gknowledge` should feel:

- calm rather than noisy
- structured rather than chaotic
- powerful without looking experimental
- native rather than cross-platform generic
- trustworthy enough for serious long-term projects

## Proposed Feature Set

The list below describes the intended product direction, not a claim of current implementation.

### Source Management

- import folders, files, web captures, and notes into a project
- support common knowledge formats such as Markdown, PDF, text, HTML, and office documents
- watch project sources for changes and reprocess incrementally
- preserve provenance for every extracted or generated artifact

### Incremental Knowledge Ingestion

- parse and normalize raw material
- run LLM-assisted analysis to detect topics, entities, facts, concepts, and open questions
- generate structured knowledge pages from the analysis
- maintain an index of the project knowledge space
- avoid unnecessary reprocessing through hashing and cache-aware ingestion

### Knowledge Graph and Structure

- store relationships between concepts, sources, and generated pages
- expose graph navigation visually and textually
- detect clusters, bridges, gaps, and contradictions
- support both hierarchical and graph-oriented browsing

### Assisted Querying

- query the persistent knowledge base rather than isolated files
- combine lexical retrieval, graph expansion, and optional semantic embeddings
- answer with citations back to project material
- let users save valuable answers as reusable knowledge artifacts

### Research Expansion

- derive missing topics from current knowledge
- propose new searches or sources to ingest
- optionally connect to web research pipelines
- fold the new findings back into the project structure

### Review and Curation

- queue uncertain outputs for human review
- distinguish generated content from user-authored content
- allow users to correct the model and persist those corrections
- preserve a change history for important knowledge artifacts

### GNOME-Native UX

- multi-pane workspace for sources, knowledge, and conversation
- Libadwaita adaptive layout
- background tasks with visible progress
- project-based workflow with recent workspaces
- keyboard-driven navigation for power users

## High-Level Functional Architecture

The product should evolve around the following layers:

### 1. Project Layer

Represents a user workspace and contains:

- source files
- generated knowledge artifacts
- metadata
- settings
- ingestion state
- provider configuration

### 2. Ingestion Layer

Responsible for:

- file detection
- parsing
- normalization
- chunking or segmentation where needed
- change detection
- job queue execution

### 3. Knowledge Extraction Layer

Responsible for:

- LLM prompting and orchestration
- entity and concept extraction
- summary generation
- cross-link suggestion
- confidence scoring
- structured output validation

### 4. Knowledge Store Layer

Stores:

- source metadata
- generated pages
- links between artifacts
- embeddings if enabled
- review items
- history and logs

### 5. Interaction Layer

Includes:

- project browser
- source viewer
- knowledge editor
- graph explorer
- search
- conversational query interface
- review workflows

### 6. Integration Layer

Handles:

- local model backends
- remote LLM providers
- embeddings services
- optional web search providers
- import/export integrations

## Suggested Information Model

At a minimum, the data model should separate:

- `sources/`
- `knowledge/`
- `notes/`
- `reviews/`
- `index/`
- `cache/`
- `settings/`

Possible artifact categories:

- source summaries
- concept pages
- entity pages
- topic pages
- research digests
- saved answers
- review tasks

This structure should remain understandable on disk even as internal capabilities grow.

## UX Direction

The application should follow a workspace model rather than a single chat view.

Suggested main areas:

- sidebar for projects, collections, and navigation
- source pane for raw material browsing
- knowledge pane for synthesized content
- assistant pane for queries, ingest status, and review actions

Important UX behaviors:

- ingest must feel observable, cancelable, and restartable
- generated content must be clearly identifiable
- citations must be easy to inspect
- failures must be debuggable by an advanced user
- the app must remain useful even when a provider is misconfigured or unavailable

## LLM Integration Strategy

`gknowledge` should be provider-agnostic at the application boundary.

The architecture should allow:

- local inference backends
- OpenAI-compatible endpoints
- vendor-specific adapters when needed
- separate models for chat, extraction, and embeddings

Key requirements:

- structured outputs wherever possible
- prompt templates versioned inside the project or application
- retry and fallback behavior
- token and cost visibility
- safe handling of secrets in desktop environments

## Technical Direction

The exact stack is still open, but the product direction suggests:

- GNOME-native UI technology
- strong local storage primitives
- explicit background job orchestration
- packaging strategy aligned with Flatpak and Linux distribution requirements
- clean separation between UI, domain logic, and LLM provider adapters

Important technical qualities:

- deterministic project layout
- resilient job queue
- schema versioning and migrations
- testable ingestion pipeline
- low-friction crash recovery

## Distribution Goals

The application should be designed from the beginning for:

- Flatpak packaging
- compatibility with Ubuntu and major GNOME-friendly distributions
- eventual submission to official or community distribution channels
- minimal environment-specific assumptions

This affects decisions around:

- filesystem access
- secrets management
- background processing
- sandbox compatibility
- bundled versus external runtimes

## Security and Privacy Expectations

Because the app will process personal and professional knowledge, it should treat privacy as a product feature.

Baseline expectations:

- transparent provider usage
- clear distinction between local and remote inference
- no silent upload of user data
- explicit consent around external enrichment or web research
- auditable storage boundaries

## Roadmap

### Phase 0: Product Definition

- define scope, language, and project principles
- formalize the information model
- choose the initial application architecture
- document the provider abstraction strategy

### Phase 1: Native Project Shell

- create the GNOME application shell
- implement project creation and loading
- define on-disk project structure
- establish settings and provider configuration flows

### Phase 2: Source Pipeline

- import and monitor files
- parse initial source formats
- build ingestion queue and job state handling
- persist normalized source metadata

### Phase 3: Knowledge Generation

- implement extraction prompts and structured outputs
- generate first knowledge pages
- maintain index and provenance links
- expose reviewable generated artifacts

### Phase 4: Query Workspace

- add search and conversational querying
- support citations into project artifacts
- persist reusable answers
- improve retrieval with graph-aware ranking

### Phase 5: Graph and Insight Layer

- introduce knowledge graph navigation
- detect clusters and weakly connected regions
- expose contradiction and gap analysis
- support research-expansion workflows

### Phase 6: Hardening and Distribution

- improve performance and recovery
- add migrations and compatibility tests
- package for Flatpak
- prepare for wider GNOME/Linux distribution

## Design Questions Still Open

These questions should guide the next development steps:

- what is the canonical on-disk project format?
- which source formats are in scope for the first usable release?
- should the initial knowledge artifacts be Markdown, SQLite-backed records, or a hybrid model?
- how much of the graph should be materialized versus derived dynamically?
- what is the minimum viable review workflow?
- which GNOME patterns best fit long-running AI jobs without making the UI feel overloaded?
- what is the first distribution target: developer preview, Flathub beta, or direct package builds?

## Development Priorities

If implementation starts immediately, the highest-value order is:

1. define the project format
2. build the native app shell
3. implement source import and persistent ingestion state
4. add one reliable LLM extraction pipeline
5. expose generated knowledge with provenance
6. add query and retrieval workflows

## Contribution Direction

In the early stage, useful contributions are likely to be:

- product architecture proposals
- GNOME UX exploration
- project format design
- ingestion pipeline prototypes
- provider abstraction design
- packaging and distribution strategy

## License

See [LICENSE](../LICENSE).


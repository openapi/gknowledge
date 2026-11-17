"""Two-step, chain-of-thought knowledge extraction.

Step 1 (analysis): read a source → structured analysis (entities, concepts,
topics, key points, open questions).
Step 2 (generation): turn the analysis into wiki pages with provenance and
cross-links, plus review items for human judgement.

Both steps go through the :class:`LLMProvider` interface. For an ``offline``
provider (or when a remote call fails) the pipeline falls back to local
heuristics, so ingestion always produces useful output.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field

from ..providers.base import LLMMessage, LLMProvider, ProviderError
from . import heuristics
from .knowledge import KnowledgeWriter, slugify
from .models import Link, Page, PageKind, ReviewAction, ReviewItem, Source
from .project import Project

MAX_INPUT_CHARS = 16000  # keep prompts bounded; heuristics see the head of long docs


@dataclass
class ExtractionResult:
    pages: list[Page] = field(default_factory=list)
    reviews: list[ReviewItem] = field(default_factory=list)
    analysis: dict = field(default_factory=dict)
    #: Non-empty when the model failed and local heuristics were used instead.
    fallback: str = ""


_ANALYSIS_SYSTEM = (
    "You are a knowledge extraction engine for a personal wiki. Read the source "
    "and return a JSON object with keys: summary (string, 2-4 sentences), "
    "entities (up to 6 objects {{name, description}} for the most important "
    "people, organisations, systems or works), concepts (up to 6 objects "
    "{{name, description}} for the central ideas), topics (up to 3 short theme "
    "names), key_points (string[]), questions (string[], open questions worth "
    "exploring). Each description is one factual sentence based only on the "
    "source. Keep names in their usual spelling and capitalisation (e.g. BERT, "
    "GPT-3). Respond in {lang}."
)

#: Limits per source; anything beyond is listed as a mention, not a page.
MAX_TOPICS, MAX_ENTITIES, MAX_CONCEPTS = 3, 8, 6


def canon(name: str) -> str:
    """Normalised key used to detect duplicate pages.

    "Retrieval-Augmented Generation (RAG)", "retrieval augmented generation"
    and "The Retrieval-Augmented Generation" all map to the same key.
    """
    s = re.sub(r"\([^)]*\)", " ", name.lower())
    s = re.sub(r"[-_/]+", " ", s)
    s = re.sub(r"[^\w\s.+#]", " ", s)
    words = s.split()
    if words and words[0] in ("the", "a", "an"):
        words = words[1:]
    if words:
        last = words[-1]
        if (len(last) > 4 and last.endswith("s")
                and not last.endswith(("ss", "us", "is", "as", "os"))):
            words[-1] = last[:-1]
    return " ".join(words)


def nice_title(name: str) -> str:
    """Capitalise the first letter only; never lowercase the rest (BLEU, GPT-3)."""
    name = " ".join(name.split())
    return name[:1].upper() + name[1:] if name[:1].islower() else name


class ExtractionPipeline:
    def __init__(self, project: Project, provider: LLMProvider):
        self.project = project
        self.provider = provider
        self.writer = KnowledgeWriter(project)
        self.last_fallback = ""

    # -- step 1 --------------------------------------------------------------
    def analyze(self, text: str) -> dict:
        text = text[:MAX_INPUT_CHARS]
        if self.provider.kind == "offline":
            return heuristics.analyze(text)
        lang = self.project.settings.language or "English"
        messages = [
            LLMMessage("system", _ANALYSIS_SYSTEM.format(lang=lang)),
            LLMMessage("user", f"SOURCE:\n{text}"),
        ]
        try:
            resp = self.provider.complete(messages, json_object=True, temperature=0.1)
            data = _parse_json(resp.content)
            self.last_fallback = ""
            return _coerce_analysis(data)
        except (ProviderError, ValueError) as exc:
            # Resilient fallback — never lose the source, but say so.
            self.last_fallback = str(exc) or exc.__class__.__name__
            return heuristics.analyze(text)

    # -- step 2 --------------------------------------------------------------
    def _mentions_path(self):
        return self.project.cache_dir / "mentions.json"

    def _load_mentions(self) -> dict:
        try:
            return json.loads(self._mentions_path().read_text("utf-8"))
        except (OSError, ValueError):
            return {}

    def _save_mentions(self, data: dict) -> None:
        path = self._mentions_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, indent=1, ensure_ascii=False), "utf-8")

    def _source_slug(self, source_id: str) -> str | None:
        for page in self.project.store.pages_for_source(source_id):
            if page.kind == PageKind.SOURCE:
                return page.slug
        return None

    def generate(self, source: Source, analysis: dict, existing_slugs: set[str],
                 text: str = "") -> ExtractionResult:
        """Turn an analysis into pages.

        Pages are created only when they carry real content: a description
        (from the model, or the sentence that mentions the name offline) and
        enough weight (central to the source, or seen in several sources).
        Everything else is recorded as a mention and promoted to a page when a
        second source mentions it. Names that match an existing page after
        normalisation are linked to that page instead of duplicated.
        """
        result = ExtractionResult(analysis=analysis)
        store = self.project.store
        offline = self.provider.kind == "offline"
        own_slug = slugify(source.title) or f"source-{source.id[:6]}"
        by_key = {canon(p.title): p.slug for p in store.list_pages()}
        mentions = self._load_mentions()
        descriptions = analysis.get("descriptions", {})
        sentences = heuristics.sentences(text) if text else []

        links: list[tuple[str, str]] = []        # (slug, title) linked from the source page
        mentioned: list[str] = []                # names kept as plain mentions
        seen: set[str] = {canon(source.title or "")}
        titles = {x.title for x in store.list_sources()} | {source.title or ""}

        def fragment_of_title(key: str) -> bool:
            # "Augmented Generation" from "Retrieval-Augmented Generation",
            # "Attention Is All You" from "Attention Is All You Need". Real
            # names inside a title ("Deep Blue" in "Deep Blue versus
            # Kasparov") are kept.
            for raw_title in titles:
                tk = canon(raw_title)
                if key == tk or f" {key} " not in f" {tk} ":
                    continue
                n, m = len(key.split()), len(tk.split())
                if n == 1 or "-" in raw_title or n / m >= 0.6:
                    return True
            return False

        source_slugs = {canon(x.title): slugify(x.title) for x in store.list_sources()}

        def source_page_for(key: str) -> str | None:
            # "GPT-3" is the title of an imported source; "Chain-of-Thought
            # Prompting Elicits Reasoning..." contains one.
            if key in source_slugs:
                return source_slugs[key]
            return next((slug for k, slug in source_slugs.items()
                         if len(k.split()) >= 2 and f" {k} " in f" {key} "), None)

        def alias_of(key: str) -> str | None:
            # "Kasparov" -> existing "Garry Kasparov".
            if " " in key:
                return None
            return next((slug for k, slug in by_key.items() if k.endswith(" " + key)), None)
        plan = [
            (PageKind.ENTITY, analysis.get("entities", [])[:MAX_ENTITIES]),
            (PageKind.CONCEPT, analysis.get("concepts", [])[:MAX_CONCEPTS]),
            (PageKind.TOPIC, analysis.get("topics", [])[:MAX_TOPICS]),
        ]
        for kind, names in plan:
            for raw in names:
                title = nice_title(raw)
                key = canon(title)
                if not key or key in seen or len(key) < 2:
                    continue
                seen.add(key)
                if fragment_of_title(key):
                    continue
                src_slug = source_page_for(key)
                if src_slug:                             # it is one of the sources
                    if src_slug != own_slug:
                        links.append((src_slug, title))
                    continue
                if key not in by_key and alias_of(key):
                    by_key[key] = alias_of(key)
                if key in by_key:                        # duplicate: link, don't create
                    slug = by_key[key]
                    existing = store.get_page(slug)
                    if existing and existing.kind != PageKind.SOURCE:
                        self.writer.merge_source_into_page(slug, source.id)
                    links.append((slug, existing.title if existing else title))
                    continue

                desc = (descriptions.get(raw) or descriptions.get(title) or "").strip()
                if not desc and offline and kind == PageKind.ENTITY:
                    desc = next((s for s in sentences if raw in s), "")
                prior = [s for s in mentions.get(key, {}).get("sources", [])
                         if s != source.id]
                if offline:
                    # Offline concepts and topics are bare keywords: keep them
                    # as mentions. Named entities need two mentions.
                    central = kind == PageKind.ENTITY and text.count(raw) >= 2
                    promote = kind == PageKind.ENTITY and bool(prior)
                else:
                    central = bool(desc)
                    promote = bool(prior)
                if not (central or promote):
                    entry = mentions.setdefault(key, {"name": title, "kind": kind.value,
                                                      "sources": []})
                    if source.id not in entry["sources"]:
                        entry["sources"].append(source.id)
                    if kind == PageKind.ENTITY or not offline:
                        mentioned.append(title)
                    continue

                src_ids = [*prior, source.id]
                src_slugs = [s for s in (self._source_slug(i) for i in prior) if s]
                src_slugs.append(own_slug)
                body = [f"# {title}", ""]
                body.append(desc or f"Mentioned in {len(src_ids)} sources.")
                body += ["", "## Sources", ""]
                body += [f"- [[{s}]]" for s in dict.fromkeys(src_slugs)]
                page = Page(kind=kind, title=title, slug=slugify(title),
                            summary=(desc or f"Mentioned in {len(src_ids)} sources.")[:280],
                            body="\n".join(body) + "\n", sources=src_ids,
                            confidence=0.7 if desc else 0.5)
                result.pages.append(page)
                by_key[key] = page.slug
                existing_slugs.add(page.slug)
                links.append((page.slug, title))
                mentions.pop(key, None)

        self._save_mentions(mentions)
        # Drop mentions that are only part of a longer one ("Vaswani").
        mentioned = [m for m in mentioned
                     if not any(m != o and f" {m} " in f" {o} " for o in mentioned)]
        analysis = {**analysis, "_links": links, "_mentions": mentioned}
        result.analysis = analysis

        # The source summary page — always created (guaranteed provenance root).
        summary_body = _render_source_summary(source, analysis, links, mentioned)
        source_page = Page(
            kind=PageKind.SOURCE,
            title=source.title or "Untitled source",
            slug=slugify(source.title) or f"source-{source.id[:6]}",
            summary=analysis.get("summary", "")[:280],
            body=summary_body,
            sources=[source.id],
            links=[s for s, _ in links],
            confidence=0.9,
        )
        result.pages.append(source_page)

        # Review items from open questions.
        for q in analysis.get("questions", [])[:3]:
            result.reviews.append(
                ReviewItem(
                    title=q,
                    detail="Open question surfaced during ingestion.",
                    action=ReviewAction.DEEP_RESEARCH,
                    queries=[q],
                    source_id=source.id,
                )
            )
        return result

    # -- orchestration -------------------------------------------------------
    def ingest_source(self, source: Source, text: str) -> ExtractionResult:
        analysis = self.analyze(text)
        existing = {p.slug for p in self.project.store.list_pages()}
        result = self.generate(source, analysis, existing, text)
        result.fallback = self.last_fallback

        source_slug = None
        for page in result.pages:
            saved = self.writer.write_page(page)
            if saved.kind == PageKind.SOURCE:
                source_slug = saved.slug

        # Persist links from the source summary to everything it references.
        if source_slug:
            targets = {s for s, _ in result.analysis.get("_links", [])}
            targets |= {p.slug for p in result.pages if p.slug != source_slug}
            self.project.store.set_links(source_slug,
                                         [Link(source_slug, s) for s in targets])

        for item in result.reviews:
            self.project.store.upsert_review(item)

        self.writer.rebuild_index()
        self.writer.rebuild_overview()
        self.writer.append_log(
            "ingest",
            f"{source.title}: {len(result.pages)} pages, {len(result.reviews)} reviews"
            + (f" (model unavailable, used offline extraction: {result.fallback})"
               if result.fallback else ""),
        )
        return result


# -- helpers -----------------------------------------------------------------
def _render_source_summary(source: Source, analysis: dict,
                           links: list[tuple[str, str]], mentioned: list[str]) -> str:
    parts = [f"# {source.title or 'Untitled source'}", ""]
    if analysis.get("summary"):
        parts += ["## Summary", "", analysis["summary"], ""]
    kp = analysis.get("key_points") or []
    if kp:
        parts += ["## Key points", ""]
        parts += [f"- {p}" for p in kp]
        parts.append("")
    if links:
        parts += ["## In this source", ""]
        parts += [f"- [[{slug}|{title}]]" for slug, title in dict.fromkeys(links)]
        parts.append("")
    if mentioned:
        parts += ["## Also mentioned", "", ", ".join(dict.fromkeys(mentioned)), ""]
    return "\n".join(parts)


def _parse_json(text: str) -> dict:
    text = text.strip()
    # Tolerate code fences around JSON.
    m = re.search(r"\{.*\}", text, re.DOTALL)
    if not m:
        raise ValueError("no JSON object found")
    return json.loads(m.group(0))


def _coerce_analysis(data: dict) -> dict:
    descriptions: dict[str, str] = {}

    def names(key: str) -> list[str]:
        v = data.get(key, [])
        if isinstance(v, (str, dict)):
            v = [v]
        out = []
        for x in v:
            if isinstance(x, dict):
                name = str(x.get("name") or x.get("title") or "").strip()
                desc = str(x.get("description") or "").strip()
                if name and desc:
                    descriptions[name] = desc
            else:
                name = str(x).strip()
            if name:
                out.append(name)
        return out

    return {
        "summary": str(data.get("summary", "")).strip(),
        "entities": names("entities"),
        "concepts": names("concepts"),
        "topics": names("topics"),
        "key_points": names("key_points"),
        "questions": names("questions"),
        "descriptions": descriptions,
    }

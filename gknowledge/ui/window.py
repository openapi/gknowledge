"""Main application window: welcome state + four-pane knowledge workspace."""

from __future__ import annotations

from pathlib import Path

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Adw, Gio, GLib, GObject, Gtk, Pango  # noqa: E402

from .. import APP_NAME, __version__
from ..core.ingestion import IngestionManager
from ..core.knowledge import KnowledgeWriter
from ..core.lint import ChangeDetector
from ..core.models import JobState, PageKind, Source
from ..core.project import Project
from ..core.query import QueryEngine
from ..providers import build_provider
from .markdown import MarkdownView
from .preferences import PreferencesDialog

_KIND_ORDER = [PageKind.SOURCE, PageKind.ENTITY, PageKind.CONCEPT, PageKind.TOPIC,
               PageKind.SYNTHESIS, PageKind.ANSWER]
_KIND_LABEL = {PageKind.SOURCE: "Sources", PageKind.ENTITY: "People, organisations and works",
               PageKind.CONCEPT: "Concepts", PageKind.TOPIC: "Topics",
               PageKind.SYNTHESIS: "Syntheses", PageKind.ANSWER: "Saved answers"}


def _kind_header(row, before):
    page = getattr(row, "page", None)
    prev = getattr(before, "page", None) if before else None
    if page and (prev is None or prev.kind != page.kind):
        label = Gtk.Label(label=_KIND_LABEL.get(page.kind, page.kind.value), xalign=0,
                          margin_start=12, margin_top=12 if before else 4, margin_bottom=4)
        label.add_css_class("heading")
        label.add_css_class("dim-label")
        row.set_header(label)
    else:
        row.set_header(None)


def _iter_rows(listbox):
    child = listbox.get_first_child()
    while child is not None:
        yield child
        child = child.get_next_sibling()


_KIND_ICON = {
    PageKind.SOURCE: "text-x-generic-symbolic",
    PageKind.ENTITY: "avatar-default-symbolic",
    PageKind.CONCEPT: "emblem-documents-symbolic",
    PageKind.TOPIC: "view-list-symbolic",
    PageKind.ANSWER: "help-about-symbolic",
    PageKind.SYNTHESIS: "view-grid-symbolic",
}


class MainWindow(Adw.ApplicationWindow):
    """Nautilus-style window.

    A full-height sidebar (own header bar, own controls) sits next to the
    content pane (own header bar, title centred on the content, not on the
    window). Sections live in the sidebar; lists push detail pages instead of
    using a draggable split.
    """

    SECTIONS = [
        ("sources", "Sources", "folder-symbolic"),
        ("knowledge", "Knowledge", "emblem-documents-symbolic"),
        ("assistant", "Assistant", "user-info-symbolic"),
        ("review", "Review", "emblem-important-symbolic"),
    ]

    def __init__(self, app: Adw.Application):
        super().__init__(application=app)
        self.app = app
        self.project: Project | None = None
        self.ingestion: IngestionManager | None = None
        self.changes: ChangeDetector | None = None
        self._stale_ids: set[str] = set()
        # Sources are often edited in another app: look for drift on return.
        self.connect("notify::is-active", self._on_active_changed)
        self._selected_source_id: str | None = None
        self.provider = None

        self.set_title(APP_NAME)
        self.set_default_size(1180, 760)

        self.toasts = Adw.ToastOverlay()
        self.set_content(self.toasts)

        self.main_stack = Gtk.Stack(transition_type=Gtk.StackTransitionType.CROSSFADE)
        self.toasts.set_child(self.main_stack)
        self.main_stack.add_named(self._build_welcome(), "welcome")
        self.main_stack.add_named(self._build_workspace(), "workspace")
        self.main_stack.set_visible_child_name("welcome")

        self._add_win_action("import-files", self._on_import_files)
        self._add_win_action("import-folder", self._on_import_folder)
        self._add_win_action("ingest", self._on_ingest)

    def _add_win_action(self, name, cb):
        action = Gio.SimpleAction.new(name, None)
        action.connect("activate", cb)
        self.add_action(action)

    # -- chrome --------------------------------------------------------------
    @staticmethod
    def _primary_menu() -> Gio.Menu:
        menu = Gio.Menu()
        menu.append("New Project…", "app.new-project")
        menu.append("Open Project…", "app.open-project")
        menu.append("Preferences", "app.preferences")
        menu.append("About gknowledge", "app.about")
        menu.append("Quit", "app.quit")
        return menu

    def _build_welcome(self) -> Gtk.Widget:
        status = Adw.StatusPage(
            icon_name="accessories-dictionary-symbolic",
            title="gknowledge",
            description="Turn your documents, notes and links into an evolving, "
                        "inspectable knowledge base.",
        )
        box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12,
                      halign=Gtk.Align.CENTER)
        new_btn = Gtk.Button(label="New Project…")
        new_btn.add_css_class("suggested-action")
        new_btn.add_css_class("pill")
        new_btn.connect("clicked", lambda *_: self.app.activate_action("new-project"))
        open_btn = Gtk.Button(label="Open Project…")
        open_btn.add_css_class("pill")
        open_btn.connect("clicked", lambda *_: self.app.activate_action("open-project"))
        box.append(new_btn)
        box.append(open_btn)
        status.set_child(box)

        view = Adw.ToolbarView()
        header = Adw.HeaderBar()
        header.pack_end(Gtk.MenuButton(icon_name="open-menu-symbolic",
                                       menu_model=self._primary_menu()))
        view.add_top_bar(header)
        view.set_content(status)
        return view

    def _build_workspace(self) -> Gtk.Widget:
        """Full-height sidebar (own header, section-specific objects) next to
        a content pane whose header carries the four section tabs."""
        # Sidebar ---------------------------------------------------------
        self.sidebar_title = Adw.WindowTitle(title=APP_NAME, subtitle="")
        side_header = Adw.HeaderBar(show_end_title_buttons=False,
                                    title_widget=self.sidebar_title)
        add_menu = Gio.Menu()
        add_menu.append("Import Files…", "win.import-files")
        add_menu.append("Import Folder…", "win.import-folder")
        side_header.pack_start(Gtk.MenuButton(
            icon_name="list-add-symbolic", menu_model=add_menu,
            tooltip_text="Add sources"))
        side_header.pack_end(Gtk.MenuButton(
            icon_name="open-menu-symbolic", menu_model=self._primary_menu(),
            primary=True, tooltip_text="Main menu"))

        self.side_stack = Gtk.Stack(transition_type=Gtk.StackTransitionType.CROSSFADE)
        side_view = Adw.ToolbarView()
        side_view.add_css_class("gk-sidebar")
        side_view.add_top_bar(side_header)
        side_view.set_content(self.side_stack)

        # Content ---------------------------------------------------------
        self.view_stack = Adw.ViewStack()
        self.view_stack.connect("notify::visible-child-name", self._sync_sidebar)
        self.view_switcher = Adw.ViewSwitcher(stack=self.view_stack,
                                              policy=Adw.ViewSwitcherPolicy.WIDE)
        header = Adw.HeaderBar(show_start_title_buttons=False,
                               title_widget=self.view_switcher)
        content_view = Adw.ToolbarView()
        content_view.add_css_class("gk-content-pane")
        content_view.add_top_bar(header)
        self.banner = Adw.Banner(revealed=False, button_label="Preferences")
        self.banner.connect("button-clicked", lambda *_: self.open_preferences())
        content_view.add_top_bar(self.banner)
        content_view.set_content(self.view_stack)

        self.split = Adw.OverlaySplitView(
            sidebar=side_view, content=content_view,
            show_sidebar=True, pin_sidebar=False,
            min_sidebar_width=240, max_sidebar_width=340,
            sidebar_width_fraction=0.26)
        try:
            bp = Adw.Breakpoint.new(Adw.BreakpointCondition.parse("max-width: 640sp"))
            bp.add_setter(self.split, "collapsed", True)
            self.add_breakpoint(bp)
        except Exception:  # noqa: BLE001  (older libadwaita)
            pass

        toggle = Gtk.ToggleButton(icon_name="sidebar-show-symbolic",
                                  tooltip_text="Toggle sidebar")
        self.split.bind_property("collapsed", toggle, "visible",
                                 GObject.BindingFlags.SYNC_CREATE)
        self.split.bind_property("show-sidebar", toggle, "active",
                                 GObject.BindingFlags.SYNC_CREATE |
                                 GObject.BindingFlags.BIDIRECTIONAL)
        header.pack_start(toggle)
        return self.split

    def _sync_sidebar(self, *_a):
        name = self.view_stack.get_visible_child_name()
        if name and self.side_stack.get_child_by_name(name):
            self.side_stack.set_visible_child_name(name)

    def _sidebar_list(self, handler) -> Gtk.ListBox:
        lb = Gtk.ListBox(css_classes=["navigation-sidebar"],
                         selection_mode=Gtk.SelectionMode.BROWSE)
        lb.connect("row-activated", handler)
        return lb

    def _detail_area(self, icon: str, empty_title: str, empty_text: str):
        """Placeholder until something is selected, then rendered Markdown."""
        tv = MarkdownView(on_link=self._open_link, resolve=self._resolve_slug)
        stack = Gtk.Stack()
        stack.add_named(Adw.StatusPage(icon_name=icon, title=empty_title,
                                       description=empty_text), "empty")
        stack.add_named(Gtk.ScrolledWindow(child=tv, vexpand=True, hexpand=True),
                        "detail")
        return stack, tv

    @staticmethod
    def _show_detail(stack: Gtk.Stack, tv, text: str, meta: str = ""):
        tv.set_markdown(text, meta=meta)
        stack.set_visible_child_name("detail")
        tv.get_parent().get_vadjustment().set_value(0)

    # -- links -----------------------------------------------------------------
    def _resolve_slug(self, slug: str) -> str | None:
        if not self.project:
            return None
        page = self.project.store.get_page(slug)
        return page.title if page else None

    def _open_link(self, target: str):
        kind, _, value = target.partition(":")
        if kind == "url":
            Gtk.UriLauncher.new(value).launch(self, None, None, None)
            return
        if kind == "cite":
            value = self._cite_slugs.get(int(value), "")
        page = self.project.store.get_page(value) if (self.project and value) else None
        if not page:
            self.toast("That page does not exist yet")
            return
        self.view_stack.set_visible_child_name("knowledge")
        self.knowledge_search.set_text("")
        for row in _iter_rows(self.knowledge_list):
            if getattr(row, "page", None) and row.page.slug == page.slug:
                self.knowledge_list.select_row(row)
                break
        self._show_page(page)

    def _show_page(self, page):
        writer = KnowledgeWriter(self.project)
        body = writer.read_body(page)
        lines = body.splitlines()
        if lines and lines[0].lstrip("# ").strip() == page.title:
            lines = lines[1:]
        n = len(page.sources)
        meta = (f"{page.kind.value.capitalize()} · {n} source{'s' if n != 1 else ''}"
                + (" · generated" if page.generated else ""))
        backlinks = sorted({l.from_slug for l in self.project.store.all_links()
                            if l.to_slug == page.slug and l.from_slug != page.slug})
        text = f"# {page.title}\n" + "\n".join(lines)
        if backlinks:
            text += "\n\n## Linked from\n" + "\n".join(f"- [[{s}]]" for s in backlinks)
        self._show_detail(self.page_stack, self.page_detail, text, meta)

    def _add_section(self, name, title, icon, sidebar: Gtk.Widget, content: Gtk.Widget):
        self.side_stack.add_named(sidebar, name)
        page = self.view_stack.add_titled_with_icon(content, name, title, icon)
        self._section_pages[name] = page

    # -- project lifecycle ---------------------------------------------------
    def set_project(self, project: Project):
        if self.project:
            self.project.close()
        self._selected_source_id = None
        self.project = project
        self.provider = build_provider(project.settings.as_dict())
        self.ingestion = IngestionManager(project, self.provider)
        self.changes = ChangeDetector(project)

        for stack in (self.side_stack, self.view_stack):
            while (child := stack.get_first_child()) is not None:
                stack.remove(child)
        self._section_pages = {}

        for name, title, icon, builder in (
            ("sources", "Sources", "folder-symbolic", self._build_sources_pane),
            ("knowledge", "Knowledge", "emblem-documents-symbolic",
             self._build_knowledge_pane),
            ("assistant", "Assistant", "user-info-symbolic",
             self._build_assistant_pane),
            ("review", "Review", "emblem-important-symbolic",
             self._build_review_pane),
        ):
            sidebar, content = builder()
            self._add_section(name, title, icon, sidebar, content)

        self.set_title(f"{project.name} — {APP_NAME}")
        self.sidebar_title.set_title(project.name)
        self.sidebar_title.set_subtitle(self.provider.name)
        self.main_stack.set_visible_child_name("workspace")
        self.refresh_all()
        self.view_stack.set_visible_child_name("sources")
        self._sync_sidebar()
        self._announce_stale()

    def on_settings_saved(self, settings):
        if self.project:
            self.provider = build_provider(settings.as_dict())
            self.ingestion.set_provider(self.provider)
            self.sidebar_title.set_subtitle(self.provider.name)
            self.toast("Provider updated")

    def refresh_all(self):
        self._refresh_sources()
        self._refresh_knowledge()
        self._refresh_reviews()
        self._refresh_answers()
        self._update_counts()

    def _update_counts(self):
        if not self.project:
            return
        store = self.project.store
        counts = {"sources": len(store.list_sources()),
                  "knowledge": len(store.list_pages()),
                  "review": len(store.list_reviews(status="open"))}
        for name, n in counts.items():
            page = self._section_pages.get(name)
            if page is not None:
                page.set_badge_number(n)

    # -- sources pane --------------------------------------------------------
    def _build_sources_pane(self):
        self.sources_list = self._sidebar_list(self._on_source_selected)

        self.ingest_btn = Gtk.Button(label="Ingest Queued")
        self.ingest_btn.add_css_class("suggested-action")
        self.ingest_btn.set_action_name("win.ingest")
        self.reingest_btn = Gtk.Button(label="Re-ingest")
        self.reingest_btn.set_sensitive(False)
        self.reingest_btn.connect("clicked", self._on_reingest_source)
        self.remove_source_btn = Gtk.Button(label="Remove")
        self.remove_source_btn.add_css_class("destructive-action")
        self.remove_source_btn.set_sensitive(False)
        self.remove_source_btn.connect("clicked", self._on_remove_source)
        source_actions = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        source_actions.append(self.reingest_btn)
        source_actions.append(self.remove_source_btn)
        self.progress = Gtk.ProgressBar(show_text=True, visible=False)
        bottom = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8,
                         margin_top=8, margin_bottom=8, margin_start=8, margin_end=8)
        bottom.append(source_actions)
        bottom.append(self.progress)
        bottom.append(self.ingest_btn)

        side = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        side.append(Gtk.ScrolledWindow(child=self.sources_list, vexpand=True,
                                       hscrollbar_policy=Gtk.PolicyType.NEVER))
        side.append(Gtk.Separator())
        side.append(bottom)

        self.source_stack, self.source_detail = self._detail_area(
            "folder-symbolic", "No source selected",
            "Pick a source on the left, or add some with the + button.")
        return side, self.source_stack

    def _refresh_sources(self):
        _clear_listbox(self.sources_list)
        if not self.project:
            self._selected_source_id = None
            self._update_source_action_buttons()
            return
        sources = self.project.store.list_sources()
        self._stale_ids = self._find_stale()
        selected_row = None
        if not sources:
            self.sources_list.append(_placeholder_row("No sources yet. Import some."))
        for s in sources:
            stale = s.id in self._stale_ids
            row = Adw.ActionRow(activatable=True, title=GLib.markup_escape_text(s.title),
                                subtitle="changed since ingest" if stale
                                else s.status.value)
            row.add_prefix(Gtk.Image.new_from_icon_name(
                "dialog-warning-symbolic" if stale else "text-x-generic-symbolic"))
            row.source = s
            self.sources_list.append(row)
            if s.id == self._selected_source_id:
                selected_row = row
        if selected_row:
            self.sources_list.select_row(selected_row)
            self._on_source_selected(self.sources_list, selected_row)
        else:
            self._selected_source_id = None
            self.source_stack.set_visible_child_name("empty")
            self._update_source_action_buttons()
        self._update_ingest_button()

    def _on_source_selected(self, _list, row):
        source: Source | None = getattr(row, "source", None)
        if not source or not self.project:
            return
        self._selected_source_id = source.id
        pages = self.project.store.pages_for_source(source.id)
        writer = KnowledgeWriter(self.project)
        summary = next((p for p in pages if p.kind == PageKind.SOURCE), None)
        if summary:
            body = writer.read_body(summary)
            body += f"\n\n## Original file\n- [{source.rel_path}](file://{self.project.sources_dir / source.rel_path})"
        else:
            fp = self.project.sources_dir / source.rel_path
            from ..core import parsers
            body = (f"# {source.title}\n\n(Not yet ingested.)\n\n"
                    + parsers.parse(fp)[:4000])
        self._show_detail(self.source_stack, self.source_detail, body)
        self._update_source_action_buttons()

    def _update_source_action_buttons(self):
        available = bool(
            self._selected_source_id and self.project and self.ingestion
            and not self.ingestion.is_running()
        )
        if hasattr(self, "reingest_btn"):
            self.reingest_btn.set_sensitive(available)
            stale = self._selected_source_id in self._stale_ids
            self.reingest_btn.set_label("Update" if stale else "Re-ingest")
            self.reingest_btn.set_tooltip_text(
                "The original file changed: ingest the new version" if stale
                else "Extract this source again")
        if hasattr(self, "remove_source_btn"):
            self.remove_source_btn.set_sensitive(available)

    def _update_ingest_button(self):
        if not self.project:
            return
        pending = [j for j in self.project.store.pending_jobs()
                   if j.state != JobState.FAILED]
        n = len(pending)
        self.ingest_btn.set_label(f"Ingest Queued ({n})" if n else "Ingest Queued")
        self.ingest_btn.set_sensitive(n > 0 and not self.ingestion.is_running())
        self._update_source_action_buttons()

    # -- knowledge pane ------------------------------------------------------
    def _build_knowledge_pane(self):
        self.knowledge_list = self._sidebar_list(self._on_page_selected)
        self.knowledge_search = Gtk.SearchEntry(placeholder_text="Search pages",
                                                margin_top=6, margin_bottom=6,
                                                margin_start=8, margin_end=8)
        self.knowledge_search.connect(
            "search-changed", lambda *_: self.knowledge_list.invalidate_filter())

        def matches(row):
            q = self.knowledge_search.get_text().strip().lower()
            page = getattr(row, "page", None)
            return not q or page is None or q in page.title.lower()

        self.knowledge_list.set_filter_func(matches)
        self.knowledge_list.set_header_func(_kind_header)
        side = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        side.append(self.knowledge_search)
        side.append(Gtk.ScrolledWindow(child=self.knowledge_list, vexpand=True,
                                       hscrollbar_policy=Gtk.PolicyType.NEVER))
        self.page_stack, self.page_detail = self._detail_area(
            "emblem-documents-symbolic", "No page selected",
            "Pages generated from your sources appear on the left.")
        return side, self.page_stack

    def _refresh_knowledge(self):
        _clear_listbox(self.knowledge_list)
        if not self.project:
            return
        pages = self.project.store.list_pages()
        if not pages:
            self.knowledge_list.append(
                _placeholder_row("No knowledge yet. Ingest a source."))
            return
        order = {k: i for i, k in enumerate(_KIND_ORDER)}
        pages.sort(key=lambda p: (order.get(p.kind, 99), p.title.lower()))
        for p in pages:
            row = Adw.ActionRow(activatable=True, title=GLib.markup_escape_text(p.title), title_lines=1,
                                tooltip_text=p.title)
            row.add_prefix(Gtk.Image.new_from_icon_name(
                _KIND_ICON.get(p.kind, "text-x-generic-symbolic")))
            row.page = p
            self.knowledge_list.append(row)

    def _on_page_selected(self, _list, row):
        page = getattr(row, "page", None)
        if not page or not self.project:
            return
        self._show_page(page)

    # -- assistant pane ------------------------------------------------------
    def _build_assistant_pane(self):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8,
                      margin_top=8, margin_bottom=8, margin_start=8, margin_end=8)
        self._cite_slugs: dict[int, str] = {}
        self.answer_view = MarkdownView(on_link=self._open_link, resolve=self._resolve_slug)
        self.answer_view.set_markdown(
            "## Ask your knowledge base\nQuestions are answered from your wiki, "
            "and every answer cites the pages it used. Click a citation to open it.")
        box.append(Gtk.ScrolledWindow(child=self.answer_view, vexpand=True))

        self.citations_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2,
                                     margin_start=20)
        box.append(self.citations_box)

        entry_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        self.query_entry = Gtk.Entry(hexpand=True,
                                     placeholder_text="Ask your knowledge base…")
        self.query_entry.connect("activate", self._on_ask)
        ask_btn = Gtk.Button(label="Ask")
        ask_btn.add_css_class("suggested-action")
        ask_btn.connect("clicked", self._on_ask)
        self.save_answer_btn = Gtk.Button(label="Save to Wiki", sensitive=False)
        self.save_answer_btn.connect("clicked", self._on_save_answer)
        entry_row.append(self.query_entry)
        entry_row.append(ask_btn)
        entry_row.append(self.save_answer_btn)
        box.append(entry_row)
        self._last_query = None
        self._last_result = None
        self.answers_list = self._sidebar_list(self._on_answer_selected)
        side = Gtk.ScrolledWindow(child=self.answers_list, vexpand=True,
                                  hscrollbar_policy=Gtk.PolicyType.NEVER)
        return side, box

    def _refresh_answers(self):
        _clear_listbox(self.answers_list)
        if not self.project:
            return
        answers = [p for p in self.project.store.list_pages()
                   if p.kind == PageKind.ANSWER]
        if not answers:
            self.answers_list.append(_placeholder_row("No saved answers yet."))
            return
        for p in answers:
            row = Adw.ActionRow(activatable=True, title=GLib.markup_escape_text(p.title),
                                subtitle="saved answer")
            row.add_prefix(Gtk.Image.new_from_icon_name("help-about-symbolic"))
            row.page = p
            self.answers_list.append(row)

    def _on_answer_selected(self, _list, row):
        page = getattr(row, "page", None)
        if not page or not self.project:
            return
        _clear_box(self.citations_box)
        self._cite_slugs = {i + 1: s for i, s in enumerate(page.links)}
        self.answer_view.set_markdown(KnowledgeWriter(self.project).read_body(page))

    def _on_ask(self, *_a):
        if not self.project:
            return
        question = self.query_entry.get_text().strip()
        if not question:
            return
        self.answer_view.set_markdown(f"## {question}\n*Thinking…*")
        engine = QueryEngine(self.project, self.provider)

        def work():
            result = engine.query(question)

            def show():
                self._cite_slugs = {c.number: c.slug for c in result.citations}
                self.answer_view.set_markdown(f"## {question}\n{result.answer}")
                _clear_box(self.citations_box)
                for c in result.citations:
                    lbl = Gtk.Label(label=f"[{c.number}]  {c.title} · {c.kind}", xalign=0,
                                    ellipsize=Pango.EllipsizeMode.END)
                    lbl.add_css_class("caption")
                    btn = Gtk.Button(child=lbl, halign=Gtk.Align.START)
                    btn.add_css_class("flat")
                    btn.add_css_class("gk-cite")
                    btn.connect("clicked", lambda _b, s=c.slug: self._open_link(f"page:{s}"))
                    self.citations_box.append(btn)
                if result.warning:
                    self._warn(result.warning)
                self._last_query = question
                self._last_result = result
                self.save_answer_btn.set_sensitive(bool(result.pages))
                return False

            GLib.idle_add(show)

        import threading
        threading.Thread(target=work, daemon=True).start()

    def _on_save_answer(self, *_a):
        if not (self.project and self._last_result and self._last_query):
            return
        engine = QueryEngine(self.project, self.provider)
        engine.save_answer(self._last_query, self._last_result)
        self._refresh_knowledge()
        self._refresh_answers()
        self._update_counts()
        self.toast("Answer saved to knowledge base")

    # -- review pane ---------------------------------------------------------
    def _build_review_pane(self):
        self.review_list = self._sidebar_list(self._on_review_selected)
        side = Gtk.ScrolledWindow(child=self.review_list, vexpand=True,
                                  hscrollbar_policy=Gtk.PolicyType.NEVER)
        self.review_stack, self.review_detail = self._detail_area(
            "emblem-important-symbolic", "Nothing selected",
            "Items the system wants you to check appear on the left.")
        return side, self.review_stack

    def _on_review_selected(self, _list, row):
        item = getattr(row, "item", None)
        if not item:
            return
        self._show_detail(self.review_stack, self.review_detail,
                          f"# {item.title}\n\n_{item.action.value}_\n\n{item.detail}")

    def _refresh_reviews(self):
        _clear_listbox(self.review_list)
        if not self.project:
            return
        items = self.project.store.list_reviews(status="open")
        if not items:
            self.review_list.append(_placeholder_row("No items awaiting review."))
            return
        for item in items:
            row = Adw.ActionRow(
                activatable=True,
                title=GLib.markup_escape_text(item.title),
                subtitle=f"{item.action.value} · {item.detail}")
            btn = Gtk.Button(label="Resolve", valign=Gtk.Align.CENTER)
            btn.connect("clicked", self._on_resolve, item.id)
            row.add_suffix(btn)
            row.item = item
            self.review_list.append(row)

    def _on_resolve(self, _btn, review_id):
        self.project.store.resolve_review(review_id)
        self._refresh_reviews()
        self._update_counts()
        self.toast("Review resolved")

    # -- import / ingest actions --------------------------------------------
    def _on_import_files(self, *_a):
        dialog = Gtk.FileDialog(title="Import files")

        def done(dlg, res):
            try:
                files = dlg.open_multiple_finish(res)
            except GLib.Error:
                return
            paths = [files.get_item(i).get_path() for i in range(files.get_n_items())]
            self._do_import(paths)

        dialog.open_multiple(self, None, done)

    def _on_import_folder(self, *_a):
        dialog = Gtk.FileDialog(title="Import folder")

        def done(dlg, res):
            try:
                folder = dlg.select_folder_finish(res)
            except GLib.Error:
                return
            self._do_import_folder(folder.get_path())

        dialog.select_folder(self, None, done)

    def _do_import(self, paths):
        imported = 0
        for p in paths:
            if self.ingestion.import_file(p):
                imported += 1
        self._refresh_sources()
        self.toast(f"Imported {imported} file(s)" if imported
                   else "Nothing imported (duplicates?)")

    def _do_import_folder(self, folder):
        outcome = self.ingestion.import_folder(folder)
        self._refresh_sources()
        self.toast(f"Imported {len(outcome.imported)}, "
                   f"skipped {len(outcome.skipped)} duplicate(s)")

    def _on_reingest_source(self, *_a):
        if not (self.project and self.ingestion and self._selected_source_id):
            return
        source_id = self._selected_source_id
        try:
            if source_id in self._stale_ids:
                source = self.ingestion.refresh_source(source_id)
            else:
                source = self.ingestion.reingest_source(source_id)
        except (OSError, RuntimeError, ValueError) as exc:
            self.toast(f"Could not re-ingest source: {exc}")
            return
        if source is None:
            self.toast("That source no longer exists.")
            self.refresh_all()
            return
        self.refresh_all()
        self.toast(f"Re-ingesting {source.title}")
        self._on_ingest()

    def _on_remove_source(self, *_a):
        if not (self.project and self.ingestion and self._selected_source_id):
            return
        source = self.project.store.get_source(self._selected_source_id)
        if source is None:
            self.toast("That source no longer exists.")
            self.refresh_all()
            return
        dialog = Adw.MessageDialog(
            transient_for=self,
            heading="Remove source?",
            body=f"Remove “{source.title}” and detach it from generated knowledge pages?",
        )
        dialog.add_response("cancel", "Cancel")
        dialog.add_response("remove", "Remove")
        dialog.set_default_response("cancel")
        dialog.set_close_response("cancel")
        dialog.set_response_appearance("remove", Adw.ResponseAppearance.DESTRUCTIVE)
        dialog.connect(
            "response",
            lambda _dialog, response: self._remove_source(source.id)
            if response == "remove" else None,
        )
        dialog.present()

    def _remove_source(self, source_id: str):
        if not (self.project and self.ingestion):
            return
        try:
            source = self.ingestion.remove_source(source_id)
        except (OSError, RuntimeError, ValueError) as exc:
            self.toast(f"Could not remove source: {exc}")
            return
        if source is None:
            self.toast("That source no longer exists.")
            self.refresh_all()
            return
        self._selected_source_id = None
        self.source_stack.set_visible_child_name("empty")
        self.refresh_all()
        self.toast(f"Removed source: {source.title}")

    def _on_ingest(self, *_a):
        if not self.ingestion or self.ingestion.is_running():
            return
        self.progress.set_visible(True)
        self.progress.set_fraction(0.0)
        self.ingest_btn.set_sensitive(False)

        def progress(event, job, message):
            def update():
                if event == "start":
                    self.progress.set_text(f"Ingesting: {message}")
                    self.progress.pulse()
                elif event == "done":
                    self.progress.pulse()
                elif event == "error":
                    self.toast(f"Failed: {message}")
                elif event == "warning":
                    self._warn(f"Model unavailable, used offline extraction for {message}")
                return False
            GLib.idle_add(update)

        def finished(count):
            def done():
                self.progress.set_visible(False)
                self.refresh_all()
                self.toast(f"Ingested {count} source(s)")
                self._update_ingest_button()
                return False
            GLib.idle_add(done)

        self.ingestion.start(progress=progress, on_finish=finished)
        self._update_source_action_buttons()

    # -- drift ---------------------------------------------------------------
    def _find_stale(self) -> set[str]:
        if not self.changes:
            return set()
        return {s.source.id for s in self.changes.stale_sources()}

    def _announce_stale(self):
        n = len(self._stale_ids)
        if n:
            self.toast(f"{n} source(s) changed since they were ingested")

    def _on_active_changed(self, *_a):
        if not (self.is_active() and self.project and self.ingestion
                and not self.ingestion.is_running()):
            return
        if self._find_stale() != self._stale_ids:
            self._refresh_sources()
            self._announce_stale()

    # -- helpers -------------------------------------------------------------
    def _warn(self, text: str):
        self.banner.set_title(GLib.markup_escape_text(text[:240]))
        self.banner.set_revealed(True)

    def toast(self, text: str):
        self.toasts.add_toast(Adw.Toast(title=text, timeout=3))

    def open_preferences(self):
        if not self.project:
            self.toast("Open a project first")
            return
        dlg = PreferencesDialog(self, self.project, self.on_settings_saved)
        dlg.present()


# -- module-level widget helpers ---------------------------------------------
def _make_text_view() -> Gtk.TextView:
    tv = Gtk.TextView(editable=False, cursor_visible=False,
                      wrap_mode=Gtk.WrapMode.WORD_CHAR,
                      left_margin=12, right_margin=12, top_margin=12, bottom_margin=12)
    tv.add_css_class("gk-content")
    return tv


def _set_text(tv: Gtk.TextView, text: str):
    tv.get_buffer().set_text(text or "")


def _clear_listbox(lb: Gtk.ListBox):
    while (child := lb.get_first_child()) is not None:
        lb.remove(child)


def _clear_box(box: Gtk.Box):
    while (child := box.get_first_child()) is not None:
        box.remove(child)


def _placeholder_row(text: str) -> Gtk.ListBoxRow:
    row = Gtk.ListBoxRow(activatable=False, selectable=False)
    row.set_child(Gtk.Label(label=text, css_classes=["dim-label"],
                            margin_top=18, margin_bottom=18))
    return row

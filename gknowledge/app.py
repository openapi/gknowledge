"""Adwaita application: window lifecycle, global actions, project loading."""

from __future__ import annotations

from pathlib import Path

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Adw, Gdk, Gio, Gtk  # noqa: E402

from . import APP_ID, APP_NAME, __version__, config
from .core.project import Project, default_home
from .ui.window import MainWindow


class GknowledgeApp(Adw.Application):
    def __init__(self):
        super().__init__(application_id=APP_ID,
                         flags=Gio.ApplicationFlags.HANDLES_OPEN)
        self.window: MainWindow | None = None
        self._pending_open: str | None = None
        self._pending_import: list[str] = []

        self._add_action("new-dossier", self._on_new_dossier, "<primary>n")
        self._add_action("open-dossier", self._on_open_dossier, "<primary>o")
        self._add_action("save-dossier", self._on_save_dossier, "<primary>s")
        self.lookup_action("save-dossier").set_enabled(False)
        self._add_action("preferences", self._on_preferences, "<primary>comma")
        self._add_action("about", self._on_about)
        self._add_action("quit", self._on_quit, "<primary>q")

    def _add_action(self, name, cb, accel=None):
        action = Gio.SimpleAction.new(name, None)
        action.connect("activate", cb)
        self.add_action(action)
        if accel:
            self.set_accels_for_action(f"app.{name}", [accel])

    # -- lifecycle -----------------------------------------------------------
    def do_startup(self):
        Adw.Application.do_startup(self)
        self._load_css()

    def do_activate(self):
        if not self.window:
            self.window = MainWindow(self)
        self.window.present()
        if self._pending_open:
            path, self._pending_open = self._pending_open, None
            self.window.confirm_leave(lambda: self._open_path(path))
        else:
            self._maybe_open_last()
        # Files handed over by the file manager ("Open With") are imported
        # into the current project, like gedit opening files into a window.
        if self._pending_import:
            paths, self._pending_import = self._pending_import, []
            if self.window.project:
                self.window._do_import(paths)
            else:
                self.window.toast("Open or create a dossier first, then import the files.")

    def do_open(self, files, n_files, hint):
        # `gknowledge /path/to/dossier` (the folder or its .dossier launcher)
        # opens it; other files are imported as sources into the current one.
        for gfile in files[:n_files]:
            path = gfile.get_path()
            if not path:
                continue
            if Project.is_project(path):
                self._pending_open = path
            elif Path(path).is_file():
                self._pending_import.append(path)
        self.activate()

    def _load_css(self):
        css = Path(__file__).parent / "ui" / "style.css"
        display = Gdk.Display.get_default()
        if css.exists() and display is not None:
            provider = Gtk.CssProvider()
            provider.load_from_path(str(css))
            Gtk.StyleContext.add_provider_for_display(
                display, provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
            )

    def _maybe_open_last(self):
        recent = config.recent_projects()
        if recent:
            self._open_path(recent[0])

    # -- project actions -----------------------------------------------------
    def _open_path(self, path: str):
        try:
            project = Project.open(path)
            path = str(project.root)
        except Exception as exc:  # noqa: BLE001
            self.window.toast(f"Could not open the dossier: {exc}")
            return
        config.add_recent_project(str(Path(path).resolve()))
        self.window.set_project(project)

    def _on_new_dossier(self, *_a):
        def create(name: str):
            try:
                project = Project.create_draft(name)
            except Exception as exc:  # noqa: BLE001
                self.window.toast(f"Could not create the dossier: {exc}")
                return
            config.add_recent_project(str(project.root.resolve()))
            self.window.set_project(project)

        self.window.confirm_leave(lambda: self.window.ask_dossier_name(create))

    def _on_open_dossier(self, *_a):
        dialog = Gtk.FileDialog(title="Open a Dossier")
        filters = Gio.ListStore.new(Gtk.FileFilter)
        dossiers = Gtk.FileFilter(name="Dossiers")
        dossiers.add_pattern("*.dossier")
        dossiers.add_pattern("gknowledge.json")  # created before 0.4
        filters.append(dossiers)
        dialog.set_filters(filters)
        dialog.set_default_filter(dossiers)
        home = default_home()
        if home.is_dir():
            dialog.set_initial_folder(Gio.File.new_for_path(str(home)))

        def done(dlg, res):
            try:
                gfile = dlg.open_finish(res)
            except Exception:
                return
            path = gfile.get_path()
            if not Project.is_project(path):
                self.window.toast("That file does not open a dossier.")
                return
            self._open_path(path)

        self.window.confirm_leave(lambda: dialog.open(self.window, None, done))

    def _on_save_dossier(self, *_a):
        if self.window:
            self.window.save_draft()

    def _on_preferences(self, *_a):
        if self.window:
            self.window.open_preferences()

    def _on_about(self, *_a):
        about = Adw.AboutWindow(
            transient_for=self.window,
            application_name=APP_NAME,
            application_icon=APP_ID,
            version=__version__,
            developer_name="gknowledge contributors",
            comments="A native GNOME knowledge workstation that turns raw "
                     "material into an evolving knowledge base.",
            website="https://github.com/openapi/gknowledge",
            issue_url="https://github.com/openapi/gknowledge/issues",
            copyright="© 2026 gknowledge contributors",
            license_type=Gtk.License.MIT_X11,
        )
        about.present()

    def _on_quit(self, *_a):
        # Closing the window asks about an unsaved draft, then ends the app.
        if self.window:
            self.window.close()
        else:
            self.quit()


def main(argv=None) -> int:
    app = GknowledgeApp()
    return app.run(argv)

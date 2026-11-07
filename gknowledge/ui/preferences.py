"""Provider & project settings dialog."""

from __future__ import annotations

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Adw, GLib, Gtk  # noqa: E402
import threading

from ..providers.chatgpt import ChatGPTAuth, SignInError
from ..providers.openai_compatible import (
    DEFAULT_OLLAMA_BASE_URL,
    OllamaUnavailable,
    discover_ollama_models,
    get_ollama_selection_state,
    resolve_ollama_model_selection,
    should_prefill_ollama_base_url,
)

from ..core.project import Project, Settings

_PROVIDERS = [
    ("offline", "Offline (local heuristics)"),
    ("chatgpt", "ChatGPT plan (sign in, no API key)"),
    ("openai", "OpenAI"),
    ("custom", "OpenAI-compatible / Custom"),
    ("ollama", "Ollama (local)"),
]
def _full_width_factory() -> Gtk.SignalListItemFactory:
    """Item factory whose labels never ellipsize, so long names stay readable."""
    factory = Gtk.SignalListItemFactory()

    def setup(_f, item):
        item.set_child(Gtk.Label(xalign=0, ellipsize=0))

    def bind(_f, item):
        item.get_child().set_label(item.get_item().get_string())

    factory.connect("setup", setup)
    factory.connect("bind", bind)
    return factory


_LANGS = ["English", "Italiano", "Español", "Français", "Deutsch", "中文"]


class PreferencesDialog(Adw.PreferencesWindow):
    def __init__(self, parent: Gtk.Window, project: Project, on_saved):
        super().__init__(title="Preferences")
        self.set_transient_for(parent)
        self.set_modal(True)
        self.set_search_enabled(False)
        # Wide enough for "ChatGPT plan (sign in, no API key)" without ellipsis.
        self.set_default_size(720, 640)
        self._project = project
        self._on_saved = on_saved
        s = project.settings

        page = Adw.PreferencesPage(title="Provider", icon_name="preferences-system-symbolic")
        self.add(page)

        group = Adw.PreferencesGroup(
            title="LLM Provider",
            description="Choose how knowledge is extracted. Offline needs no API key.",
        )
        page.add(group)

        self._provider_row = Adw.ComboRow(title="Provider")
        model = Gtk.StringList()
        for _, label in _PROVIDERS:
            model.append(label)
        self._provider_row.set_model(model)
        self._provider_row.set_factory(_full_width_factory())
        self._provider_row.set_list_factory(_full_width_factory())
        self._provider_row.set_selected(self._provider_index(s.provider))
        self._provider_row.connect("notify::selected", self._on_provider_changed)
        group.add(self._provider_row)

        # Ollama: list local models, probed only on user request.
        self._saved_ollama_model = s.model if s.provider == "ollama" else ""
        self._last_selected_provider = s.provider
        self._ollama_models: list[str] = []
        self._ollama_request_id = 0
        self._updating_ollama_models = False
        self._ollama_probe_in_flight = False

        self._ollama_row = Adw.ActionRow(title="Ollama server",
                                         subtitle="Local model discovery")
        self._detect_btn = Gtk.Button(label="Detect", valign=Gtk.Align.CENTER)
        self._detect_btn.connect("clicked", self._on_detect_clicked)
        self._ollama_row.add_suffix(self._detect_btn)
        group.add(self._ollama_row)

        # ChatGPT account: sign in like linking a cloud drive.
        self._auth = ChatGPTAuth()
        self._cancel = threading.Event()
        self._account_row = Adw.ActionRow(title="ChatGPT account")
        self._signin_btn = Gtk.Button(label="Sign in with ChatGPT",
                                      valign=Gtk.Align.CENTER)
        self._signin_btn.add_css_class("suggested-action")
        self._signin_btn.connect("clicked", self._on_signin_clicked)
        self._account_row.add_suffix(self._signin_btn)
        group.add(self._account_row)
        self._refresh_account_row()

        self._base_url = Adw.EntryRow(title="Base URL")
        self._base_url.set_text(s.base_url)
        group.add(self._base_url)

        self._api_key = Adw.PasswordEntryRow(title="API Key")
        self._api_key.set_text(s.api_key)
        group.add(self._api_key)

        self._model = Adw.EntryRow(title="Model")
        self._model.set_text(s.model)
        group.add(self._model)

        # For the ChatGPT plan the model list comes from the signed-in account.
        self._model_slugs: list[str] = [""]
        self._model_list = Gtk.StringList.new(["Automatic (recommended)"])
        self._model_combo = Adw.ComboRow(title="Model", model=self._model_list,
                                         subtitle="Loaded from your ChatGPT account")
        self._model_combo.set_factory(_full_width_factory())
        self._model_combo.set_list_factory(_full_width_factory())
        group.add(self._model_combo)
        self._saved_model = s.model if s.provider == "chatgpt" else ""

        # For Ollama the model list comes from local server discovery.
        self._ollama_model_list = Gtk.StringList.new([])
        self._ollama_model_combo = Adw.ComboRow(title="Model", model=self._ollama_model_list,
                                                subtitle="Discovered from local Ollama server")
        self._ollama_model_combo.set_factory(_full_width_factory())
        self._ollama_model_combo.set_list_factory(_full_width_factory())
        self._ollama_model_combo.connect("notify::selected", self._on_ollama_model_changed)
        group.add(self._ollama_model_combo)

        lang_group = Adw.PreferencesGroup(title="Generation")
        page.add(lang_group)
        self._lang = Adw.ComboRow(title="Language")
        lang_model = Gtk.StringList()
        for l in _LANGS:
            lang_model.append(l)
        self._lang.set_model(lang_model)
        self._lang.set_selected(_LANGS.index(s.language) if s.language in _LANGS else 0)
        lang_group.add(self._lang)

        save_group = Adw.PreferencesGroup()
        page.add(save_group)
        save_btn = Gtk.Button(label="Save", halign=Gtk.Align.END)
        save_btn.add_css_class("suggested-action")
        save_btn.connect("clicked", self._on_save)
        save_group.add(save_btn)

        self._sync_sensitivity()

    @staticmethod
    def _provider_index(value: str) -> int:
        for i, (key, _) in enumerate(_PROVIDERS):
            if key == value:
                return i
        return 0

    def _on_provider_changed(self, *_a):
        kind = _PROVIDERS[self._provider_row.get_selected()][0]
        if kind == "ollama" and self._last_selected_provider != "ollama":
            if not self._ollama_models and not self._ollama_probe_in_flight:
                self._load_ollama_models()
        self._last_selected_provider = kind
        self._sync_sensitivity()

    def _sync_sensitivity(self):
        kind = _PROVIDERS[self._provider_row.get_selected()][0]
        is_offline = (kind == "offline")
        is_chatgpt = (kind == "chatgpt")
        is_ollama = (kind == "ollama")

        self._account_row.set_visible(is_chatgpt)
        self._ollama_row.set_visible(is_ollama)
        self._base_url.set_visible(not is_chatgpt)
        self._api_key.set_visible(not is_chatgpt)
        self._base_url.set_sensitive(not is_offline)
        self._api_key.set_sensitive(not is_offline)
        self._model.set_sensitive(not is_offline)

        self._model_combo.set_visible(is_chatgpt)

        if is_chatgpt:
            self._model.set_visible(False)
            self._ollama_model_combo.set_visible(False)
            if len(self._model_slugs) == 1:
                self._load_chatgpt_models()
        elif is_ollama:
            has_models = bool(self._ollama_models)
            self._ollama_model_combo.set_visible(has_models)
            if has_models:
                idx = self._ollama_model_combo.get_selected()
                _, is_custom = get_ollama_selection_state(idx, self._ollama_models)
                self._model.set_visible(is_custom)
                if is_custom:
                    self._model.set_title("Custom Model")
            else:
                self._model.set_visible(True)
                self._model.set_title("Model")
        else:
            self._ollama_model_combo.set_visible(False)
            self._model.set_visible(True)
            self._model.set_title("Model")

    def _load_chatgpt_models(self):
        if not self._auth.store.load().sharing:
            self._model_combo.set_subtitle("Sign in to choose a model")
            return
        self._model_combo.set_subtitle("Loading models…")

        def work():
            from ..providers.chatgpt import ChatGPTPlanProvider
            try:
                models = ChatGPTPlanProvider(auth=self._auth).list_models()
                err = None
            except Exception as exc:  # noqa: BLE001
                models, err = [], str(exc)
            GLib.idle_add(self._fill_models, models, err)

        threading.Thread(target=work, daemon=True).start()

    def _fill_models(self, models, err):
        if err:
            self._model_combo.set_subtitle(f"Could not load models: {err[:80]}")
            return False
        self._model_slugs = [""] + [m["slug"] for m in models]
        names = ["Automatic (recommended)"] + [m.get("display_name") or m["slug"] for m in models]
        self._model_list.splice(0, self._model_list.get_n_items(), names)
        if self._saved_model in self._model_slugs:
            self._model_combo.set_selected(self._model_slugs.index(self._saved_model))
        self._model_combo.set_subtitle("Models available to your ChatGPT account")
        return False

    # -- Ollama local discovery ----------------------------------------------
    def _on_detect_clicked(self, *_a):
        self._load_ollama_models()

    def _on_ollama_model_changed(self, *_a):
        # "Custom…" reveals the free-text Model row; a discovered model hides it.
        if self._updating_ollama_models or not self._ollama_models:
            return
        _, is_custom = get_ollama_selection_state(
            self._ollama_model_combo.get_selected(), self._ollama_models)
        self._model.set_title("Custom Model")
        self._model.set_visible(is_custom)

    def _get_current_ollama_model(self) -> str:
        """Return the currently selected or entered Ollama model name."""
        if self._ollama_model_combo.get_visible() and self._ollama_models:
            idx = self._ollama_model_combo.get_selected()
            model_name, is_custom = get_ollama_selection_state(idx, self._ollama_models)
            if model_name is not None:
                return model_name
            if is_custom:
                return self._model.get_text().strip()

        text = self._model.get_text().strip()
        if text:
            if self._project.settings.provider == "ollama" or text != "gpt-4o-mini":
                return text

        return self._saved_ollama_model

    def _load_ollama_models(self):
        self._ollama_request_id += 1
        req_id = self._ollama_request_id
        self._ollama_probe_in_flight = True
        self._detect_btn.set_sensitive(False)
        self._ollama_row.set_subtitle("Connecting to Ollama…")

        current_model = self._get_current_ollama_model()

        def work():
            # Always the local default: a URL left over from another provider
            # must never receive an unrequested probe.
            try:
                models = discover_ollama_models()
                err = None
            except OllamaUnavailable:
                models, err = [], "No Ollama server found at localhost:11434"
            except Exception as exc:  # noqa: BLE001
                models, err = [], f"Could not list Ollama models: {str(exc)[:80]}"
            GLib.idle_add(self._fill_ollama_models, req_id, current_model, models, err)

        threading.Thread(target=work, daemon=True).start()

    def _fill_ollama_models(self, req_id: int, current_model: str, models: list[str], err: str | None):
        if req_id != self._ollama_request_id:
            return False

        self._ollama_probe_in_flight = False
        self._detect_btn.set_sensitive(True)

        current_kind = _PROVIDERS[self._provider_row.get_selected()][0]
        if current_kind != "ollama":
            return False

        if err:
            self._ollama_row.set_subtitle(err)
            self._ollama_models = []
            if current_model:
                self._model.set_text(current_model)
            self._sync_sensitivity()
            return False

        if not models:
            self._ollama_row.set_subtitle("Ollama is running, but no models are installed")
            self._ollama_models = []
            if current_model:
                self._model.set_text(current_model)
            self._sync_sensitivity()
            return False

        if should_prefill_ollama_base_url(self._base_url.get_text()):
            self._base_url.set_text(DEFAULT_OLLAMA_BASE_URL)

        n = len(models)
        self._ollama_row.set_subtitle(
            f"Ollama running at localhost ({n} model{'s' if n != 1 else ''} found)"
        )
        self._ollama_models = list(models)

        self._updating_ollama_models = True
        try:
            items = list(models) + ["Custom…"]
            self._ollama_model_list.splice(0, self._ollama_model_list.get_n_items(), items)

            idx, chosen_model, _ = resolve_ollama_model_selection(current_model, models)
            self._ollama_model_combo.set_selected(idx)
            self._model.set_text(chosen_model)
        finally:
            self._updating_ollama_models = False

        self._sync_sensitivity()
        return False

    # -- ChatGPT sign-in -----------------------------------------------------
    def _refresh_account_row(self, message: str | None = None):
        acct = self._auth.store.load()
        if message:
            self._account_row.set_subtitle(message)
        elif acct.sharing:
            who = acct.email or "your account"
            self._account_row.set_subtitle(
                f"Signed in as {who}. Usage is charged to your ChatGPT plan "
                "(limits in ChatGPT Settings, Usage).")
        elif acct.signed_in:
            self._account_row.set_subtitle(
                "Signed in, but plan usage was not allowed. Sign in again.")
        else:
            self._account_row.set_subtitle(
                "Use your own ChatGPT Plus or Pro plan. No API key needed.")
        self._signin_btn.set_label("Sign out" if acct.signed_in else "Sign in with ChatGPT")
        self._signin_btn.remove_css_class("suggested-action")
        if not acct.signed_in:
            self._signin_btn.add_css_class("suggested-action")
        self._signin_btn.set_sensitive(True)
        if acct.sharing and len(getattr(self, "_model_slugs", [0, 0])) == 1 and \
                _PROVIDERS[self._provider_row.get_selected()][0] == "chatgpt":
            self._load_chatgpt_models()

    def _on_signin_clicked(self, *_a):
        acct = self._auth.store.load()
        self._signin_btn.set_sensitive(False)
        if acct.signed_in:
            def out():
                self._auth.sign_out()
                GLib.idle_add(self._refresh_account_row)
            threading.Thread(target=out, daemon=True).start()
            return
        self._refresh_account_row("Waiting for your browser…")
        self._signin_btn.set_sensitive(False)
        self._cancel.clear()

        def open_url(url):
            def launch():
                Gtk.UriLauncher.new(url).launch(self, None, None, None)
                return False
            GLib.idle_add(launch)

        def work():
            try:
                self._auth.sign_in(open_url, cancel=self._cancel)
                msg = None
            except SignInError as exc:
                msg = str(exc)
            except Exception as exc:  # noqa: BLE001
                msg = f"Sign-in failed: {exc}"
            GLib.idle_add(self._refresh_account_row, msg)

        threading.Thread(target=work, daemon=True).start()

    def _on_save(self, *_a):
        provider = _PROVIDERS[self._provider_row.get_selected()][0]
        if provider == "chatgpt":
            model = (self._model_slugs[self._model_combo.get_selected()]
                     if self._model_combo.get_selected() < len(self._model_slugs)
                     else "")
        elif provider == "ollama":
            if self._ollama_model_combo.get_visible() and self._ollama_models:
                idx = self._ollama_model_combo.get_selected()
                model_name, _ = get_ollama_selection_state(idx, self._ollama_models)
                if model_name is not None:
                    model = model_name
                else:
                    model = self._model.get_text().strip() or "llama3.2"
            else:
                model = self._model.get_text().strip() or "llama3.2"
        else:
            model = self._model.get_text().strip() or "gpt-4o-mini"

        settings = Settings(
            provider=provider,
            base_url=self._base_url.get_text().strip() or (
                DEFAULT_OLLAMA_BASE_URL if provider == "ollama" else "https://api.openai.com/v1"
            ),
            api_key=self._api_key.get_text().strip(),
            model=model,
            language=_LANGS[self._lang.get_selected()],
        )
        self._cancel.set()
        self._project.save_settings(settings)
        if self._on_saved:
            self._on_saved(settings)
        self.close()

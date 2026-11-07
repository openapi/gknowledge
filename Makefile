# gknowledge — build & install
#
# `make install` performs a local (per-user) install using the system
# PyGObject, so it works out of the box on Ubuntu/Fedora/Arch without touching
# pip's externally-managed environment. Use PREFIX=/usr with sudo for a
# system-wide install.

APP_ID      := io.github.openapi.Gknowledge
PYTHON      ?= python3
PREFIX      ?= $(HOME)/.local
DESTDIR     ?=
BINDIR      := $(PREFIX)/bin
LIBDIR      := $(PREFIX)/share/gknowledge
DATADIR     := $(PREFIX)/share
APPSDIR     := $(DATADIR)/applications
ICONDIR     := $(DATADIR)/icons/hicolor/scalable/apps
METAINFODIR := $(DATADIR)/metainfo

INSTALL     := install

.PHONY: all help check test run dev start start-flatpak demo-svg install uninstall clean dist pypi flatpak

all: help

help:
	@echo "gknowledge — targets:"
	@echo "  make start      Dev loop: run on a demo project and auto-restart on source changes"
	@echo "  make start-flatpak  Same loop, but inside the GNOME runtime Flatpak users get"
	@echo "  make run        Run the app from the source tree (opens your last project)"
	@echo "  make test       Run the headless core test suite"
	@echo "  make check      Byte-compile all sources (syntax check)"
	@echo "  make install    Install locally into $(PREFIX)"
	@echo "  make uninstall  Remove a local install"
	@echo "  make dist       Build a wheel/sdist with the Python build backend"
	@echo "  make pypi       Build the gknowledge-mcp package for PyPI into dist/pypi"
	@echo "  make flatpak    Build a Flatpak (needs flatpak-builder)"
	@echo "  make clean      Remove build artifacts"

check:
	$(PYTHON) -m compileall -q gknowledge

test:
	$(PYTHON) tests/test_core.py

run:
	$(PYTHON) -m gknowledge

dev: run

# Rapid development loop: launch the app on a throwaway demo project and
# restart it automatically whenever a file under gknowledge/ changes. Config (recent projects, provider settings) is
# kept in ./sandbox/config so your real settings are never touched.
SANDBOX     := sandbox
DEMO        := $(SANDBOX)/demo

demo-svg:
	$(PYTHON) build-aux/dev/make_demo_svg.py docs/gknowledge-demo.svg

start:
	@mkdir -p $(SANDBOX)/config
	@if [ ! -f $(DEMO)/gknowledge.json ]; then \
		echo ">> Creating and ingesting demo project in $(DEMO)"; \
		$(PYTHON) build-aux/dev/seed_demo.py $(DEMO); \
	fi
	XDG_CONFIG_HOME=$(CURDIR)/$(SANDBOX)/config $(PYTHON) build-aux/dev/watch.py $(DEMO)

# The same loop inside the Flatpak runtime: the host GTK and libadwaita can
# differ from what Flatpak users run, so check UI work here before a release.
# The runtime version is read from the manifest to keep the two in sync.
RUNTIME     := org.gnome.Platform//$(shell sed -n "s/^runtime-version: *'\(.*\)'/\1/p" build-aux/flatpak/$(APP_ID).yaml)

start-flatpak:
	@flatpak info --user $(RUNTIME) >/dev/null 2>&1 || flatpak info $(RUNTIME) >/dev/null 2>&1 || { \
		echo ">> Missing runtime. Install it with:"; \
		echo "   flatpak install --user flathub $(RUNTIME)"; exit 1; }
	@mkdir -p $(SANDBOX)/config
	@if [ ! -f $(DEMO)/gknowledge.json ]; then \
		echo ">> Creating and ingesting demo project in $(DEMO)"; \
		$(PYTHON) build-aux/dev/seed_demo.py $(DEMO); \
	fi
	flatpak run --share=network --share=ipc --socket=wayland --socket=fallback-x11 \
		--device=dri --own-name=$(APP_ID) --filesystem=$(CURDIR) --cwd=$(CURDIR) \
		--env=XDG_CONFIG_HOME=$(CURDIR)/$(SANDBOX)/config \
		--command=python3 $(RUNTIME) build-aux/dev/watch.py $(DEMO)

install:
	@echo ">> Installing gknowledge into $(DESTDIR)$(PREFIX)"
	$(INSTALL) -d $(DESTDIR)$(LIBDIR)
	cp -r gknowledge $(DESTDIR)$(LIBDIR)/
	$(PYTHON) -m compileall -q $(DESTDIR)$(LIBDIR)/gknowledge || true
	# Launcher that uses the installed package with the system PyGObject.
	$(INSTALL) -d $(DESTDIR)$(BINDIR)
	printf '#!/bin/sh\nexport PYTHONPATH="%s:$$PYTHONPATH"\nexec %s -m gknowledge "$$@"\n' \
		"$(LIBDIR)" "$(PYTHON)" > $(DESTDIR)$(BINDIR)/gknowledge
	chmod +x $(DESTDIR)$(BINDIR)/gknowledge
	printf '#!/bin/sh\nexport PYTHONPATH="%s:$$PYTHONPATH"\nexec %s -m gknowledge.mcp "$$@"\n' \
		"$(LIBDIR)" "$(PYTHON)" > $(DESTDIR)$(BINDIR)/gknowledge-mcp
	chmod +x $(DESTDIR)$(BINDIR)/gknowledge-mcp
	# Desktop entry, icon and AppStream metadata.
	$(INSTALL) -d $(DESTDIR)$(APPSDIR)
	$(INSTALL) -m 644 data/$(APP_ID).desktop $(DESTDIR)$(APPSDIR)/$(APP_ID).desktop
	$(INSTALL) -d $(DESTDIR)$(ICONDIR)
	$(INSTALL) -m 644 data/icons/hicolor/scalable/apps/$(APP_ID).svg $(DESTDIR)$(ICONDIR)/$(APP_ID).svg
	$(INSTALL) -d $(DESTDIR)$(METAINFODIR)
	$(INSTALL) -m 644 data/$(APP_ID).metainfo.xml $(DESTDIR)$(METAINFODIR)/$(APP_ID).metainfo.xml
	@# Refresh caches only for a live install; packages leave this to dpkg triggers.
	@if [ -z "$(DESTDIR)" ]; then \
		update-desktop-database $(APPSDIR) 2>/dev/null || true; \
		gtk-update-icon-cache -f -t $(DATADIR)/icons/hicolor 2>/dev/null || true; \
	fi
	@echo ">> Done. Make sure $(BINDIR) is on your PATH, then run: gknowledge"

uninstall:
	rm -f  $(DESTDIR)$(BINDIR)/gknowledge $(DESTDIR)$(BINDIR)/gknowledge-mcp
	rm -rf $(DESTDIR)$(LIBDIR)
	rm -f  $(DESTDIR)$(APPSDIR)/$(APP_ID).desktop
	rm -f  $(DESTDIR)$(ICONDIR)/$(APP_ID).svg
	rm -f  $(DESTDIR)$(METAINFODIR)/$(APP_ID).metainfo.xml
	@# A stale icon cache would still point at the removed icon and leave a blank one.
	@if [ -z "$(DESTDIR)" ]; then \
		update-desktop-database $(APPSDIR) 2>/dev/null || true; \
		gtk-update-icon-cache -f -t $(DATADIR)/icons/hicolor 2>/dev/null || true; \
	fi
	@echo ">> Uninstalled gknowledge from $(PREFIX)"

dist:
	$(PYTHON) -m build

pypi:
	build-aux/pypi/build.sh dist/pypi

flatpak:
	flatpak-builder --user --install --force-clean build-aux/flatpak-build \
		build-aux/flatpak/$(APP_ID).yaml

clean:
	rm -rf build dist *.egg-info build-aux/flatpak-build .pytest_cache
	find gknowledge -name '__pycache__' -type d -exec rm -rf {} + 2>/dev/null || true

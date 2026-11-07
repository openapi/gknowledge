#!/usr/bin/env bash
# gknowledge installer.
#
#   curl -fsSL https://github.com/openapi/gknowledge/releases/latest/download/install.sh | bash
#
# Ubuntu / Debian: adds the signed gknowledge APT repository and installs from
# it, so later versions arrive with `apt upgrade`. apt also pulls GTK 4,
# Libadwaita and PyGObject. If the repository is unreachable, installs the
# latest .deb from GitHub Releases instead.
# Other distributions: installs the latest release into ~/.local (no root),
# after checking that PyGObject, GTK 4 and Libadwaita are present.
#
# Environment overrides:
#   GKNOWLEDGE_REPO   owner/repo (default openapi/gknowledge)
#   GKNOWLEDGE_MODE   deb | local (default: deb when apt is available)
#   GKNOWLEDGE_NO_REPO=1  install the release .deb without adding the repository
set -euo pipefail

REPO="${GKNOWLEDGE_REPO:-openapi/gknowledge}"
BASE="https://github.com/${REPO}/releases/latest/download"
PAGES="${GKNOWLEDGE_PAGES:-https://${REPO%%/*}.github.io/${REPO#*/}}"

info() { printf '\033[1;34m==>\033[0m %s\n' "$*"; }
warn() { printf '\033[1;33m!!\033[0m %s\n' "$*" >&2; }
die()  { printf '\033[1;31mxx\033[0m %s\n' "$*" >&2; exit 1; }

need() { command -v "$1" >/dev/null 2>&1 || die "'$1' is required but not installed."; }

sudo_cmd() {
  if [ "$(id -u)" -eq 0 ]; then "$@"; else need sudo; sudo "$@"; fi
}

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

install_repo() {
  info "Adding the gknowledge APT repository ($PAGES/apt)"
  curl -fsSL -o "$TMP/gknowledge.gpg" "$PAGES/gknowledge.gpg" || return 1
  curl -fsSL -o "$TMP/gknowledge.sources" "$PAGES/gknowledge.sources" || return 1
  grep -q "^URIs: $PAGES/apt$" "$TMP/gknowledge.sources" || return 1
  sudo_cmd install -m 644 "$TMP/gknowledge.gpg" /usr/share/keyrings/gknowledge.gpg
  sudo_cmd install -m 644 "$TMP/gknowledge.sources" /etc/apt/sources.list.d/gknowledge.sources
  info "Installing with apt (you may be asked for your password)"
  sudo_cmd apt-get update -o Dir::Etc::sourcelist=sources.list.d/gknowledge.sources \
    -o Dir::Etc::sourceparts=- -o APT::Get::List-Cleanup=0 || {
    # A broken source would make every later `apt update` fail.
    sudo_cmd rm -f /etc/apt/sources.list.d/gknowledge.sources /usr/share/keyrings/gknowledge.gpg
    return 1
  }
  sudo_cmd apt-get install -y gknowledge
}

install_release_deb() {
  info "Downloading the latest gknowledge .deb"
  curl -fL --progress-bar -o "$TMP/gknowledge_all.deb" "$BASE/gknowledge_all.deb" \
    || die "Download failed from $BASE/gknowledge_all.deb"
  # apt downloads as the unprivileged _apt user, which cannot enter mktemp's 0700 dir.
  chmod 755 "$TMP"
  chmod 644 "$TMP/gknowledge_all.deb"
  info "Installing with apt (you may be asked for your password)"
  sudo_cmd apt-get install -y "$TMP/gknowledge_all.deb"
}

install_deb() {
  if [ "${GKNOWLEDGE_NO_REPO:-}" = 1 ] || ! install_repo; then
    [ "${GKNOWLEDGE_NO_REPO:-}" = 1 ] || warn "The APT repository is not reachable; installing the release .deb (no automatic updates)."
    install_release_deb
  fi
  if [ -e "$HOME/.local/bin/gknowledge" ] || [ -e "$HOME/.local/share/applications/io.gknowledge.Gknowledge.desktop" ] \
     || [ -e "$HOME/.local/share/applications/io.github.openapi.Gknowledge.desktop" ]; then
    warn "An older gknowledge in ~/.local shadows this install (old icon and version)."
    warn "Remove it with: rm -rf ~/.local/bin/gknowledge ~/.local/bin/gknowledge-mcp ~/.local/share/gknowledge ~/.local/share/applications/io.*Gknowledge.desktop ~/.local/share/icons/hicolor/scalable/apps/io.*Gknowledge.svg ~/.local/share/metainfo/io.*Gknowledge.metainfo.xml && gtk-update-icon-cache -f -t ~/.local/share/icons/hicolor"
  fi
  info "Done. Launch gknowledge from the app grid or run: gknowledge"
}

install_local() {
  need python3
  need make
  need tar
  python3 - <<'PY' || die "Missing PyGObject, GTK 4 or Libadwaita. Install them with your package manager (Fedora: python3-gobject gtk4 libadwaita; Arch: python-gobject gtk4 libadwaita) and run this again."
import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Adw, Gtk  # noqa: F401
PY
  info "Resolving the latest release"
  tag="$(curl -fsSLI -o /dev/null -w '%{url_effective}' "https://github.com/${REPO}/releases/latest")"
  tag="${tag##*/}"
  if [ -z "$tag" ] || [ "$tag" = "latest" ]; then
    die "Could not determine the latest release."
  fi
  info "Downloading gknowledge ${tag}"
  curl -fsSL "https://github.com/${REPO}/archive/refs/tags/${tag}.tar.gz" | tar -xz -C "$TMP"
  src="$(find "$TMP" -mindepth 1 -maxdepth 1 -type d | head -n1)"
  info "Installing into ~/.local"
  make -C "$src" install PREFIX="$HOME/.local" >/dev/null
  case ":$PATH:" in
    *":$HOME/.local/bin:"*) ;;
    *) warn "Add ~/.local/bin to your PATH to run 'gknowledge' from a terminal." ;;
  esac
  info "Done. Launch gknowledge from the app grid or run: gknowledge"
}

main() {
  need curl
  [ "$(uname -s)" = "Linux" ] || die "gknowledge is a Linux desktop application."
  mode="${GKNOWLEDGE_MODE:-}"
  if [ -z "$mode" ]; then
    if command -v apt-get >/dev/null 2>&1 && command -v dpkg >/dev/null 2>&1; then
      mode=deb
    else
      mode=local
    fi
  fi
  case "$mode" in
    deb) install_deb ;;
    local) install_local ;;
    *) die "Unknown GKNOWLEDGE_MODE '$mode' (use deb or local)." ;;
  esac
}

main "$@"

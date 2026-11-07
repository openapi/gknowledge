#!/bin/sh
# Build the static package repositories served from GitHub Pages:
# an APT repository and a Flatpak remote, both signed with one GPG key.
#
# Usage: build-aux/repos/build-site.sh DEB_DIR FLATPAK_BUNDLE OUT_DIR BASE_URL
#
#   DEB_DIR         directory with the gknowledge_*_all.deb files to publish
#   FLATPAK_BUNDLE  gknowledge-vX.Y.Z.flatpak from the release
#   OUT_DIR         where the site is written (emptied first)
#   BASE_URL        public URL of the site, e.g. https://openapi.github.io/gknowledge
#
# The signing key must already be in the GnuPG keyring; GPG_KEY_ID selects it.
# Needs: apt-utils (apt-ftparchive), gnupg, flatpak, ostree.
set -eu

DEB_DIR=$1
BUNDLE=$2
OUT=$3
BASE_URL=${4%/}
APP_ID=io.github.openapi.Gknowledge
# Until 0.3.0 the app was io.gknowledge.Gknowledge (a domain nobody owns).
OLD_ID=io.gknowledge.Gknowledge
: "${GPG_KEY_ID:?set GPG_KEY_ID to the signing key}"
ROOT=$(cd "$(dirname "$0")/../.." && pwd)

rm -rf "$OUT"
mkdir -p "$OUT"

# Public key, armored for Flatpak and binary for apt's Signed-By.
gpg --batch --export "$GPG_KEY_ID" > "$OUT/gknowledge.gpg"
gpg --batch --armor --export "$GPG_KEY_ID" > "$OUT/gknowledge.asc"

# --- APT --------------------------------------------------------------------
# Architecture "all" packages are indexed for every common architecture so apt
# finds them without warnings on amd64 and arm64.
APT="$OUT/apt"
mkdir -p "$APT/pool/main"
cp "$DEB_DIR"/gknowledge_*_all.deb "$APT/pool/main/"
for arch in all amd64 arm64; do
  d="$APT/dists/stable/main/binary-$arch"
  mkdir -p "$d"
  (cd "$APT" && apt-ftparchive --arch "$arch" packages pool) > "$d/Packages"
  gzip -9nk "$d/Packages"
done
apt-ftparchive \
  -o APT::FTPArchive::Release::Origin=gknowledge \
  -o APT::FTPArchive::Release::Label=gknowledge \
  -o APT::FTPArchive::Release::Suite=stable \
  -o APT::FTPArchive::Release::Codename=stable \
  -o APT::FTPArchive::Release::Components=main \
  -o "APT::FTPArchive::Release::Architectures=all amd64 arm64" \
  -o "APT::FTPArchive::Release::Description=gknowledge packages" \
  release "$APT/dists/stable" > "$APT/dists/stable/Release"
gpg --batch --yes --local-user "$GPG_KEY_ID" --clearsign \
  -o "$APT/dists/stable/InRelease" "$APT/dists/stable/Release"
gpg --batch --yes --local-user "$GPG_KEY_ID" --armor --detach-sign \
  -o "$APT/dists/stable/Release.gpg" "$APT/dists/stable/Release"

cat > "$OUT/gknowledge.sources" <<EOF
Types: deb
URIs: $BASE_URL/apt
Suites: stable
Components: main
Signed-By: /usr/share/keyrings/gknowledge.gpg
EOF

# --- Flatpak ----------------------------------------------------------------
FP="$OUT/flatpak"
ostree init --mode=archive-z2 --repo="$FP"
# Only affects building; a nearly full build disk should not abort the import.
ostree config --repo="$FP" set core.min-free-space-percent 0
flatpak build-import-bundle --gpg-sign="$GPG_KEY_ID" "$FP" "$BUNDLE"
# Installs of the old ID move to the new one on the next `flatpak update`,
# and Flatpak carries ~/.var/app/$OLD_ID over with them.
for ref in $(ostree refs --repo="$FP" | grep "^app/$APP_ID/"); do
  flatpak build-commit-from --gpg-sign="$GPG_KEY_ID" --src-ref="$ref" \
    --end-of-life-rebase="$OLD_ID=$APP_ID" "$FP" "app/$OLD_ID/${ref#app/$APP_ID/}"
done
flatpak build-update-repo --gpg-sign="$GPG_KEY_ID" --generate-static-deltas \
  --title=gknowledge --default-branch=master "$FP"

KEY_B64=$(base64 -w0 < "$OUT/gknowledge.gpg")
cat > "$OUT/gknowledge.flatpakrepo" <<EOF
[Flatpak Repo]
Title=gknowledge
Url=$BASE_URL/flatpak/
Homepage=https://github.com/openapi/gknowledge
Comment=Native GNOME knowledge workstation
Icon=$BASE_URL/$APP_ID.svg
GPGKey=$KEY_B64
EOF
cat > "$OUT/$APP_ID.flatpakref" <<EOF
[Flatpak Ref]
Name=$APP_ID
Branch=master
Title=gknowledge
Url=$BASE_URL/flatpak/
SuggestRemoteName=gknowledge
Homepage=https://github.com/openapi/gknowledge
Icon=$BASE_URL/$APP_ID.svg
RuntimeRepo=https://dl.flathub.org/repo/flathub.flatpakrepo
IsRuntime=false
GPGKey=$KEY_B64
EOF
# Links to the old .flatpakref keep working and install the new ID.
cp "$OUT/$APP_ID.flatpakref" "$OUT/$OLD_ID.flatpakref"
cp "$ROOT/data/icons/hicolor/scalable/apps/$APP_ID.svg" "$OUT/"

# --- Landing page -----------------------------------------------------------
FPR=$(gpg --batch --with-colons --fingerprint "$GPG_KEY_ID" | awk -F: '/^fpr/{print $10; exit}')
sed -e "s|@BASE_URL@|$BASE_URL|g" -e "s|@FINGERPRINT@|$FPR|g" \
  "$ROOT/build-aux/repos/index.html" > "$OUT/index.html"
touch "$OUT/.nojekyll"
echo "Site written to $OUT"

#!/bin/bash
# build_deb.sh — Construit le paquet .deb de LibreTrador
set -euo pipefail

VERSION=$(python3 -c "from config import APP_VERSION; print(APP_VERSION)")
PKG="libretrador_${VERSION}_all"
BUILD_DIR="dist/${PKG}"

echo "=== Build LibreTrador v${VERSION} ==="

# Nettoyage
rm -rf "dist/${PKG}"

# Arborescence du paquet
mkdir -p "${BUILD_DIR}/DEBIAN"
mkdir -p "${BUILD_DIR}/usr/bin"
mkdir -p "${BUILD_DIR}/usr/lib/libretrador"
mkdir -p "${BUILD_DIR}/usr/share/applications"
mkdir -p "${BUILD_DIR}/usr/share/icons/hicolor/48x48/apps"
mkdir -p "${BUILD_DIR}/usr/share/icons/hicolor/128x128/apps"

# Wrapper exécutable
cat > "${BUILD_DIR}/usr/bin/libretrador" << 'EOF'
#!/bin/bash
cd /usr/lib/libretrador
exec python3 main.py "$@"
EOF
chmod 755 "${BUILD_DIR}/usr/bin/libretrador"

# Sources Python
cp -r main.py config.py core ui "${BUILD_DIR}/usr/lib/libretrador/"
cp -r assets "${BUILD_DIR}/usr/lib/libretrador/"

# Fichier .desktop
cp libretrador.desktop "${BUILD_DIR}/usr/share/applications/"

# Icônes PNG
if [ -f assets/libretrador_48.png ]; then
    cp assets/libretrador_48.png \
       "${BUILD_DIR}/usr/share/icons/hicolor/48x48/apps/libretrador.png"
fi
if [ -f assets/libretrador_128.png ]; then
    cp assets/libretrador_128.png \
       "${BUILD_DIR}/usr/share/icons/hicolor/128x128/apps/libretrador.png"
fi

# Métadonnées DEBIAN
cp debian/control   "${BUILD_DIR}/DEBIAN/"
cp debian/postinst  "${BUILD_DIR}/DEBIAN/"
chmod 755 "${BUILD_DIR}/DEBIAN/postinst"

# Calcul de la taille installée
INSTALLED_SIZE=$(du -sk "${BUILD_DIR}" | cut -f1)
echo "Installed-Size: ${INSTALLED_SIZE}" >> "${BUILD_DIR}/DEBIAN/control"

# Construction du .deb
dpkg-deb --build --root-owner-group "${BUILD_DIR}"
echo ""
echo "=== Paquet créé : dist/${PKG}.deb ==="

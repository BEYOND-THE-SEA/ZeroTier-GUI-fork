#!/bin/sh

# This script will create a deb package for ZeroTier-GUI

packageVersion=$(printf "1.4.0.r%s.%s" "$(git rev-list --count HEAD)" "$(git rev-parse --short HEAD)")

# Create file structure

mkdir -pv packaging/DEBIAN
mkdir -pv packaging/usr/share/licenses/ZeroTier-GUI
mkdir -pv packaging/usr/share/pixmaps
mkdir -pv packaging/usr/share/applications
mkdir -pv packaging/usr/share/doc/ZeroTier-GUI
mkdir -pv packaging/usr/share/polkit-1/actions
mkdir -pv packaging/usr/libexec
mkdir -pv packaging/usr/bin


# Copy files to corresponding directories

cp -vf LICENSE packaging/usr/share/licenses/ZeroTier-GUI
cp -vf img/zerotier-gui.png packaging/usr/share/pixmaps
cp -vf zerotier-gui.desktop packaging/usr/share/applications
cp -vf README.md packaging/usr/share/doc/ZeroTier-GUI
cp -vf src/zerotier-gui packaging/usr/bin
cp -vf src/zerotier-gui-helper packaging/usr/libexec
cp -vf linux/polkit/com.github.tralph3.zerotier-gui.policy packaging/usr/share/polkit-1/actions

chmod 755 packaging/usr/bin/zerotier-gui
chmod 755 packaging/usr/libexec/zerotier-gui-helper
chmod 644 packaging/usr/share/polkit-1/actions/com.github.tralph3.zerotier-gui.policy


# Create control file

echo "Package: zerotier-gui
Version: ${packageVersion}
Architecture: all
Maintainer: tralph3
Depends: python3-tk,policykit-1,python3 (>=3.6),acl,iproute2
Priority: optional
Homepage: https://github.com/tralph3/ZeroTier-GUI
Description: A Linux front-end for ZeroTier" > packaging/DEBIAN/control

# Build the package

dpkg-deb --root-owner-group --build packaging

# Rename the package

mv packaging.deb ZeroTier-GUI.deb

# Ensure predictable ownership for apt/_apt access
chmod a+r ZeroTier-GUI.deb

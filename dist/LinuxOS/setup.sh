#!/bin/bash

echo "[Desktop Entry]" > ALVIS.desktop
echo "Name=ALVIS" >> ALVIS.desktop
echo "GenericName=Novel AI Algorithms Visualization and Teaching Software" >> ALVIS.desktop
echo "Comment=Report a malfunction to the developers" >> ALVIS.desktop
echo "Exec=$PWD/ALVIS/ALVIS" >> ALVIS.desktop
echo "Icon=$PWD/ALVIS/assets/images/kivy-icon-512.png" >> ALVIS.desktop
echo "Type=Application" >> ALVIS.desktop
echo "Category=Office" >> ALVIS.desktop
sudo mv ALVIS.desktop /usr/share/applications

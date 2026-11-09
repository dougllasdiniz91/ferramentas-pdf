#!/usr/bin/env bash
rm -rf "$HOME/.local/share/ferramentas-pdf"
rm -f "$HOME/.local/bin/ferramentas-pdf" \
      "$HOME/.local/share/applications/ferramentas-pdf.desktop" \
      "$HOME/.local/share/icons/hicolor/scalable/apps/ferramentas-pdf.svg" \
      "$HOME"/.local/share/icons/hicolor/*x*/apps/ferramentas-pdf.png
update-desktop-database "$HOME/.local/share/applications" >/dev/null 2>&1 || true
echo "✔ Ferramentas PDF removido."

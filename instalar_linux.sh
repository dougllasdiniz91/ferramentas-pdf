#!/usr/bin/env bash
# Instala o Ferramentas PDF para o usuário atual.
# (Só pede senha se precisar instalar o Tkinter/venv do sistema.)
set -e

ORIGEM="$(cd "$(dirname "$0")" && pwd)"
DESTINO="$HOME/.local/share/ferramentas-pdf"
BIN="$HOME/.local/bin"
APPS="$HOME/.local/share/applications"
ICONES="$HOME/.local/share/icons/hicolor/scalable/apps"

echo ">> Verificando Tkinter e venv..."
if ! python3 -c "import tkinter, venv, ensurepip" 2>/dev/null; then
    echo "   Instalando dependências do sistema (pode pedir sua senha)..."
    if command -v apt >/dev/null; then sudo apt install -y python3-tk python3-venv
    elif command -v dnf >/dev/null; then sudo dnf install -y python3-tkinter
    elif command -v pacman >/dev/null; then sudo pacman -S --noconfirm tk
    else echo "   Instale o Tkinter do Python manualmente e rode de novo."; exit 1
    fi
fi

echo ">> Copiando arquivos para $DESTINO..."
mkdir -p "$DESTINO" "$BIN" "$APPS" "$ICONES"
cp "$ORIGEM/ferramentas_pdf.py" "$ORIGEM/pdf_core.py" "$ORIGEM/arquivos_info.py" "$ORIGEM/seletor.py" "$ORIGEM/tema.py" "$ORIGEM/dialogos.py" "$ORIGEM"/icone-*.png "$ORIGEM/requirements.txt" "$DESTINO/"
cp "$ORIGEM/icone.svg" "$ICONES/ferramentas-pdf.svg"
for n in 16 32 64 256; do
    mkdir -p "$HOME/.local/share/icons/hicolor/${n}x${n}/apps"
    cp "$ORIGEM/icone-$n.png" "$HOME/.local/share/icons/hicolor/${n}x${n}/apps/ferramentas-pdf.png"
done

echo ">> Criando ambiente Python e instalando pypdf..."
python3 -m venv "$DESTINO/venv"
"$DESTINO/venv/bin/pip" install --quiet --upgrade pip
"$DESTINO/venv/bin/pip" install --quiet -r "$DESTINO/requirements.txt"

cat > "$BIN/ferramentas-pdf" <<EOS
#!/usr/bin/env bash
exec "$DESTINO/venv/bin/python" "$DESTINO/ferramentas_pdf.py" "\$@"
EOS
chmod +x "$BIN/ferramentas-pdf"

echo ">> Adicionando ao menu de aplicativos..."
cat > "$APPS/ferramentas-pdf.desktop" <<EOS
[Desktop Entry]
Type=Application
Name=Ferramentas PDF
Comment=Unir e separar arquivos PDF
Exec=$BIN/ferramentas-pdf %F
Icon=ferramentas-pdf
Terminal=false
Categories=Office;Utility;
MimeType=application/pdf;
StartupWMClass=Ferramentas-pdf
StartupNotify=true
Keywords=pdf;unir;juntar;separar;dividir;merge;split;
EOS
update-desktop-database "$APPS" >/dev/null 2>&1 || true
gtk-update-icon-cache -q "$HOME/.local/share/icons/hicolor" >/dev/null 2>&1 || true

echo
echo "✔ Instalado! Procure por 'Ferramentas PDF' no menu ou rode: ferramentas-pdf"

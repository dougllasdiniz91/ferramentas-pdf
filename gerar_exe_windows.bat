@echo off
REM Gera FerramentasPDF.exe (rode no Windows com Python 3 instalado de python.org)
python -m pip install --upgrade pip pypdf pyinstaller
python -m PyInstaller --noconfirm --onefile --windowed --name FerramentasPDF --icon icone.ico --add-data "icone-256.png;." --add-data "icone-64.png;." --add-data "icone-32.png;." --add-data "icone-16.png;." --add-data "icone.ico;." ferramentas_pdf.py
echo.
echo Pronto! O executavel esta em: dist\FerramentasPDF.exe
pause

"""Tema visual claro e moderno (ttk/clam com paleta própria)."""

import os
import sys
import tkinter as tk
import tkinter.font as tkfont
from tkinter import ttk

# Classe das janelas (WM_CLASS). Tem que bater com StartupWMClass do .desktop para a
# barra de tarefas/dock associar a janela ao lançador e usar o mesmo ícone.
CLASSE_JANELA = "Ferramentas-pdf"

# Tamanho padrão de todas as janelas grandes (principal, abrir, salvar, escolher pasta)
JANELA_PADRAO = (1100, 680)
JANELA_MINIMA = (900, 560)

# Paleta
FUNDO = "#ffffff"        # fundo geral
SUPERFICIE = "#f6f8fb"   # barras, cabeçalhos, áreas secundárias
BORDA = "#e3e8ef"
BORDA_FORTE = "#c9d2de"
TEXTO = "#1e293b"
SUTIL = "#64748b"
DESTAQUE = "#2563eb"
DESTAQUE_HOVER = "#1d4ed8"
DESTAQUE_CLARO = "#e8f0fe"
MARCADO = "#dbe7fd"
PASTA = "#1e40af"


def _fonte_base():
    familias = set(tkfont.families())
    for f in ("Inter", "Segoe UI", "Cantarell", "Ubuntu", "Noto Sans", "SF Pro Text",
              "Helvetica Neue", "DejaVu Sans"):
        if f in familias:
            return f
    return tkfont.nametofont("TkDefaultFont").actual()["family"]


def _pasta_recursos():
    # no executável do PyInstaller os arquivos ficam em sys._MEIPASS
    return getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))


def aplicar_icone(root):
    """Usa o mesmo ícone do lançador em todas as janelas (barra de tarefas e Alt+Tab)."""
    pasta = _pasta_recursos()
    imagens = []
    for n in (256, 64, 32, 16):
        caminho = os.path.join(pasta, f"icone-{n}.png")
        if os.path.isfile(caminho):
            try:
                imagens.append(tk.PhotoImage(master=root, file=caminho))
            except tk.TclError:
                pass
    if imagens:
        root.iconphoto(True, *imagens)  # True = vale também para as janelas filhas
        root._icones = imagens  # mantém referência (senão o Tk descarta as imagens)
    if sys.platform.startswith("win"):
        ico = os.path.join(pasta, "icone.ico")
        if os.path.isfile(ico):
            try:
                root.iconbitmap(default=ico)
            except tk.TclError:
                pass


def aplicar_tema(root):
    fam = _fonte_base()
    for nome in ("TkDefaultFont", "TkTextFont", "TkMenuFont", "TkHeadingFont",
                 "TkCaptionFont", "TkTooltipFont"):
        try:
            tkfont.nametofont(nome).configure(family=fam, size=10)
        except tk.TclError:
            pass
    negrito = (fam, 10, "bold")

    root.configure(bg=FUNDO)
    root.option_add("*Toplevel.background", FUNDO)
    root.option_add("*TCombobox*Listbox.background", FUNDO)
    root.option_add("*TCombobox*Listbox.foreground", TEXTO)
    root.option_add("*TCombobox*Listbox.selectBackground", DESTAQUE_CLARO)
    root.option_add("*TCombobox*Listbox.selectForeground", TEXTO)
    root.option_add("*TCombobox*Listbox.borderWidth", 0)
    root.option_add("*TCombobox*Listbox.font", (fam, 10))

    s = ttk.Style(root)
    s.theme_use("clam")

    s.configure(".", background=FUNDO, foreground=TEXTO, font=(fam, 10),
                bordercolor=BORDA, lightcolor=FUNDO, darkcolor=FUNDO, troughcolor=SUPERFICIE,
                focuscolor=DESTAQUE, selectbackground=DESTAQUE_CLARO, selectforeground=TEXTO,
                insertcolor=TEXTO, relief="flat")
    s.map(".", foreground=[("disabled", "#a0aab8")])

    s.configure("TFrame", background=FUNDO)
    s.configure("Barra.TFrame", background=SUPERFICIE)
    s.configure("TLabel", background=FUNDO, foreground=TEXTO)
    s.configure("Sutil.TLabel", foreground=SUTIL)
    s.configure("Titulo.TLabel", font=(fam, 13, "bold"))
    s.configure("TituloDialogo.TLabel", font=(fam, 12, "bold"))
    s.configure("Secao.TLabel", font=negrito, foreground=SUTIL)
    s.configure("Barra.TLabel", background=SUPERFICIE, foreground=SUTIL, padding=(12, 6))
    s.configure("BarraSecao.TLabel", background=SUPERFICIE, foreground=SUTIL, font=negrito)
    s.configure("Dica.TLabel", background=DESTAQUE_CLARO, foreground=PASTA, padding=(10, 6))
    s.configure("TSeparator", background=BORDA)

    # Botões
    s.configure("TButton", background=FUNDO, foreground=TEXTO, bordercolor=BORDA_FORTE,
                lightcolor=FUNDO, darkcolor=FUNDO, padding=(12, 6), borderwidth=1,
                focusthickness=0, anchor="center")
    s.map("TButton",
          background=[("pressed", "#e9eef5"), ("active", SUPERFICIE)],
          bordercolor=[("active", "#aab6c6"), ("focus", DESTAQUE)],
          lightcolor=[("pressed", "#e9eef5"), ("active", SUPERFICIE)],
          darkcolor=[("pressed", "#e9eef5"), ("active", SUPERFICIE)])

    s.configure("Destaque.TButton", background=DESTAQUE, foreground="#ffffff",
                bordercolor=DESTAQUE, lightcolor=DESTAQUE, darkcolor=DESTAQUE,
                font=(fam, 10, "bold"), padding=(18, 8))
    s.map("Destaque.TButton",
          background=[("disabled", "#93b4f5"), ("pressed", "#1e3fae"), ("active", DESTAQUE_HOVER)],
          bordercolor=[("active", DESTAQUE_HOVER)],
          lightcolor=[("pressed", "#1e3fae"), ("active", DESTAQUE_HOVER)],
          darkcolor=[("pressed", "#1e3fae"), ("active", DESTAQUE_HOVER)],
          foreground=[("disabled", "#ffffff")])

    s.configure("Local.TButton", background=SUPERFICIE, bordercolor=SUPERFICIE,
                lightcolor=SUPERFICIE, darkcolor=SUPERFICIE, anchor="w", padding=(10, 7))
    s.map("Local.TButton",
          background=[("pressed", MARCADO), ("active", DESTAQUE_CLARO)],
          foreground=[("active", DESTAQUE)],
          bordercolor=[("active", DESTAQUE_CLARO), ("focus", SUPERFICIE)],
          lightcolor=[("active", DESTAQUE_CLARO)], darkcolor=[("active", DESTAQUE_CLARO)])

    s.configure("Icone.TButton", padding=(8, 6))

    # Campos
    for estilo in ("TEntry", "TCombobox"):
        s.configure(estilo, fieldbackground=FUNDO, background=FUNDO, bordercolor=BORDA_FORTE,
                    lightcolor=FUNDO, darkcolor=FUNDO, padding=(8, 5), arrowcolor=SUTIL)
        s.map(estilo,
              bordercolor=[("focus", DESTAQUE)], lightcolor=[("focus", DESTAQUE)],
              fieldbackground=[("readonly", FUNDO), ("disabled", SUPERFICIE)],
              background=[("readonly", FUNDO), ("active", FUNDO)],
              foreground=[("disabled", "#a0aab8")],
              selectbackground=[("readonly", FUNDO)], selectforeground=[("readonly", TEXTO)])

    # Caixas de marcar / opções
    for estilo in ("TCheckbutton", "TRadiobutton"):
        s.configure(estilo, background=FUNDO, indicatorbackground=FUNDO,
                    indicatorforeground=FUNDO, upperbordercolor="#94a3b8",
                    lowerbordercolor="#94a3b8", indicatormargin=(0, 0, 8, 0), padding=(0, 3))
        s.map(estilo,
              background=[("active", FUNDO)],
              indicatorbackground=[("selected", DESTAQUE), ("pressed", DESTAQUE_CLARO)],
              upperbordercolor=[("selected", DESTAQUE), ("active", DESTAQUE)],
              lowerbordercolor=[("selected", DESTAQUE), ("active", DESTAQUE)])

    # Grupos
    s.configure("TLabelframe", background=FUNDO, bordercolor=BORDA, lightcolor=FUNDO,
                darkcolor=FUNDO, borderwidth=1, relief="solid")
    s.configure("TLabelframe.Label", background=FUNDO, foreground=TEXTO, font=negrito)

    # Abas
    s.configure("TNotebook", background=SUPERFICIE, bordercolor=BORDA, lightcolor=SUPERFICIE,
                darkcolor=SUPERFICIE, borderwidth=0, tabmargins=(12, 10, 12, 0))
    s.configure("TNotebook.Tab", background=SUPERFICIE, foreground=SUTIL, bordercolor=SUPERFICIE,
                lightcolor=SUPERFICIE, darkcolor=SUPERFICIE, padding=(20, 9), font=negrito,
                focuscolor=SUPERFICIE)
    s.map("TNotebook.Tab",
          background=[("selected", FUNDO), ("active", "#eef2f7")],
          foreground=[("selected", DESTAQUE), ("active", TEXTO)],
          bordercolor=[("selected", BORDA)],
          lightcolor=[("selected", DESTAQUE)],
          expand=[("selected", (0, 0, 0, 0))])

    # Listas
    s.configure("Treeview", background=FUNDO, fieldbackground=FUNDO, foreground=TEXTO,
                bordercolor=BORDA, lightcolor=FUNDO, darkcolor=FUNDO, rowheight=30,
                borderwidth=1, relief="solid")
    s.map("Treeview", background=[("selected", DESTAQUE_CLARO)],
          foreground=[("selected", TEXTO)])
    s.configure("Treeview.Heading", background=SUPERFICIE, foreground=SUTIL, font=negrito,
                bordercolor=BORDA, lightcolor=SUPERFICIE, darkcolor=SUPERFICIE,
                relief="flat", padding=(8, 7))
    s.map("Treeview.Heading", background=[("active", "#eaeff6")],
          foreground=[("active", TEXTO)], lightcolor=[("active", "#eaeff6")],
          darkcolor=[("active", "#eaeff6")])
    s.configure("Seletor.Treeview", rowheight=30)

    # Barras de rolagem finas
    for orient in ("Vertical", "Horizontal"):
        s.configure(f"{orient}.TScrollbar", background="#d5dce6", troughcolor=FUNDO,
                    bordercolor=FUNDO, lightcolor="#d5dce6", darkcolor="#d5dce6",
                    arrowcolor=SUTIL, arrowsize=12, gripcount=0, relief="flat")
        s.map(f"{orient}.TScrollbar",
              background=[("active", "#b4bfcd"), ("pressed", "#9aa7b8")],
              lightcolor=[("active", "#b4bfcd")], darkcolor=[("active", "#b4bfcd")])
    return s

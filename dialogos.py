"""Caixas de mensagem no mesmo padrão visual do app (substituem o messagebox do Tk)."""

import tkinter as tk
from tkinter import ttk

from tema import CLASSE_JANELA, DESTAQUE, FUNDO

LARGURA = 480  # todas as caixas de mensagem têm a mesma largura

TIPOS = {  # tipo: (símbolo, cor)
    "info": ("i", DESTAQUE),
    "sucesso": ("✓", "#16a34a"),
    "aviso": ("!", "#d97706"),
    "erro": ("✕", "#dc2626"),
    "pergunta": ("?", DESTAQUE),
}


class Dialogo(tk.Toplevel):
    def __init__(self, master, titulo, mensagem, tipo="info", botoes=(("OK", True),),
                 padrao=0, cancelar=None, campo=None):
        super().__init__(master, class_=CLASSE_JANELA, bg=FUNDO)
        self.withdraw()
        self.title(titulo)
        self.transient(master)
        self.resizable(False, False)
        self.configure(bg=FUNDO)
        self.resposta = cancelar

        corpo = ttk.Frame(self, padding=(24, 24, 24, 20))
        corpo.pack(fill="both", expand=True)
        simbolo, cor = TIPOS.get(tipo, TIPOS["info"])
        icone = tk.Canvas(corpo, width=40, height=40, bg=FUNDO, highlightthickness=0)
        icone.create_oval(2, 2, 38, 38, fill=cor, outline=cor)
        icone.create_text(20, 20, text=simbolo, fill="#ffffff", font=("TkDefaultFont", 15, "bold"))
        icone.pack(side="left", anchor="n", padx=(0, 16))
        textos = ttk.Frame(corpo)
        textos.pack(side="left", fill="both", expand=True)
        ttk.Label(textos, text=titulo, style="TituloDialogo.TLabel").pack(anchor="w")
        ttk.Label(textos, text=mensagem, wraplength=LARGURA - 120, justify="left").pack(
            anchor="w", pady=(6, 0))
        self.var_campo = None
        if campo is not None:
            self.var_campo = tk.StringVar(value=campo)
            entrada = ttk.Entry(textos, textvariable=self.var_campo)
            entrada.pack(fill="x", pady=(12, 0))
            entrada.select_range(0, "end")
            self.after(50, entrada.focus_set)

        ttk.Separator(self).pack(fill="x")
        base = ttk.Frame(self, style="Barra.TFrame", padding=(16, 12))
        base.pack(fill="x")
        self._botoes = []
        for i, (texto, valor) in enumerate(botoes):  # o 1º fica mais à direita
            bt = ttk.Button(base, text=texto, command=lambda v=valor: self._responder(v),
                            style="Destaque.TButton" if i == padrao else "TButton")
            bt.pack(side="right", padx=(8, 0))
            self._botoes.append(bt)

        self.bind("<Return>", lambda e: self._responder(botoes[padrao][1]))
        self.bind("<KP_Enter>", lambda e: self._responder(botoes[padrao][1]))
        self.bind("<Escape>", lambda e: self._responder(cancelar))
        self.protocol("WM_DELETE_WINDOW", lambda: self._responder(cancelar))

        self.update_idletasks()
        largura = max(LARGURA, self.winfo_reqwidth())
        altura = self.winfo_reqheight()
        try:
            x = master.winfo_rootx() + (master.winfo_width() - largura) // 2
            y = master.winfo_rooty() + (master.winfo_height() - altura) // 3
        except tk.TclError:
            x = y = 200
        self.geometry(f"{largura}x{altura}+{max(x, 0)}+{max(y, 0)}")
        self.deiconify()
        self.grab_set()
        if campo is None:
            self.focus_set()
        master.wait_window(self)

    def _responder(self, valor):
        if valor is True and self.var_campo is not None:
            valor = self.var_campo.get().strip()
        self.resposta = valor
        self.grab_release()
        self.destroy()


def _janela(master):
    # se houver um diálogo (Toplevel) ativo com grab, usa-o como pai
    try:
        atual = master.grab_current()
        if atual is not None:
            return atual.winfo_toplevel()
    except Exception:
        pass
    return master


def info(master, titulo, mensagem):
    Dialogo(_janela(master), titulo, mensagem, "info")


def sucesso(master, titulo, mensagem):
    Dialogo(_janela(master), titulo, mensagem, "sucesso")


def aviso(master, titulo, mensagem):
    Dialogo(_janela(master), titulo, mensagem, "aviso")


def erro(master, titulo, mensagem):
    Dialogo(_janela(master), titulo, mensagem, "erro")


def perguntar(master, titulo, mensagem, sim="Sim", nao="Não", tipo="pergunta"):
    d = Dialogo(_janela(master), titulo, mensagem, tipo,
                botoes=((sim, True), (nao, False)), padrao=0, cancelar=False)
    return bool(d.resposta)


def pedir_texto(master, titulo, mensagem, inicial="", ok="OK"):
    """Pede um texto; devolve a string digitada ou None se cancelar."""
    d = Dialogo(_janela(master), titulo, mensagem, "pergunta",
                botoes=((ok, True), ("Cancelar", None)), padrao=0, cancelar=None,
                campo=inicial)
    return d.resposta or None

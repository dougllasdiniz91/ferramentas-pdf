"""Janela grande para escolher PDFs, com marcação de vários arquivos e ordenação."""

import os
import subprocess
import sys
import tkinter as tk
from tkinter import ttk

from arquivos_info import (
    carregar_config, fmt_data, fmt_tamanho, info_arquivos, ordenar, salvar_config,
)
import dialogos
from tema import CLASSE_JANELA, FUNDO, JANELA_MINIMA, JANELA_PADRAO, MARCADO, PASTA

COLUNAS = (  # (chave, título, largura, âncora)
    ("nome", "Nome", 440, "w"),
    ("tamanho", "Tamanho", 90, "e"),
    ("modificado", "Modificado em", 140, "center"),
    ("criado", "Criado em", 140, "center"),
)
ROTULOS = {"nome": "Nome", "tamanho": "Tamanho", "modificado": "Data de modificação",
           "criado": "Data de criação"}
CAIXA_VAZIA, CAIXA_MARCADA = "☐", "☑"


def _pasta_xdg(nome, padrao):
    if sys.platform.startswith("linux"):
        try:
            p = subprocess.run(["xdg-user-dir", nome], capture_output=True, text=True,
                               timeout=2).stdout.strip()
            if p and os.path.isdir(p) and p != os.path.expanduser("~"):
                return p
        except Exception:
            pass
    p = os.path.expanduser(f"~/{padrao}")
    return p if os.path.isdir(p) else None


def _locais():
    locais = [("🏠  Pasta pessoal", os.path.expanduser("~"))]
    for xdg, padrao, rotulo in (
        ("DESKTOP", "Desktop", "🖥  Área de Trabalho"),
        ("DOCUMENTS", "Documents", "📄  Documentos"),
        ("DOWNLOAD", "Downloads", "⬇  Downloads"),
    ):
        p = _pasta_xdg(xdg, padrao)
        if p:
            locais.append((rotulo, p))
    locais.append(("💽  Raiz do sistema", os.path.abspath(os.sep)))
    return locais


class SeletorPDF(tk.Toplevel):
    def __init__(self, master, titulo, pasta, multiplo=True, modo="abrir", nome_inicial=""):
        super().__init__(master, class_=CLASSE_JANELA, bg=FUNDO)
        self.title(titulo)
        self.transient(master)
        self.modo = modo  # "abrir" | "salvar" | "pasta"
        self.multiplo = multiplo and modo == "abrir"
        self.nome_inicial = nome_inicial
        self.resultado = []
        self.historico = []
        self.pasta = None
        self.itens = []        # dicts: caminho, pasta(bool), tamanho, modificado, criado
        self.marcados = {}     # caminho -> None (dict mantém a ordem em que foram marcados)
        self.ancora = None     # último PDF clicado (para Shift+clique)
        self.ultimo_clique = None  # linha do último clique (para validar duplo clique)

        cfg = carregar_config()
        self.chave = cfg.get("seletor_ordem", "nome")
        if self.chave not in ROTULOS:
            self.chave = "nome"
        self.desc = bool(cfg.get("seletor_desc", False))
        self.minsize(*JANELA_MINIMA)
        # mesmo tamanho e posição da janela principal
        try:
            principal = master.winfo_toplevel()
            principal.update_idletasks()
            self.geometry(principal.geometry())
        except tk.TclError:
            self.geometry("%dx%d" % JANELA_PADRAO)

        self._montar()
        self.protocol("WM_DELETE_WINDOW", self.cancelar)
        self.bind("<Escape>", lambda e: self.cancelar())
        self.bind("<Alt-Left>", lambda e: self.voltar())
        self.bind("<Alt-Up>", lambda e: self.subir())
        self.bind("<BackSpace>", self._backspace)
        self.bind("<Control-l>", lambda e: (self.campo_pasta.focus_set(),
                                            self.campo_pasta.select_range(0, "end")))

        if not pasta or not os.path.isdir(pasta):
            pasta = os.path.expanduser("~")
        self.abrir_pasta(pasta, registrar=False)
        if self.modo == "salvar":
            self.campo_nome.focus_set()
            self.campo_nome.icursor("end")
            base = os.path.splitext(self.var_nome.get())[0]
            self.campo_nome.select_range(0, len(base))
        else:
            self.lista.focus_set()
        self.grab_set()

    # ----- interface -----
    def _montar(self):
        # Barra superior: navegação + caminho + filtro
        topo = ttk.Frame(self, padding=(12, 12, 12, 10))
        topo.pack(fill="x")
        self.bt_voltar = ttk.Button(topo, text="◀", width=3, style="Icone.TButton",
                                    command=self.voltar)
        self.bt_voltar.pack(side="left")
        ttk.Button(topo, text="⬆", width=3, style="Icone.TButton", command=self.subir).pack(
            side="left", padx=(6, 10))
        self.var_pasta = tk.StringVar()
        self.campo_pasta = ttk.Entry(topo, textvariable=self.var_pasta)
        self.campo_pasta.pack(side="left", fill="x", expand=True)
        self.campo_pasta.bind("<Return>", lambda e: self.abrir_pasta(
            os.path.expanduser(self.var_pasta.get().strip())))
        ttk.Label(topo, text="   🔍").pack(side="left")
        self.var_filtro = tk.StringVar()
        self.var_filtro.trace_add("write", lambda *a: self.mostrar())
        filtro = ttk.Entry(topo, textvariable=self.var_filtro, width=24)
        filtro.pack(side="left", padx=(4, 0))
        filtro.bind("<Escape>", lambda e: (self.var_filtro.set(""), "break")[1])
        ttk.Separator(self).pack(fill="x")

        meio = self._meio = ttk.Frame(self)
        meio.pack(fill="both", expand=True)

        # Locais à esquerda
        lado = ttk.Frame(meio, style="Barra.TFrame", padding=(10, 12))
        lado.pack(side="left", fill="y")
        ttk.Label(lado, text="LOCAIS", style="BarraSecao.TLabel").pack(
            anchor="w", padx=6, pady=(0, 6))
        for rotulo, caminho in _locais():
            ttk.Button(lado, text=rotulo, style="Local.TButton",
                       command=lambda c=caminho: self.abrir_pasta(c)).pack(fill="x", pady=1)
        ttk.Separator(meio, orient="vertical").pack(side="left", fill="y")

        direita = ttk.Frame(meio, padding=(12, 12, 12, 0))
        direita.pack(side="left", fill="both", expand=True)
        if self.multiplo:
            dica = ("☑  Clique nos PDFs para marcar vários (vale até em pastas diferentes)"
                    "   ·   Shift+clique: intervalo   ·   Ctrl+A: todos")
        elif self.modo == "salvar":
            dica = ("💾  Escolha a pasta e digite o nome do arquivo abaixo   ·   "
                    "Clique em um PDF para reaproveitar o nome dele")
        elif self.modo == "pasta":
            dica = ("📁  Entre na pasta desejada (duplo clique) e clique em “Usar esta pasta”"
                    "   ·   Também dá para criar uma nova pasta")
        else:
            dica = "📄  Clique no PDF desejado e depois em “Abrir” (ou dê um duplo clique)"
        ttk.Label(direita, style="Dica.TLabel", text=dica).pack(fill="x", pady=(0, 10))

        # Lista de arquivos
        quadro = ttk.Frame(direita)
        quadro.pack(fill="both", expand=True)
        self.lista = ttk.Treeview(
            quadro, columns=[c[0] for c in COLUNAS], show="headings", style="Seletor.Treeview",
            selectmode="browse",
        )
        for chave, titulo, larg, anc in COLUNAS:
            self.lista.heading(chave, text=titulo, anchor="w" if anc == "w" else "center",
                               command=lambda k=chave: self.clicou_coluna(k))
            self.lista.column(chave, width=larg, minwidth=60, anchor=anc,
                              stretch=chave == "nome")
        self.lista.tag_configure("pasta", foreground=PASTA)
        self.lista.tag_configure("marcado", background=MARCADO)
        rolagem = ttk.Scrollbar(quadro, orient="vertical", command=self.lista.yview)
        self.lista.configure(yscrollcommand=rolagem.set)
        self.lista.pack(side="left", fill="both", expand=True)
        rolagem.pack(side="right", fill="y")
        self.lista.bind("<Double-1>", self._duplo_clique)
        self.lista.bind("<Return>", self._enter)
        self.lista.bind("<<TreeviewSelect>>", lambda e: self._atualizar_contagem())
        if self.multiplo:
            self.lista.bind("<Button-1>", self._clique)
            self.lista.bind("<Control-Button-1>", self._clique)
            self.lista.bind("<Shift-Button-1>", lambda e: self._clique(e, intervalo=True))
            self.lista.bind("<space>", self._espaco)
            self.lista.bind("<Control-a>", lambda e: (self.marcar_todos(), "break")[1])
        else:
            self.lista.bind("<Button-1>", self._registrar_clique)

        self.contagem = ttk.Label(direita, text="", style="Sutil.TLabel")
        self.contagem.pack(anchor="w", pady=(6, 0))

        self.var_nome = tk.StringVar(value=self.nome_inicial)
        if self.modo == "salvar":
            linha = ttk.Frame(direita)
            linha.pack(fill="x", pady=(10, 0))
            ttk.Label(linha, text="Nome do arquivo:", style="TituloDialogo.TLabel").pack(
                side="left")
            self.campo_nome = ttk.Entry(linha, textvariable=self.var_nome)
            self.campo_nome.pack(side="left", fill="x", expand=True, padx=(10, 0))
            self.campo_nome.bind("<Return>", lambda e: self.confirmar())
            self.campo_nome.bind("<KP_Enter>", lambda e: self.confirmar())
            self.lista.bind("<<TreeviewSelect>>", self._usar_nome_selecionado, add="+")

        # Rodapé: botões de ação (à direita, sempre visíveis) + ordenação
        # (empacotado antes do meio para nunca sumir quando a janela encolhe)
        base = ttk.Frame(self, padding=12)
        base.pack(fill="x", side="bottom", before=self._meio)
        ttk.Separator(self).pack(fill="x", side="bottom", pady=(8, 0), before=self._meio)
        ttk.Button(base, text="Cancelar", command=self.cancelar).pack(side="right")
        texto_ok = {"salvar": "Salvar", "pasta": "Usar esta pasta"}.get(
            self.modo, "Adicionar" if self.multiplo else "Abrir")
        self.bt_ok = ttk.Button(base, text=texto_ok, style="Destaque.TButton",
                                command=self.confirmar)
        self.bt_ok.pack(side="right", padx=(0, 8))

        ttk.Label(base, text="Ordenar por", style="Sutil.TLabel").pack(side="left")
        self.var_ordem = tk.StringVar(value=ROTULOS[self.chave])
        combo = ttk.Combobox(base, textvariable=self.var_ordem, state="readonly", width=19,
                             values=list(ROTULOS.values()))
        combo.pack(side="left", padx=(8, 6))
        combo.bind("<<ComboboxSelected>>", lambda e: self.definir_ordem(
            next(k for k, v in ROTULOS.items() if v == self.var_ordem.get())))
        self.bt_direcao = ttk.Button(base, width=19, command=self.inverter)
        self.bt_direcao.pack(side="left")
        if self.multiplo:
            ttk.Button(base, text="☑ Marcar todos", command=self.marcar_todos).pack(
                side="left", padx=(16, 6))
            ttk.Button(base, text="☐ Desmarcar", command=self.desmarcar_todos).pack(side="left")
        if self.modo in ("salvar", "pasta"):
            ttk.Button(base, text="📁 Nova pasta", command=self.nova_pasta).pack(
                side="left", padx=(16, 0))

    # ----- navegação -----
    def abrir_pasta(self, pasta, registrar=True):
        pasta = os.path.abspath(pasta)
        if not os.path.isdir(pasta):
            self.contagem.config(text="Pasta não encontrada.")
            self.var_pasta.set(self.pasta or "")
            return
        try:
            entradas = list(os.scandir(pasta))
        except OSError as e:
            self.contagem.config(text=f"Sem acesso: {e.strerror}")
            self.var_pasta.set(self.pasta or "")
            return
        if registrar and self.pasta and self.pasta != pasta:
            self.historico.append(self.pasta)
        self.pasta = pasta
        self.ancora = None
        self.var_pasta.set(pasta)
        self.var_filtro.set("")

        pastas, pdfs = [], []
        for e in entradas:
            if e.name.startswith("."):
                continue
            try:
                if e.is_dir():
                    pastas.append(e.path)
                elif (self.modo != "pasta" and e.name.lower().endswith(".pdf")
                      and e.is_file()):
                    pdfs.append(e.path)
            except OSError:
                pass
        dados = info_arquivos(pastas + pdfs)
        conj_pastas = set(pastas)
        self.itens = []
        for c in pastas + pdfs:
            d = dados.get(c, {"tamanho": None, "modificado": None, "criado": None})
            self.itens.append({"caminho": c, "pasta": c in conj_pastas, **d})
            if c in conj_pastas:
                self.itens[-1]["tamanho"] = None
        self.bt_voltar.config(state="normal" if self.historico else "disabled")
        self.mostrar()

    def voltar(self):
        if self.historico:
            self.abrir_pasta(self.historico.pop(), registrar=False)

    def subir(self):
        if self.pasta:
            pai = os.path.dirname(self.pasta)
            if pai != self.pasta:
                self.abrir_pasta(pai)

    def _backspace(self, evento):
        if evento.widget is self.lista:
            self.subir()

    # ----- exibição / ordenação -----
    def _eh_pasta(self, iid):
        return iid.startswith("D:")

    def _caminho(self, iid):
        return iid[2:]

    def _texto_nome(self, d):
        nome = os.path.basename(d["caminho"])
        if d["pasta"]:
            return f"📁  {nome}"
        if self.multiplo:
            caixa = CAIXA_MARCADA if d["caminho"] in self.marcados else CAIXA_VAZIA
            return f"{caixa}  {nome}"
        return f"📄  {nome}"

    def mostrar(self):
        filtro = self.var_filtro.get().strip().lower()
        itens = [d for d in self.itens
                 if not filtro or filtro in os.path.basename(d["caminho"]).lower()]
        pastas = ordenar([d for d in itens if d["pasta"]], self.chave, self.desc)
        pdfs = ordenar([d for d in itens if not d["pasta"]], self.chave, self.desc)

        self.lista.delete(*self.lista.get_children())
        for d in pastas + pdfs:
            c = d["caminho"]
            tags = ("pasta",) if d["pasta"] else (("marcado",) if c in self.marcados else ())
            self.lista.insert(
                "", "end", iid=("D:" if d["pasta"] else "F:") + c, tags=tags,
                values=(self._texto_nome(d), fmt_tamanho(d["tamanho"]),
                        fmt_data(d["modificado"]), fmt_data(d["criado"])),
            )
        filhos = self.lista.get_children()
        if filhos:
            self.lista.focus(filhos[0])

        seta = "  ▼" if self.desc else "  ▲"
        for chave, titulo, _, _ in COLUNAS:
            self.lista.heading(chave, text=titulo + seta if chave == self.chave else titulo)
        self.var_ordem.set(ROTULOS[self.chave])
        if self.chave == "nome":
            self.bt_direcao.config(text="Z → A" if self.desc else "A → Z")
        elif self.chave == "tamanho":
            self.bt_direcao.config(text="Maior primeiro" if self.desc else "Menor primeiro")
        else:
            self.bt_direcao.config(text="Mais novo primeiro" if self.desc else "Mais antigo primeiro")
        self._atualizar_contagem()

    def definir_ordem(self, chave):
        if chave != self.chave:
            self.chave = chave
            # datas e tamanho: por padrão mostra os mais recentes/maiores primeiro
            self.desc = chave in ("modificado", "criado", "tamanho")
        self._salvar_ordem()
        self.mostrar()

    def clicou_coluna(self, chave):
        if chave == self.chave:
            self.inverter()
        else:
            self.definir_ordem(chave)

    def inverter(self):
        self.desc = not self.desc
        self._salvar_ordem()
        self.mostrar()

    def _salvar_ordem(self):
        salvar_config(seletor_ordem=self.chave, seletor_desc=self.desc)

    # ----- marcação (modo múltiplo) -----
    def _pdfs_visiveis(self):
        return [i for i in self.lista.get_children() if not self._eh_pasta(i)]

    def _redesenhar(self, iid):
        c = self._caminho(iid)
        marcado = c in self.marcados
        valores = list(self.lista.item(iid, "values"))
        valores[0] = f"{CAIXA_MARCADA if marcado else CAIXA_VAZIA}  {os.path.basename(c)}"
        self.lista.item(iid, values=valores, tags=("marcado",) if marcado else ())

    def _definir(self, iids, marcar):
        for iid in iids:
            c = self._caminho(iid)
            if marcar:
                self.marcados.setdefault(c, None)
            else:
                self.marcados.pop(c, None)
            self._redesenhar(iid)
        self._atualizar_contagem()

    def _registrar_clique(self, evento):
        self.ultimo_clique = self.lista.identify_row(evento.y) or None

    def _clique(self, evento, intervalo=False):
        if self.lista.identify_region(evento.x, evento.y) != "cell":
            self.ultimo_clique = None
            return None  # cabeçalho, divisória etc.: comportamento normal
        iid = self.lista.identify_row(evento.y)
        self.ultimo_clique = iid or None
        if not iid or self._eh_pasta(iid):
            return None  # pastas: seleção normal (duplo clique abre)
        self.lista.focus(iid)
        self.lista.selection_set(iid)
        if intervalo and self.ancora in self.lista.get_children():
            filhos = self.lista.get_children()
            a, b = sorted((filhos.index(self.ancora), filhos.index(iid)))
            self._definir([i for i in filhos[a:b + 1] if not self._eh_pasta(i)], True)
        else:
            self._definir([iid], self._caminho(iid) not in self.marcados)
            self.ancora = iid
        return "break"

    def _espaco(self, evento):
        iid = self.lista.focus()
        if iid and not self._eh_pasta(iid):
            self._definir([iid], self._caminho(iid) not in self.marcados)
            self.ancora = iid
        return "break"

    def marcar_todos(self):
        self._definir(self._pdfs_visiveis(), True)

    def desmarcar_todos(self):
        self.marcados.clear()
        for iid in self._pdfs_visiveis():
            self._redesenhar(iid)
        self._atualizar_contagem()

    # ----- contagem / confirmação -----
    def _atualizar_contagem(self):
        if self.modo == "pasta":
            n = len(self.lista.get_children())
            self.contagem.config(text=f"{n} subpasta(s)   •   Pasta atual: {self.pasta}")
            return
        n_pdfs = len(self._pdfs_visiveis())
        texto = f"{n_pdfs} PDF(s) nesta pasta"
        if self.multiplo:
            n = len(self.marcados)
            if n:
                fora = sum(1 for c in self.marcados if os.path.dirname(c) != self.pasta)
                texto += f"  •  {n} marcado(s)" + (f" ({fora} em outras pastas)" if fora else "")
            self.bt_ok.config(text=f"Adicionar ({n})" if n else "Adicionar")
        self.contagem.config(text=texto)

    def _duplo_clique(self, evento):
        if self.lista.identify_region(evento.x, evento.y) != "cell":
            return
        iid = self.lista.identify_row(evento.y)
        if not iid:
            return
        if iid != self.ultimo_clique:
            # dois cliques rápidos em linhas diferentes: são dois cliques simples
            if self.multiplo:
                return self._clique(evento, intervalo=bool(evento.state & 0x0001))  # Shift
            return self._registrar_clique(evento)
        self.ultimo_clique = None
        if self._eh_pasta(iid):
            self.abrir_pasta(self._caminho(iid))
        else:
            if self.multiplo:  # os dois cliques alternaram a marca; garante marcado
                self._definir([iid], True)
            self.lista.selection_set(iid)
            self.confirmar()

    def _enter(self, evento=None):
        sel = self.lista.selection()
        if sel and self._eh_pasta(sel[0]):
            self.abrir_pasta(self._caminho(sel[0]))
        else:
            self.confirmar()
        return "break"

    def _usar_nome_selecionado(self, evento=None):
        sel = self.lista.selection()
        if sel and not self._eh_pasta(sel[0]):
            self.var_nome.set(os.path.basename(self._caminho(sel[0])))

    def nova_pasta(self):
        nome = dialogos.pedir_texto(self, "Nova pasta", f"Criar uma pasta dentro de:\n{self.pasta}",
                                    "Nova pasta", ok="Criar")
        if not nome:
            return
        caminho = os.path.join(self.pasta, nome)
        try:
            os.makedirs(caminho)
        except OSError as e:
            dialogos.erro(self, "Não foi possível criar a pasta", str(e.strerror or e))
            return
        self.abrir_pasta(caminho)

    def confirmar(self):
        if self.modo == "pasta":
            self.resultado = [self.pasta]
            self.fechar()
            return
        if self.modo == "salvar":
            nome = self.var_nome.get().strip()
            if not nome:
                self.campo_nome.focus_set()
                return
            caminho = os.path.join(self.pasta, os.path.expanduser(nome))
            if not caminho.lower().endswith(".pdf"):
                caminho += ".pdf"
            if os.path.isdir(caminho):
                self.abrir_pasta(caminho)
                return
            if os.path.exists(caminho) and not dialogos.perguntar(
                self, "Substituir arquivo?",
                f"Já existe um arquivo chamado “{os.path.basename(caminho)}” nesta pasta.\n\n"
                "Deseja substituí-lo?", sim="Substituir", nao="Cancelar", tipo="aviso",
            ):
                return
            self.resultado = [caminho]
            self.fechar()
            return
        sel = self.lista.selection()
        foco = sel[0] if sel else ""
        if self.multiplo and self.marcados:
            self.resultado = [c for c in self.marcados if os.path.isfile(c)]
        elif foco and not self._eh_pasta(foco):
            self.resultado = [self._caminho(foco)]
        elif foco and self._eh_pasta(foco):
            self.abrir_pasta(self._caminho(foco))
            return
        else:
            return
        self.fechar()

    def cancelar(self):
        self.resultado = []
        self.fechar()

    def fechar(self):
        try:
            salvar_config(ultima_pasta=self.pasta)
        except Exception:
            pass
        self.grab_release()
        self.destroy()


def escolher_pdfs(master, titulo="Escolha os PDFs", pasta=None, multiplo=True):
    """Abre o seletor e devolve a lista de caminhos escolhidos ([] se cancelar)."""
    janela = SeletorPDF(master, titulo, pasta, multiplo)
    master.wait_window(janela)
    return janela.resultado


def salvar_pdf(master, titulo="Salvar PDF como", pasta=None, nome="documento.pdf"):
    """Pergunta onde salvar; devolve o caminho escolhido ou None."""
    janela = SeletorPDF(master, titulo, pasta, modo="salvar", nome_inicial=nome)
    master.wait_window(janela)
    return janela.resultado[0] if janela.resultado else None


def escolher_pasta(master, titulo="Escolha a pasta", pasta=None):
    """Pergunta uma pasta; devolve o caminho escolhido ou None."""
    janela = SeletorPDF(master, titulo, pasta, modo="pasta")
    master.wait_window(janela)
    return janela.resultado[0] if janela.resultado else None

#!/usr/bin/env python3
"""Ferramentas PDF - unir e separar arquivos PDF com interface gráfica."""

import os
import subprocess
import sys
import tkinter as tk
from tkinter import messagebox, ttk

try:
    from pdf_core import ErroPDF, contar_paginas, separar_pdf, unir_pdfs
    from arquivos_info import (
        CRITERIOS, carregar_config, fmt_data, fmt_tamanho, info_arquivos, ordenar,
        salvar_config,
    )
    import dialogos
    from seletor import escolher_pasta, escolher_pdfs, salvar_pdf
    from tema import (
        CLASSE_JANELA, JANELA_MINIMA, JANELA_PADRAO, aplicar_icone, aplicar_tema,
    )
except ImportError:
    _r = tk.Tk()
    _r.withdraw()
    messagebox.showerror(
        "Dependência ausente",
        "A biblioteca 'pypdf' não está instalada.\n\nInstale com:\n  pip install pypdf",
    )
    sys.exit(1)

APP_NOME = "Ferramentas PDF"


def abrir_no_gerenciador(caminho):
    """Abre uma pasta (ou arquivo) no gerenciador do sistema."""
    try:
        if sys.platform.startswith("win"):
            os.startfile(caminho)  # type: ignore[attr-defined]
        elif sys.platform == "darwin":
            subprocess.Popen(["open", caminho])
        else:
            subprocess.Popen(["xdg-open", caminho])
    except Exception:
        pass


class AbaUnir(ttk.Frame):
    COLUNAS = (
        ("n", "#", 40, "center"),
        ("nome", "Arquivo", 280, "w"),
        ("paginas", "Páginas", 70, "center"),
        ("tamanho", "Tamanho", 80, "e"),
        ("modificado", "Modificado em", 130, "center"),
        ("criado", "Criado em", 130, "center"),
        ("pasta", "Pasta", 200, "w"),
    )

    def __init__(self, master, app):
        super().__init__(master, padding=12)
        self.app = app
        self.arquivos = []  # dicts: caminho, paginas, tamanho, modificado, criado
        cfg = carregar_config()
        rotulos = dict(CRITERIOS)
        self.var_ordem = tk.StringVar(value=rotulos.get(cfg.get("unir_ordem"), "Nome"))
        self.var_desc = tk.BooleanVar(value=bool(cfg.get("unir_desc", False)))

        ttk.Label(
            self,
            text="Adicione os PDFs e organize a ordem. Eles serão unidos de cima para baixo.",
        ).grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 8))

        # Lista de arquivos
        quadro = ttk.Frame(self)
        quadro.grid(row=1, column=0, sticky="nsew")
        self.lista = ttk.Treeview(
            quadro, columns=[c[0] for c in self.COLUNAS], show="headings",
            selectmode="extended", style="Seletor.Treeview",
        )
        for col, titulo, larg, anc in self.COLUNAS:
            ordenavel = col in dict(CRITERIOS)
            self.lista.heading(col, text=titulo, anchor="w" if anc == "w" else "center", command=(
                (lambda k=col: self.clicou_coluna(k)) if ordenavel else ""))
            self.lista.column(col, width=larg, minwidth=40, anchor=anc,
                              stretch=col in ("nome", "pasta"))
        barra = ttk.Scrollbar(quadro, orient="vertical", command=self.lista.yview)
        self.lista.configure(yscrollcommand=barra.set)
        self.lista.pack(side="left", fill="both", expand=True)
        barra.pack(side="right", fill="y")
        self.lista.bind("<Delete>", lambda e: self.remover())

        # Botões laterais
        lado = ttk.Frame(self, padding=(10, 0, 0, 0))
        lado.grid(row=1, column=1, sticky="n")
        for texto, cmd in (
            ("➕ Adicionar…", self.adicionar),
            ("➖ Remover", self.remover),
            ("⬆ Subir", lambda: self.mover(-1)),
            ("⬇ Descer", lambda: self.mover(1)),
            ("🗑 Limpar", self.limpar),
        ):
            ttk.Button(lado, text=texto, command=cmd, width=18).pack(fill="x", pady=2)

        caixa = ttk.LabelFrame(lado, text=" Ordenar por ", padding=8)
        caixa.pack(fill="x", pady=(14, 0))
        ttk.Combobox(caixa, textvariable=self.var_ordem, state="readonly", width=18,
                     values=[r for _, r in CRITERIOS]).pack(fill="x")
        ttk.Checkbutton(caixa, text="Ordem decrescente", variable=self.var_desc).pack(
            anchor="w", pady=(6, 4))
        ttk.Button(caixa, text="⇅ Ordenar", command=self.ordenar).pack(fill="x")
        ttk.Label(lado, text="Dica: clique no título\nde uma coluna para\nordenar por ela.",
                  style="Sutil.TLabel", justify="left").pack(anchor="w", pady=(10, 0))

        # Rodapé
        rodape = ttk.Frame(self)
        rodape.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(10, 0))
        self.resumo = ttk.Label(rodape, text="Nenhum arquivo adicionado.")
        self.resumo.pack(side="left")
        ttk.Button(rodape, text="Unir PDFs…", style="Destaque.TButton",
                   command=self.unir).pack(side="right")

        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

    # ----- ações -----
    def adicionar(self, caminhos=None):
        if caminhos is None:
            caminhos = escolher_pdfs(self.app, "Escolha os PDFs para unir", self.app.ultima_pasta)
        erros = []
        dados = info_arquivos(caminhos)
        for c in caminhos:
            try:
                d = {"caminho": c, "paginas": contar_paginas(c),
                     **dados.get(c, {"tamanho": None, "modificado": None, "criado": None})}
                self.arquivos.append(d)
                self.app.ultima_pasta = os.path.dirname(c)
            except ErroPDF as e:
                erros.append(str(e))
        self.atualizar()
        if erros:
            dialogos.aviso(self.app, "Alguns arquivos não foram adicionados",
                           "\n\n".join(erros))

    def selecionados(self):
        return sorted(self.lista.index(i) for i in self.lista.selection())

    def remover(self):
        for i in reversed(self.selecionados()):
            del self.arquivos[i]
        self.atualizar()

    def mover(self, passo):
        sel = self.selecionados()
        if not sel:
            return
        if (passo < 0 and sel[0] == 0) or (passo > 0 and sel[-1] == len(self.arquivos) - 1):
            return
        for i in (sel if passo < 0 else reversed(sel)):
            self.arquivos[i], self.arquivos[i + passo] = self.arquivos[i + passo], self.arquivos[i]
        self.atualizar([i + passo for i in sel])

    def chave_ordem(self):
        return next(k for k, r in CRITERIOS if r == self.var_ordem.get())

    def ordenar(self):
        chave, desc = self.chave_ordem(), self.var_desc.get()
        salvar_config(unir_ordem=chave, unir_desc=desc)
        self.arquivos = ordenar(self.arquivos, chave, desc)
        self.atualizar()
        rotulo = self.var_ordem.get().lower()
        self.app.status(f"Lista ordenada por {rotulo} ({'decrescente' if desc else 'crescente'}).")

    def clicou_coluna(self, chave):
        if chave == self.chave_ordem():
            self.var_desc.set(not self.var_desc.get())
        else:
            self.var_ordem.set(dict(CRITERIOS)[chave])
            self.var_desc.set(chave in ("modificado", "criado", "tamanho"))
        self.ordenar()

    def limpar(self):
        self.arquivos.clear()
        self.atualizar()

    def atualizar(self, selecionar=()):
        self.lista.delete(*self.lista.get_children())
        ids = []
        for n, d in enumerate(self.arquivos, 1):
            c = d["caminho"]
            ids.append(self.lista.insert("", "end", values=(
                n, os.path.basename(c), d["paginas"], fmt_tamanho(d["tamanho"]),
                fmt_data(d["modificado"]), fmt_data(d["criado"]), os.path.dirname(c),
            )))
        for i in selecionar:
            self.lista.selection_add(ids[i])
            self.lista.see(ids[i])
        if self.arquivos:
            total = sum(d["paginas"] for d in self.arquivos)
            self.resumo.config(text=f"{len(self.arquivos)} arquivo(s) • {total} página(s) no total")
        else:
            self.resumo.config(text="Nenhum arquivo adicionado.")

    def unir(self):
        if len(self.arquivos) < 2:
            dialogos.info(self.app, "Poucos arquivos",
                          "Adicione pelo menos dois PDFs para unir.")
            return
        destino = salvar_pdf(self.app, "Salvar PDF unido como", self.app.ultima_pasta,
                             "unido.pdf")
        if not destino:
            return
        entradas = {os.path.abspath(d["caminho"]) for d in self.arquivos}
        if os.path.abspath(destino) in entradas:
            dialogos.erro(self.app, "Nome inválido",
                          "Escolha um nome diferente dos arquivos que serão unidos.")
            return
        with self.app.ocupado("Unindo PDFs…"):
            try:
                paginas = unir_pdfs([d["caminho"] for d in self.arquivos], destino)
            except (ErroPDF, OSError) as e:
                dialogos.erro(self.app, "Não foi possível unir os PDFs", str(e))
                return
        self.app.status(f"PDF criado: {destino}")
        if dialogos.perguntar(
            self.app, "PDF unido com sucesso",
            f"{paginas} página(s) salvas em:\n{destino}\n\nDeseja abrir o arquivo?",
            sim="Abrir arquivo", nao="Fechar", tipo="sucesso",
        ):
            abrir_no_gerenciador(destino)


class AbaSeparar(ttk.Frame):
    MODOS = (
        ("cada", "Uma página por arquivo", ""),
        ("intervalos", "Um arquivo por intervalo", "Ex.: 1-3, 4-7, 8-"),
        ("a_cada_n", "A cada N páginas", "Ex.: 2  (gera arquivos de 2 em 2 páginas)"),
        ("extrair", "Extrair páginas para um único arquivo", "Ex.: 1, 3, 5-9"),
    )

    def __init__(self, master, app):
        super().__init__(master, padding=12)
        self.app = app
        self.total = 0
        self.arquivo = tk.StringVar()
        self.pasta = tk.StringVar()
        self.modo = tk.StringVar(value="cada")
        self.param = tk.StringVar()

        # Arquivo de origem
        caixa = ttk.LabelFrame(self, text=" 1. PDF de origem ", padding=10)
        caixa.pack(fill="x")
        ttk.Entry(caixa, textvariable=self.arquivo, state="readonly").pack(
            side="left", fill="x", expand=True)
        ttk.Button(caixa, text="Escolher…", command=self.escolher_arquivo).pack(
            side="left", padx=(8, 0))
        self.info = ttk.Label(self, text="", style="Sutil.TLabel")
        self.info.pack(anchor="w", pady=(4, 8))

        # Modo
        caixa = ttk.LabelFrame(self, text=" 2. Como separar ", padding=10)
        caixa.pack(fill="x")
        for valor, texto, _ in self.MODOS:
            ttk.Radiobutton(caixa, text=texto, value=valor, variable=self.modo,
                            command=self.mudou_modo).pack(anchor="w", pady=1)
        linha = ttk.Frame(caixa)
        linha.pack(fill="x", pady=(8, 0))
        self.rotulo_param = ttk.Label(linha, text="Páginas:")
        self.rotulo_param.pack(side="left")
        self.campo_param = ttk.Entry(linha, textvariable=self.param, width=30)
        self.campo_param.pack(side="left", padx=8)
        self.dica = ttk.Label(linha, text="", style="Sutil.TLabel")
        self.dica.pack(side="left")

        # Pasta de saída
        caixa = ttk.LabelFrame(self, text=" 3. Pasta de destino ", padding=10)
        caixa.pack(fill="x", pady=(8, 0))
        ttk.Entry(caixa, textvariable=self.pasta).pack(side="left", fill="x", expand=True)
        ttk.Button(caixa, text="Escolher…", command=self.escolher_pasta).pack(
            side="left", padx=(8, 0))

        ttk.Button(self, text="Separar PDF", style="Destaque.TButton",
                   command=self.separar).pack(anchor="e", pady=(12, 0))
        self.mudou_modo()

    def escolher_arquivo(self, caminho=None):
        if caminho is None:
            escolhidos = escolher_pdfs(self.app, "Escolha o PDF para separar",
                                       self.app.ultima_pasta, multiplo=False)
            caminho = escolhidos[0] if escolhidos else None
        if not caminho:
            return
        try:
            self.total = contar_paginas(caminho)
        except ErroPDF as e:
            dialogos.erro(self.app, "Não foi possível abrir o PDF", str(e))
            return
        self.arquivo.set(caminho)
        self.app.ultima_pasta = os.path.dirname(caminho)
        base = os.path.splitext(os.path.basename(caminho))[0]
        self.pasta.set(os.path.join(os.path.dirname(caminho), f"{base}_separado"))
        self.info.config(text=f"{self.total} página(s)")

    def escolher_pasta(self):
        inicial = self.pasta.get().strip() or self.app.ultima_pasta
        while inicial and not os.path.isdir(inicial) and os.path.dirname(inicial) != inicial:
            inicial = os.path.dirname(inicial)  # pasta ainda não existe: começa pela mãe
        p = escolher_pasta(self.app, "Escolha a pasta de destino", inicial)
        if p:
            self.pasta.set(p)

    def mudou_modo(self):
        modo = self.modo.get()
        dica = dict((v, d) for v, _, d in self.MODOS)[modo]
        ativo = modo != "cada"
        self.campo_param.config(state="normal" if ativo else "disabled")
        self.rotulo_param.config(text="Nº de páginas:" if modo == "a_cada_n" else "Páginas:")
        self.dica.config(text=dica)

    def separar(self):
        if not self.arquivo.get():
            dialogos.info(self.app, "Nenhum PDF escolhido",
                          "Escolha primeiro o PDF que deseja separar.")
            return
        if not self.pasta.get().strip():
            dialogos.info(self.app, "Falta a pasta de destino",
                          "Escolha a pasta onde os arquivos serão salvos.")
            return
        pasta = self.pasta.get().strip()
        with self.app.ocupado("Separando PDF…"):
            try:
                criados = separar_pdf(self.arquivo.get(), pasta, self.modo.get(), self.param.get())
            except (ErroPDF, OSError) as e:
                dialogos.erro(self.app, "Não foi possível separar o PDF", str(e))
                return
        self.app.status(f"{len(criados)} arquivo(s) criado(s) em {pasta}")
        if dialogos.perguntar(
            self.app, "PDF separado com sucesso",
            f"{len(criados)} arquivo(s) criado(s) em:\n{pasta}\n\nDeseja abrir a pasta?",
            sim="Abrir pasta", nao="Fechar", tipo="sucesso",
        ):
            abrir_no_gerenciador(pasta)


class _Ocupado:
    def __init__(self, app, msg):
        self.app, self.msg = app, msg

    def __enter__(self):
        self.app.status(self.msg)
        self.app.config(cursor="watch")
        self.app.update()

    def __exit__(self, *exc):
        self.app.config(cursor="")
        self.app.status("Pronto.")
        return False


class App(tk.Tk):
    def __init__(self, arquivos_iniciais=()):
        super().__init__(className=CLASSE_JANELA)
        self.title(APP_NOME)
        cfg = carregar_config()
        self.minsize(*JANELA_MINIMA)
        geo = cfg.get("janela_geometria", "")
        try:
            w, h = (int(v) for v in geo.split("x"))
            if w < JANELA_MINIMA[0] or h < JANELA_MINIMA[1]:
                raise ValueError
        except ValueError:
            w, h = JANELA_PADRAO
        self.geometry(f"{w}x{h}")
        self.protocol("WM_DELETE_WINDOW", self.fechar)
        pasta = cfg.get("ultima_pasta")
        self.ultima_pasta = pasta if pasta and os.path.isdir(pasta) else os.path.expanduser("~")

        aplicar_tema(self)
        aplicar_icone(self)

        abas = ttk.Notebook(self)
        abas.pack(fill="both", expand=True)
        self.aba_unir = AbaUnir(abas, self)
        self.aba_separar = AbaSeparar(abas, self)
        abas.add(self.aba_unir, text="  Unir PDFs  ")
        abas.add(self.aba_separar, text="  Separar PDF  ")

        ttk.Separator(self).pack(fill="x")
        self.barra = ttk.Label(self, text="Pronto.", anchor="w", style="Barra.TLabel")
        self.barra.pack(fill="x")

        pdfs = [a for a in arquivos_iniciais if a.lower().endswith(".pdf") and os.path.isfile(a)]
        if len(pdfs) == 1:
            self.aba_separar.escolher_arquivo(pdfs[0])
            abas.select(self.aba_separar)
        elif pdfs:
            self.aba_unir.adicionar(pdfs)

    def fechar(self):
        if self.state() == "normal":
            salvar_config(janela_geometria=f"{self.winfo_width()}x{self.winfo_height()}")
        self.destroy()

    def status(self, texto):
        self.barra.config(text=texto)

    def ocupado(self, msg):
        return _Ocupado(self, msg)


def main():
    App(sys.argv[1:]).mainloop()


if __name__ == "__main__":
    main()

"""Funções de manipulação de PDF (sem interface), usadas pela aplicação."""

import os
import re

from pypdf import PdfReader, PdfWriter


class ErroPDF(Exception):
    """Erro amigável para exibir ao usuário."""


def abrir_pdf(caminho):
    try:
        leitor = PdfReader(caminho)
    except Exception as e:  # arquivo corrompido ou não-PDF
        raise ErroPDF(f"Não foi possível abrir '{os.path.basename(caminho)}':\n{e}")
    if leitor.is_encrypted:
        try:
            if not leitor.decrypt(""):
                raise ErroPDF(f"'{os.path.basename(caminho)}' está protegido por senha.")
        except ErroPDF:
            raise
        except Exception:
            raise ErroPDF(f"'{os.path.basename(caminho)}' está protegido por senha.")
    return leitor


def contar_paginas(caminho):
    return len(abrir_pdf(caminho).pages)


def unir_pdfs(caminhos, destino):
    """Junta os PDFs na ordem informada em um único arquivo."""
    if len(caminhos) < 1:
        raise ErroPDF("Adicione pelo menos um arquivo PDF.")
    escritor = PdfWriter()
    for caminho in caminhos:
        for pagina in abrir_pdf(caminho).pages:
            escritor.add_page(pagina)
    with open(destino, "wb") as f:
        escritor.write(f)
    return len(escritor.pages)


def interpretar_intervalos(texto, total):
    """Converte '1-3, 5, 8-' em [(1, 3), (5, 5), (8, total)] (numeração a partir de 1)."""
    texto = texto.strip()
    if not texto:
        raise ErroPDF("Informe as páginas. Exemplo: 1-3, 5, 8-10")
    intervalos = []
    for parte in re.split(r"[;,]", texto):
        parte = parte.strip().replace(" ", "")
        if not parte:
            continue
        m = re.fullmatch(r"(\d*)-(\d*)|(\d+)", parte)
        if not m or parte == "-":
            raise ErroPDF(f"Trecho inválido: '{parte}'. Use algo como 1-3, 5, 8-10")
        if m.group(3):
            ini = fim = int(m.group(3))
        else:
            ini = int(m.group(1)) if m.group(1) else 1
            fim = int(m.group(2)) if m.group(2) else total
        if ini < 1 or fim > total or ini > fim:
            raise ErroPDF(f"Intervalo '{parte}' fora do documento (1 a {total}).")
        intervalos.append((ini, fim))
    if not intervalos:
        raise ErroPDF("Informe as páginas. Exemplo: 1-3, 5, 8-10")
    return intervalos


def _salvar(leitor, paginas, destino):
    escritor = PdfWriter()
    for i in paginas:  # índices base 0
        escritor.add_page(leitor.pages[i])
    with open(destino, "wb") as f:
        escritor.write(f)


def separar_pdf(caminho, pasta_saida, modo, parametro=""):
    """
    Separa um PDF. Modos:
      'cada'       -> um arquivo por página
      'intervalos' -> um arquivo para cada intervalo (ex.: '1-3, 4-6')
      'a_cada_n'   -> blocos de N páginas (parametro = N)
      'extrair'    -> um único arquivo só com as páginas escolhidas
    Retorna a lista de arquivos criados.
    """
    leitor = abrir_pdf(caminho)
    total = len(leitor.pages)
    base = os.path.splitext(os.path.basename(caminho))[0]
    os.makedirs(pasta_saida, exist_ok=True)
    largura = len(str(total))
    criados = []

    def nome(sufixo):
        return os.path.join(pasta_saida, f"{base}_{sufixo}.pdf")

    if modo == "cada":
        grupos = [(p, p) for p in range(1, total + 1)]
    elif modo == "intervalos":
        grupos = interpretar_intervalos(parametro, total)
    elif modo == "a_cada_n":
        try:
            n = int(str(parametro).strip())
            assert n >= 1
        except Exception:
            raise ErroPDF("Informe um número inteiro de páginas maior que zero.")
        grupos = [(i, min(i + n - 1, total)) for i in range(1, total + 1, n)]
    elif modo == "extrair":
        intervalos = interpretar_intervalos(parametro, total)
        paginas = [p - 1 for ini, fim in intervalos for p in range(ini, fim + 1)]
        destino = nome("extraido")
        _salvar(leitor, paginas, destino)
        return [destino]
    else:
        raise ErroPDF(f"Modo desconhecido: {modo}")

    for ini, fim in grupos:
        if ini == fim:
            sufixo = f"pag{ini:0{largura}d}"
        else:
            sufixo = f"pag{ini:0{largura}d}-{fim:0{largura}d}"
        destino = nome(sufixo)
        _salvar(leitor, range(ini - 1, fim), destino)
        criados.append(destino)
    return criados

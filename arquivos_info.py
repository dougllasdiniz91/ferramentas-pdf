"""Metadados de arquivos (tamanho, modificação, criação) e preferências do app."""

import json
import os
import subprocess
import sys
import time

CONFIG = os.path.join(
    os.environ.get("APPDATA") or os.environ.get("XDG_CONFIG_HOME")
    or os.path.expanduser("~/.config"),
    "ferramentas-pdf", "config.json",
)


def carregar_config():
    try:
        with open(CONFIG, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def salvar_config(**valores):
    dados = carregar_config()
    dados.update(valores)
    try:
        os.makedirs(os.path.dirname(CONFIG), exist_ok=True)
        with open(CONFIG, "w", encoding="utf-8") as f:
            json.dump(dados, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


def _criacao_linux(caminhos):
    """Data de criação via `stat -c %W` (statx), em lote. Retorna {caminho: ts|None}."""
    res = {}
    caminhos = list(caminhos)
    for i in range(0, len(caminhos), 400):
        lote = caminhos[i:i + 400]
        try:
            saida = subprocess.run(
                ["stat", "-c", "%W", "--", *lote], capture_output=True, text=True, timeout=10
            ).stdout.split("\n")
        except Exception:
            saida = []
        if len(saida) < len(lote):  # algum falhou: refaz um a um
            saida = []
            for c in lote:
                try:
                    saida.append(subprocess.run(
                        ["stat", "-c", "%W", "--", c], capture_output=True, text=True, timeout=5
                    ).stdout.strip())
                except Exception:
                    saida.append("")
        for c, v in zip(lote, saida):
            try:
                ts = int(v.strip())
                res[c] = ts if ts > 0 else None
            except ValueError:
                res[c] = None
    return res


def info_arquivos(caminhos):
    """Retorna {caminho: {"tamanho", "modificado", "criado"}} (criado pode ser None)."""
    info = {}
    for c in caminhos:
        try:
            s = os.stat(c)
        except OSError:
            continue
        info[c] = {
            "tamanho": s.st_size,
            "modificado": s.st_mtime,
            "criado": getattr(s, "st_birthtime", None)
            or (s.st_ctime if sys.platform.startswith("win") else None),
        }
    faltando = [c for c, d in info.items() if d["criado"] is None]
    if faltando and sys.platform.startswith("linux"):
        for c, ts in _criacao_linux(faltando).items():
            info[c]["criado"] = ts
    return info


def fmt_data(ts):
    return time.strftime("%d/%m/%Y %H:%M", time.localtime(ts)) if ts else "—"


def fmt_tamanho(n):
    if n is None:
        return ""
    for unidade in ("B", "KB", "MB", "GB"):
        if n < 1024 or unidade == "GB":
            return f"{n:.0f} {unidade}" if unidade == "B" else f"{n:.1f} {unidade}"
        n /= 1024


CRITERIOS = (  # (chave, rótulo)
    ("nome", "Nome"),
    ("modificado", "Data de modificação"),
    ("criado", "Data de criação"),
    ("tamanho", "Tamanho"),
    ("paginas", "Nº de páginas"),
)


def ordenar(itens, chave, decrescente=False):
    """Ordena dicts por `chave`; valores ausentes (None) ficam sempre no fim."""
    def nome(d):
        return os.path.basename(d["caminho"]).lower()

    if chave == "nome":
        return sorted(itens, key=nome, reverse=decrescente)
    com = [d for d in itens if d.get(chave) is not None]
    sem = [d for d in itens if d.get(chave) is None]
    com.sort(key=lambda d: (d[chave], nome(d)), reverse=decrescente)
    return com + sorted(sem, key=nome)

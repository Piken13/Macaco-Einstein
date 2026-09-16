"""
╔══════════════════════════════════════════════════════════════╗
║         🔄 CONVERSOR UNIVERSAL DE ARQUIVOS — GUI 🔄          ║
║                                                              ║
║  Suporta: Imagens, PDFs, Word, Texto, HTML, Ícones, MD       ║
╚══════════════════════════════════════════════════════════════╝

Dependências:
    pip install Pillow pymupdf python-docx reportlab markdown
"""

import os
import sys
import re
import threading
from pathlib import Path
from typing import Optional

import tkinter as tk
from tkinter import ttk, filedialog, messagebox

# ──────────────────────────────────────────────────────────────
# Importações com tratamento de erro
# ──────────────────────────────────────────────────────────────

MISSING_DEPS = []

try:
    from PIL import Image, ImageTk
except ImportError:
    MISSING_DEPS.append("Pillow")

try:
    import fitz  # PyMuPDF
except ImportError:
    MISSING_DEPS.append("pymupdf")

try:
    from docx import Document as DocxDocument
except ImportError:
    MISSING_DEPS.append("python-docx")

try:
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen import canvas as rl_canvas
    from reportlab.lib.units import cm
except ImportError:
    MISSING_DEPS.append("reportlab")

try:
    import markdown as md_lib
except ImportError:
    MISSING_DEPS.append("markdown")


# ──────────────────────────────────────────────────────────────
# Constantes
# ──────────────────────────────────────────────────────────────

IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".bmp", ".gif", ".tiff", ".tif", ".webp", ".ico"}
DOCUMENT_EXTENSIONS = {".pdf", ".docx", ".txt", ".html", ".htm", ".md"}
ALL_EXTENSIONS = IMAGE_EXTENSIONS | DOCUMENT_EXTENSIONS

# Mapa de conversões possíveis: extensão_entrada → [extensões_saída]
CONVERSION_MAP = {
    ".png":  [".jpg", ".jpeg", ".bmp", ".gif", ".tiff", ".webp", ".ico", ".pdf"],
    ".jpg":  [".png", ".bmp", ".gif", ".tiff", ".webp", ".ico", ".pdf"],
    ".jpeg": [".png", ".bmp", ".gif", ".tiff", ".webp", ".ico", ".pdf"],
    ".bmp":  [".png", ".jpg", ".gif", ".tiff", ".webp", ".ico", ".pdf"],
    ".gif":  [".png", ".jpg", ".bmp", ".tiff", ".webp", ".ico", ".pdf"],
    ".tiff": [".png", ".jpg", ".bmp", ".gif", ".webp", ".ico", ".pdf"],
    ".tif":  [".png", ".jpg", ".bmp", ".gif", ".webp", ".ico", ".pdf"],
    ".webp": [".png", ".jpg", ".bmp", ".gif", ".tiff", ".ico", ".pdf"],
    ".ico":  [".png", ".jpg", ".bmp", ".gif", ".tiff", ".webp"],
    ".pdf":  [".png", ".jpg", ".bmp", ".gif", ".tiff", ".webp", ".txt", ".docx", ".html"],
    ".docx": [".pdf", ".txt", ".html"],
    ".txt":  [".pdf", ".docx", ".html"],
    ".html": [".txt", ".pdf", ".docx"],
    ".htm":  [".txt", ".pdf", ".docx"],
    ".md":   [".html", ".pdf", ".txt"],
}

FORMAT_LABELS = {
    ".png": "PNG (Imagem)", ".jpg": "JPG (Imagem)", ".jpeg": "JPEG (Imagem)",
    ".bmp": "BMP (Imagem)", ".gif": "GIF (Imagem)", ".tiff": "TIFF (Imagem)",
    ".webp": "WebP (Imagem)", ".ico": "ICO (Ícone)", ".pdf": "PDF (Documento)",
    ".docx": "Word (DOCX)", ".txt": "Texto (TXT)", ".html": "HTML (Web)",
    ".md": "Markdown (MD)",
}


# ══════════════════════════════════════════════════════════════
#  FUNÇÕES DE CONVERSÃO (mesmo motor do CLI)
# ══════════════════════════════════════════════════════════════

def converter_imagem_para_imagem(entrada, saida, qualidade=95, redimensionar=None):
    img = Image.open(entrada)
    ext_saida = Path(saida).suffix.lower()
    if ext_saida in {".jpg", ".jpeg", ".bmp"} and img.mode in ("RGBA", "P"):
        img = img.convert("RGB")
    if redimensionar:
        img = img.resize(redimensionar, Image.LANCZOS)
    kwargs = {}
    if ext_saida in {".jpg", ".jpeg", ".webp"}:
        kwargs["quality"] = qualidade
        kwargs["optimize"] = True
    elif ext_saida == ".png":
        kwargs["optimize"] = True
    img.save(saida, **kwargs)


def converter_imagem_para_ico(entrada, saida):
    img = Image.open(entrada)
    tamanhos = [(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
    img.save(saida, format="ICO", sizes=tamanhos)


def converter_imagens_para_pdf(entradas, saida):
    imagens = []
    for caminho in entradas:
        img = Image.open(caminho)
        if img.mode == "RGBA":
            img = img.convert("RGB")
        imagens.append(img)
    primeira = imagens[0]
    if len(imagens) > 1:
        primeira.save(saida, format="PDF", save_all=True,
                      append_images=imagens[1:], resolution=150)
    else:
        primeira.save(saida, format="PDF", resolution=150)


def converter_pdf_para_imagens(entrada, saida, formato="png", dpi=200):
    doc = fitz.open(entrada)
    pasta = Path(saida).parent
    nome_base = Path(entrada).stem
    zoom = dpi / 72
    mat = fitz.Matrix(zoom, zoom)
    arquivos_criados = []
    for i, pagina in enumerate(doc, 1):
        pix = pagina.get_pixmap(matrix=mat)
        if len(doc) == 1:
            caminho = str(pasta / f"{Path(saida).stem}.{formato}")
        else:
            caminho = str(pasta / f"{nome_base}_pagina_{i}.{formato}")
        pix.save(caminho)
        arquivos_criados.append(caminho)
    doc.close()
    return arquivos_criados


def converter_pdf_para_texto(entrada, saida):
    doc = fitz.open(entrada)
    partes = []
    for i, pagina in enumerate(doc, 1):
        partes.append(f"--- Página {i} ---\n{pagina.get_text()}\n")
    doc.close()
    with open(saida, "w", encoding="utf-8") as f:
        f.write("\n".join(partes))


def converter_pdf_para_docx(entrada, saida):
    doc_pdf = fitz.open(entrada)
    doc_word = DocxDocument()
    doc_word.add_heading(Path(entrada).stem, level=0)
    for i, pagina in enumerate(doc_pdf, 1):
        doc_word.add_heading(f"Página {i}", level=1)
        for p in pagina.get_text().split("\n"):
            if p.strip():
                doc_word.add_paragraph(p.strip())
    doc_pdf.close()
    doc_word.save(saida)


def converter_pdf_para_html(entrada, saida):
    doc = fitz.open(entrada)
    html = [
        "<!DOCTYPE html><html lang='pt-BR'><head><meta charset='utf-8'>",
        f"<title>{Path(entrada).stem}</title>",
        "<style>body{font-family:Arial,sans-serif;max-width:800px;margin:0 auto;padding:20px}",
        ".pagina{border-bottom:2px solid #ccc;padding:20px 0;margin-bottom:20px}</style>",
        f"</head><body><h1>{Path(entrada).stem}</h1>",
    ]
    for i, pagina in enumerate(doc, 1):
        html.append(f'<div class="pagina"><h2>Página {i}</h2>')
        for linha in pagina.get_text().split("\n"):
            if linha.strip():
                html.append(f"<p>{linha.strip()}</p>")
        html.append("</div>")
    html.append("</body></html>")
    doc.close()
    with open(saida, "w", encoding="utf-8") as f:
        f.write("\n".join(html))


def converter_docx_para_txt(entrada, saida):
    doc = DocxDocument(entrada)
    with open(saida, "w", encoding="utf-8") as f:
        f.write("\n".join(p.text for p in doc.paragraphs))


def converter_docx_para_html(entrada, saida):
    doc = DocxDocument(entrada)
    html = [
        "<!DOCTYPE html><html lang='pt-BR'><head><meta charset='utf-8'>",
        f"<title>{Path(entrada).stem}</title>",
        "<style>body{font-family:Arial,sans-serif;max-width:800px;margin:0 auto;padding:20px}",
        "h1,h2,h3{color:#2c3e50}p{line-height:1.6;margin:8px 0}</style></head><body>",
    ]
    for para in doc.paragraphs:
        estilo = para.style.name.lower() if para.style else ""
        texto = para.text.strip()
        if not texto:
            continue
        if "heading 1" in estilo:
            html.append(f"<h1>{texto}</h1>")
        elif "heading 2" in estilo:
            html.append(f"<h2>{texto}</h2>")
        elif "heading 3" in estilo:
            html.append(f"<h3>{texto}</h3>")
        else:
            spans = []
            for run in para.runs:
                t = run.text
                if run.bold: t = f"<strong>{t}</strong>"
                if run.italic: t = f"<em>{t}</em>"
                if run.underline: t = f"<u>{t}</u>"
                spans.append(t)
            html.append(f"<p>{''.join(spans)}</p>")
    html.append("</body></html>")
    with open(saida, "w", encoding="utf-8") as f:
        f.write("\n".join(html))


def converter_docx_para_pdf(entrada, saida):
    doc = DocxDocument(entrada)
    c = rl_canvas.Canvas(saida, pagesize=A4)
    largura, altura = A4
    margem = 2 * cm
    y = altura - margem
    tam = 11
    esp = tam + 5
    c.setFont("Helvetica", tam)
    max_larg = largura - 2 * margem

    for para in doc.paragraphs:
        texto = para.text.strip()
        if not texto:
            y -= esp / 2
            continue
        estilo = para.style.name.lower() if para.style else ""
        if "heading 1" in estilo:
            c.setFont("Helvetica-Bold", 18); esp_atual = 28
        elif "heading 2" in estilo:
            c.setFont("Helvetica-Bold", 14); esp_atual = 22
        elif "heading 3" in estilo:
            c.setFont("Helvetica-Bold", 12); esp_atual = 18
        else:
            bold = any(r.bold for r in para.runs) if para.runs else False
            c.setFont("Helvetica-Bold" if bold else "Helvetica", tam)
            esp_atual = esp
        palavras = texto.split()
        linha_atual = ""
        for palavra in palavras:
            teste = f"{linha_atual} {palavra}".strip()
            if c.stringWidth(teste) < max_larg:
                linha_atual = teste
            else:
                if y < margem:
                    c.showPage(); c.setFont("Helvetica", tam); y = altura - margem
                c.drawString(margem, y, linha_atual); y -= esp_atual; linha_atual = palavra
        if linha_atual:
            if y < margem:
                c.showPage(); c.setFont("Helvetica", tam); y = altura - margem
            c.drawString(margem, y, linha_atual); y -= esp_atual
    c.save()


def _texto_para_pdf(texto, saida):
    c = rl_canvas.Canvas(saida, pagesize=A4)
    largura, altura = A4
    margem = 2 * cm
    y = altura - margem
    tam = 11; esp = tam + 5
    c.setFont("Helvetica", tam)
    max_larg = largura - 2 * margem
    for linha in texto.split("\n"):
        if not linha.strip():
            y -= esp / 2
            if y < margem:
                c.showPage(); c.setFont("Helvetica", tam); y = altura - margem
            continue
        palavras = linha.split()
        linha_atual = ""
        for palavra in palavras:
            teste = f"{linha_atual} {palavra}".strip()
            if c.stringWidth(teste) < max_larg:
                linha_atual = teste
            else:
                if y < margem:
                    c.showPage(); c.setFont("Helvetica", tam); y = altura - margem
                c.drawString(margem, y, linha_atual); y -= esp; linha_atual = palavra
        if linha_atual:
            if y < margem:
                c.showPage(); c.setFont("Helvetica", tam); y = altura - margem
            c.drawString(margem, y, linha_atual); y -= esp
    c.save()


def converter_txt_para_pdf(entrada, saida):
    with open(entrada, "r", encoding="utf-8") as f:
        _texto_para_pdf(f.read(), saida)


def converter_txt_para_docx(entrada, saida):
    with open(entrada, "r", encoding="utf-8") as f:
        texto = f.read()
    doc = DocxDocument()
    doc.add_heading(Path(entrada).stem, level=0)
    for linha in texto.split("\n"):
        doc.add_paragraph(linha)
    doc.save(saida)


def converter_txt_para_html(entrada, saida):
    with open(entrada, "r", encoding="utf-8") as f:
        texto = f.read()
    html = [
        "<!DOCTYPE html><html lang='pt-BR'><head><meta charset='utf-8'>",
        f"<title>{Path(entrada).stem}</title>",
        "<style>body{font-family:'Courier New',monospace;max-width:800px;margin:0 auto;padding:20px;",
        "background:#f5f5f5}pre{background:#fff;padding:20px;border-radius:8px;line-height:1.5}</style>",
        f"</head><body><h1>{Path(entrada).stem}</h1><pre>{texto}</pre></body></html>",
    ]
    with open(saida, "w", encoding="utf-8") as f:
        f.write("\n".join(html))


def _limpar_html(html_str):
    texto = re.sub(r"<script[^>]*>.*?</script>", "", html_str, flags=re.DOTALL)
    texto = re.sub(r"<style[^>]*>.*?</style>", "", texto, flags=re.DOTALL)
    texto = re.sub(r"<br\s*/?>", "\n", texto)
    texto = re.sub(r"</p>|</div>|</h[1-6]>|</li>|</tr>", "\n", texto)
    texto = re.sub(r"<[^>]+>", "", texto)
    texto = re.sub(r"&nbsp;", " ", texto)
    texto = re.sub(r"&amp;", "&", texto)
    texto = re.sub(r"&lt;", "<", texto)
    texto = re.sub(r"&gt;", ">", texto)
    return re.sub(r"\n{3,}", "\n\n", texto).strip()


def converter_html_para_txt(entrada, saida):
    with open(entrada, "r", encoding="utf-8") as f:
        html_str = f.read()
    with open(saida, "w", encoding="utf-8") as f:
        f.write(_limpar_html(html_str))


def converter_html_para_pdf(entrada, saida):
    with open(entrada, "r", encoding="utf-8") as f:
        html_str = f.read()
    _texto_para_pdf(_limpar_html(html_str), saida)


def converter_html_para_docx(entrada, saida):
    with open(entrada, "r", encoding="utf-8") as f:
        html_str = f.read()
    doc = DocxDocument()
    doc.add_heading(Path(entrada).stem, level=0)
    for linha in _limpar_html(html_str).split("\n"):
        if linha.strip():
            doc.add_paragraph(linha.strip())
    doc.save(saida)


def converter_md_para_html(entrada, saida):
    with open(entrada, "r", encoding="utf-8") as f:
        texto_md = f.read()
    html_body = md_lib.markdown(texto_md, extensions=["tables", "fenced_code"])
    html = [
        "<!DOCTYPE html><html lang='pt-BR'><head><meta charset='utf-8'>",
        f"<title>{Path(entrada).stem}</title>",
        "<style>body{font-family:-apple-system,sans-serif;max-width:800px;margin:0 auto;padding:20px}",
        "code{background:#f6f8fa;padding:2px 6px;border-radius:4px}",
        "pre{background:#f6f8fa;padding:16px;border-radius:8px;overflow-x:auto}",
        "pre code{background:none;padding:0}table{border-collapse:collapse;width:100%}",
        "th,td{border:1px solid #d0d7de;padding:8px 12px}th{background:#f6f8fa}</style></head><body>",
        html_body, "</body></html>",
    ]
    with open(saida, "w", encoding="utf-8") as f:
        f.write("\n".join(html))


def converter_md_para_pdf(entrada, saida):
    with open(entrada, "r", encoding="utf-8") as f:
        texto_md = f.read()
    html_body = md_lib.markdown(texto_md, extensions=["tables", "fenced_code"])
    _texto_para_pdf(_limpar_html(html_body), saida)


def converter_md_para_txt(entrada, saida):
    with open(entrada, "r", encoding="utf-8") as f:
        texto = f.read()
    texto = re.sub(r"#{1,6}\s+", "", texto)
    texto = re.sub(r"\*\*(.+?)\*\*", r"\1", texto)
    texto = re.sub(r"\*(.+?)\*", r"\1", texto)
    texto = re.sub(r"`(.+?)`", r"\1", texto)
    texto = re.sub(r"```[\s\S]*?```", "", texto)
    texto = re.sub(r"\[(.+?)\]\(.+?\)", r"\1", texto)
    texto = re.sub(r"!\[.*?\]\(.+?\)", "", texto)
    texto = re.sub(r"^[-*+]\s+", "• ", texto, flags=re.MULTILINE)
    with open(saida, "w", encoding="utf-8") as f:
        f.write(texto.strip())


# ──────────────────────────────────────────────────────────────
# Motor de Conversão
# ──────────────────────────────────────────────────────────────

CONVERSION_FUNCS = {
    (".pdf", ".txt"): converter_pdf_para_texto,
    (".pdf", ".docx"): converter_pdf_para_docx,
    (".pdf", ".html"): converter_pdf_para_html,
    (".docx", ".pdf"): converter_docx_para_pdf,
    (".docx", ".txt"): converter_docx_para_txt,
    (".docx", ".html"): converter_docx_para_html,
    (".txt", ".pdf"): converter_txt_para_pdf,
    (".txt", ".docx"): converter_txt_para_docx,
    (".txt", ".html"): converter_txt_para_html,
    (".html", ".txt"): converter_html_para_txt,
    (".html", ".pdf"): converter_html_para_pdf,
    (".html", ".docx"): converter_html_para_docx,
    (".htm", ".txt"): converter_html_para_txt,
    (".htm", ".pdf"): converter_html_para_pdf,
    (".htm", ".docx"): converter_html_para_docx,
    (".md", ".html"): converter_md_para_html,
    (".md", ".pdf"): converter_md_para_pdf,
    (".md", ".txt"): converter_md_para_txt,
}


def executar_conversao(entrada, saida):
    """Retorna mensagem de sucesso ou levanta exceção."""
    ext_in = Path(entrada).suffix.lower()
    ext_out = Path(saida).suffix.lower()

    # Imagem → Imagem
    if ext_in in IMAGE_EXTENSIONS and ext_out in IMAGE_EXTENSIONS:
        if ext_out == ".ico":
            converter_imagem_para_ico(entrada, saida)
        else:
            converter_imagem_para_imagem(entrada, saida)
        return saida

    # Imagem → PDF
    if ext_in in IMAGE_EXTENSIONS and ext_out == ".pdf":
        converter_imagens_para_pdf([entrada], saida)
        return saida

    # PDF → Imagem
    if ext_in == ".pdf" and ext_out in IMAGE_EXTENSIONS:
        arquivos = converter_pdf_para_imagens(entrada, saida, formato=ext_out.lstrip("."))
        return "\n".join(arquivos)

    # Documento → Documento
    func = CONVERSION_FUNCS.get((ext_in, ext_out))
    if func:
        func(entrada, saida)
        return saida

    raise ValueError(f"Conversão não suportada: {ext_in} → {ext_out}")


# ══════════════════════════════════════════════════════════════
#  INTERFACE GRÁFICA (tkinter)
# ══════════════════════════════════════════════════════════════

# ── Paleta de cores ──
COR_BG           = "#1e1e2e"
COR_BG_CARD      = "#2a2a3d"
COR_BG_INPUT     = "#363650"
COR_TEXTO        = "#cdd6f4"
COR_TEXTO_DIM    = "#6c7086"
COR_ACCENT       = "#89b4fa"
COR_ACCENT_HOVER = "#74c7ec"
COR_SUCCESS      = "#a6e3a1"
COR_ERROR        = "#f38ba8"
COR_WARNING      = "#f9e2af"
COR_BORDER       = "#45475a"


class ConversorApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("🔄 Conversor Universal de Arquivos")
        self.root.geometry("750x680")
        self.root.configure(bg=COR_BG)
        self.root.minsize(650, 600)

        # Variáveis
        self.arquivo_entrada = tk.StringVar()
        self.formato_saida = tk.StringVar()
        self.arquivo_saida = tk.StringVar()
        self.formatos_disponiveis = []

        self._criar_interface()

        # Checar dependências
        if MISSING_DEPS:
            self._log(f"⚠ Dependências faltando: pip install {' '.join(MISSING_DEPS)}", "warning")

    # ──────────────────────────────────────────────────────
    # Construção da Interface
    # ──────────────────────────────────────────────────────

    def _criar_interface(self):
        # ── Container principal com scroll ──
        container = tk.Frame(self.root, bg=COR_BG)
        container.pack(fill="both", expand=True, padx=20, pady=10)

        # ── Título ──
        frame_titulo = tk.Frame(container, bg=COR_BG)
        frame_titulo.pack(fill="x", pady=(10, 20))

        tk.Label(
            frame_titulo, text="🔄 Conversor Universal", font=("Segoe UI", 22, "bold"),
            fg=COR_ACCENT, bg=COR_BG,
        ).pack()
        tk.Label(
            frame_titulo, text="Imagens • PDFs • Word • Texto • HTML • Markdown • Ícones",
            font=("Segoe UI", 10), fg=COR_TEXTO_DIM, bg=COR_BG,
        ).pack()

        # ── Card: Arquivo de Entrada ──
        card1 = self._criar_card(container, "📁 ARQUIVO DE ENTRADA")

        frame_entrada = tk.Frame(card1, bg=COR_BG_CARD)
        frame_entrada.pack(fill="x", pady=(5, 0))

        self.entry_entrada = tk.Entry(
            frame_entrada, textvariable=self.arquivo_entrada, font=("Segoe UI", 10),
            bg=COR_BG_INPUT, fg=COR_TEXTO, insertbackground=COR_TEXTO,
            relief="flat", bd=0,
        )
        self.entry_entrada.pack(side="left", fill="x", expand=True, ipady=8, padx=(0, 8))

        btn_escolher = tk.Button(
            frame_entrada, text="📂 Escolher Arquivo", font=("Segoe UI", 9, "bold"),
            bg=COR_ACCENT, fg="#11111b", activebackground=COR_ACCENT_HOVER,
            relief="flat", cursor="hand2", padx=16, pady=6,
            command=self._escolher_arquivo,
        )
        btn_escolher.pack(side="right")

        self.lbl_info_entrada = tk.Label(
            card1, text="Nenhum arquivo selecionado", font=("Segoe UI", 9),
            fg=COR_TEXTO_DIM, bg=COR_BG_CARD, anchor="w",
        )
        self.lbl_info_entrada.pack(fill="x", pady=(5, 0))

        # ── Card: Formato de Saída ──
        card2 = self._criar_card(container, "🎯 FORMATO DE SAÍDA")

        self.frame_formatos = tk.Frame(card2, bg=COR_BG_CARD)
        self.frame_formatos.pack(fill="x", pady=(5, 0))

        self.lbl_sem_formato = tk.Label(
            self.frame_formatos,
            text="Selecione um arquivo de entrada primeiro",
            font=("Segoe UI", 9, "italic"), fg=COR_TEXTO_DIM, bg=COR_BG_CARD,
        )
        self.lbl_sem_formato.pack(anchor="w")

        # ── Card: Arquivo de Saída ──
        card3 = self._criar_card(container, "💾 ARQUIVO DE SAÍDA")

        frame_saida = tk.Frame(card3, bg=COR_BG_CARD)
        frame_saida.pack(fill="x", pady=(5, 0))

        self.entry_saida = tk.Entry(
            frame_saida, textvariable=self.arquivo_saida, font=("Segoe UI", 10),
            bg=COR_BG_INPUT, fg=COR_TEXTO, insertbackground=COR_TEXTO,
            relief="flat", bd=0,
        )
        self.entry_saida.pack(side="left", fill="x", expand=True, ipady=8, padx=(0, 8))

        btn_saida = tk.Button(
            frame_saida, text="📂 Escolher Local", font=("Segoe UI", 9, "bold"),
            bg=COR_BG_INPUT, fg=COR_TEXTO, activebackground=COR_BORDER,
            relief="flat", cursor="hand2", padx=16, pady=6,
            command=self._escolher_saida,
        )
        btn_saida.pack(side="right")

        # ── Botão Converter ──
        frame_botao = tk.Frame(container, bg=COR_BG)
        frame_botao.pack(fill="x", pady=(20, 10))

        self.btn_converter = tk.Button(
            frame_botao, text="⚡  CONVERTER", font=("Segoe UI", 13, "bold"),
            bg=COR_ACCENT, fg="#11111b", activebackground=COR_ACCENT_HOVER,
            relief="flat", cursor="hand2", pady=12,
            command=self._iniciar_conversao,
        )
        self.btn_converter.pack(fill="x")

        # ── Barra de progresso ──
        self.style = ttk.Style()
        self.style.theme_use("default")
        self.style.configure(
            "Custom.Horizontal.TProgressbar",
            troughcolor=COR_BG_INPUT, background=COR_ACCENT,
            darkcolor=COR_ACCENT, lightcolor=COR_ACCENT, bordercolor=COR_BG,
        )
        self.progress = ttk.Progressbar(
            container, style="Custom.Horizontal.TProgressbar",
            mode="indeterminate", length=300,
        )

        # ── Log ──
        card_log = self._criar_card(container, "📋 LOG")

        self.txt_log = tk.Text(
            card_log, height=6, font=("Consolas", 9),
            bg=COR_BG_INPUT, fg=COR_TEXTO, insertbackground=COR_TEXTO,
            relief="flat", bd=0, wrap="word", state="disabled",
        )
        self.txt_log.pack(fill="both", expand=True, pady=(5, 0))

        # Tags de cor para o log
        self.txt_log.tag_configure("success", foreground=COR_SUCCESS)
        self.txt_log.tag_configure("error", foreground=COR_ERROR)
        self.txt_log.tag_configure("warning", foreground=COR_WARNING)
        self.txt_log.tag_configure("info", foreground=COR_ACCENT)

    def _criar_card(self, parent, titulo_texto):
        """Cria um card estilizado."""
        card = tk.Frame(parent, bg=COR_BG_CARD, padx=16, pady=12,
                        highlightbackground=COR_BORDER, highlightthickness=1)
        card.pack(fill="x", pady=(0, 10))

        tk.Label(
            card, text=titulo_texto, font=("Segoe UI", 10, "bold"),
            fg=COR_ACCENT, bg=COR_BG_CARD, anchor="w",
        ).pack(fill="x")

        return card

    # ──────────────────────────────────────────────────────
    # Ações da Interface
    # ──────────────────────────────────────────────────────

    def _escolher_arquivo(self):
        tipos = [
            ("Todos suportados", " ".join(f"*{e}" for e in sorted(ALL_EXTENSIONS))),
            ("Imagens", " ".join(f"*{e}" for e in sorted(IMAGE_EXTENSIONS))),
            ("PDF", "*.pdf"),
            ("Word", "*.docx"),
            ("Texto", "*.txt"),
            ("HTML", "*.html *.htm"),
            ("Markdown", "*.md"),
            ("Todos os arquivos", "*.*"),
        ]
        caminho = filedialog.askopenfilename(
            title="Selecionar arquivo para converter",
            filetypes=tipos,
        )
        if caminho:
            self.arquivo_entrada.set(caminho)
            self._atualizar_info_entrada(caminho)
            self._atualizar_formatos(caminho)

    def _atualizar_info_entrada(self, caminho):
        nome = Path(caminho).name
        tamanho = os.path.getsize(caminho)
        ext = Path(caminho).suffix.lower()
        label = FORMAT_LABELS.get(ext, ext.upper())
        tam_str = self._formatar_tamanho(tamanho)
        self.lbl_info_entrada.config(
            text=f"📄 {nome}  •  {label}  •  {tam_str}",
            fg=COR_TEXTO,
        )

    def _atualizar_formatos(self, caminho):
        """Atualiza os botões de formato de saída."""
        # Limpar
        for widget in self.frame_formatos.winfo_children():
            widget.destroy()

        ext = Path(caminho).suffix.lower()
        formatos = CONVERSION_MAP.get(ext, [])

        if not formatos:
            tk.Label(
                self.frame_formatos,
                text=f"Nenhuma conversão disponível para {ext}",
                font=("Segoe UI", 9, "italic"), fg=COR_ERROR, bg=COR_BG_CARD,
            ).pack(anchor="w")
            return

        self.formatos_disponiveis = formatos
        self.formato_saida.set(formatos[0])

        # Criar grid de botões
        frame_grid = tk.Frame(self.frame_formatos, bg=COR_BG_CARD)
        frame_grid.pack(fill="x")

        self.botoes_formato = []
        cols = 4
        for i, fmt in enumerate(formatos):
            row = i // cols
            col = i % cols
            label = FORMAT_LABELS.get(fmt, fmt.upper())
            btn = tk.Button(
                frame_grid, text=label, font=("Segoe UI", 8, "bold"),
                bg=COR_BG_INPUT, fg=COR_TEXTO, activebackground=COR_BORDER,
                relief="flat", cursor="hand2", padx=10, pady=6,
                command=lambda f=fmt: self._selecionar_formato(f),
            )
            btn.grid(row=row, column=col, padx=3, pady=3, sticky="ew")
            self.botoes_formato.append((btn, fmt))
            frame_grid.columnconfigure(col, weight=1)

        # Selecionar o primeiro por padrão
        self._selecionar_formato(formatos[0])

        # Auto-preencher caminho de saída
        self._auto_preencher_saida()

    def _selecionar_formato(self, formato):
        self.formato_saida.set(formato)
        for btn, fmt in self.botoes_formato:
            if fmt == formato:
                btn.config(bg=COR_ACCENT, fg="#11111b")
            else:
                btn.config(bg=COR_BG_INPUT, fg=COR_TEXTO)
        self._auto_preencher_saida()

    def _auto_preencher_saida(self):
        entrada = self.arquivo_entrada.get()
        fmt = self.formato_saida.get()
        if entrada and fmt:
            p = Path(entrada)
            saida = str(p.parent / f"{p.stem}_convertido{fmt}")
            self.arquivo_saida.set(saida)

    def _escolher_saida(self):
        fmt = self.formato_saida.get()
        if not fmt:
            messagebox.showwarning("Aviso", "Selecione o formato de saída primeiro.")
            return
        ext_limpa = fmt.lstrip(".")
        caminho = filedialog.asksaveasfilename(
            title="Salvar arquivo convertido como",
            defaultextension=fmt,
            filetypes=[(f"Arquivo {ext_limpa.upper()}", f"*{fmt}"), ("Todos", "*.*")],
        )
        if caminho:
            self.arquivo_saida.set(caminho)

    def _iniciar_conversao(self):
        entrada = self.arquivo_entrada.get().strip()
        saida = self.arquivo_saida.get().strip()
        fmt = self.formato_saida.get()

        # Validações
        if not entrada:
            messagebox.showwarning("Aviso", "Selecione um arquivo de entrada.")
            return
        if not os.path.isfile(entrada):
            messagebox.showerror("Erro", f"Arquivo não encontrado:\n{entrada}")
            return
        if not saida:
            messagebox.showwarning("Aviso", "Defina o arquivo de saída.")
            return
        if not fmt:
            messagebox.showwarning("Aviso", "Selecione um formato de saída.")
            return

        # Confirmar sobrescrita
        if os.path.isfile(saida):
            resp = messagebox.askyesno("Confirmar", f"O arquivo já existe:\n{saida}\n\nDeseja sobrescrever?")
            if not resp:
                return

        # Desabilitar botão e iniciar progresso
        self.btn_converter.config(state="disabled", text="⏳ Convertendo...", bg=COR_BORDER)
        self.progress.pack(fill="x", pady=(0, 10), before=self.txt_log.master)
        self.progress.start(15)

        self._log(f"Convertendo: {Path(entrada).name} → {fmt}", "info")

        # Executar em thread separada para não travar a GUI
        thread = threading.Thread(target=self._converter_thread, args=(entrada, saida), daemon=True)
        thread.start()

    def _converter_thread(self, entrada, saida):
        try:
            resultado = executar_conversao(entrada, saida)

            # Chamar de volta na thread principal
            self.root.after(0, self._conversao_sucesso, resultado)
        except Exception as e:
            self.root.after(0, self._conversao_erro, str(e))

    def _conversao_sucesso(self, resultado):
        self.progress.stop()
        self.progress.pack_forget()
        self.btn_converter.config(state="normal", text="⚡  CONVERTER", bg=COR_ACCENT)

        # Mostrar tamanho do resultado
        linhas = resultado.strip().split("\n")
        for arq in linhas:
            if os.path.isfile(arq):
                tam = self._formatar_tamanho(os.path.getsize(arq))
                self._log(f"✅ Salvo: {Path(arq).name} ({tam})", "success")
            else:
                self._log(f"✅ {arq}", "success")

        messagebox.showinfo(
            "Sucesso! ✅",
            f"Arquivo convertido com sucesso!\n\n{resultado}",
        )

    def _conversao_erro(self, mensagem):
        self.progress.stop()
        self.progress.pack_forget()
        self.btn_converter.config(state="normal", text="⚡  CONVERTER", bg=COR_ACCENT)
        self._log(f"❌ Erro: {mensagem}", "error")
        messagebox.showerror("Erro na Conversão", f"Ocorreu um erro:\n\n{mensagem}")

    # ──────────────────────────────────────────────────────
    # Utilidades
    # ──────────────────────────────────────────────────────

    def _log(self, texto, tag=None):
        self.txt_log.config(state="normal")
        if tag:
            self.txt_log.insert("end", f"{texto}\n", tag)
        else:
            self.txt_log.insert("end", f"{texto}\n")
        self.txt_log.see("end")
        self.txt_log.config(state="disabled")

    @staticmethod
    def _formatar_tamanho(b):
        for u in ["B", "KB", "MB", "GB"]:
            if b < 1024:
                return f"{b:.1f} {u}"
            b /= 1024
        return f"{b:.1f} TB"


# ══════════════════════════════════════════════════════════════
#  PONTO DE ENTRADA
# ══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    root = tk.Tk()

    # Ícone (opcional, falha silenciosamente se não disponível)
    try:
        root.iconbitmap(default="")
    except Exception:
        pass

    # DPI awareness no Windows
    try:
        from ctypes import windll
        windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        pass

    app = ConversorApp(root)
    root.mainloop()

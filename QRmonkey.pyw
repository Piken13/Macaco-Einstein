import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk
import qrcode

# --- CONFIGURAÇÃO DA JANELA ---
janela = tk.Tk()
janela.title("🐒 Macaco Einstein: Gerador de QR Code 🍌")
janela.geometry("450x640")
janela.configure(bg="#22272e")
janela.resizable(False, False)

# Variáveis globais para guardar a imagem gerada
imagem_pil_atual = None
imagem_tk_global = None


def gerar_qrcode():
    global imagem_pil_atual, imagem_tk_global
    link = entrada_link.get().strip()

    if not link:
        messagebox.showwarning("Aviso!", "Cole um link primeiro, macaco!")
        return

    # Cria o QR Code
    qr = qrcode.QRCode(box_size=8, border=2)
    qr.add_data(link)
    qr.make(fit=True)

    # Guarda a imagem original na memória
    imagem_pil_atual = qr.make_image(fill_color="black", back_color="white")

    # Mostra a prévia na janela
    preview = imagem_pil_atual.resize((220, 220))
    imagem_tk_global = ImageTk.PhotoImage(preview)
    label_imagem.configure(image=imagem_tk_global, text="")

    # Habilita o botão de salvar e avisa o usuário
    botao_salvar.configure(state="normal", bg="#388bfd", fg="white")
    label_status.configure(
        text="QR Code pronto! Agora clique em 'Salvar Imagem'.", fg="#57ab5a"
    )


def salvar_como():
    global imagem_pil_atual

    if imagem_pil_atual is None:
        messagebox.showwarning("Aviso", "Gere um QR Code antes de salvar!")
        return

    # Abre a janela oficial do Windows pra escolher a pasta e o nome
    caminho = filedialog.asksaveasfilename(
        defaultextension=".png",
        filetypes=[("Imagem PNG", "*.png"), ("Todos os Arquivos", "*.*")],
        initialfile="meu_qrcode.png",
        title="Onde o macaco quer guardar o QR Code?",
    )

    # Se o usuário escolheu um lugar e não cancelou:
    if caminho:
        imagem_pil_atual.save(caminho)
        messagebox.showinfo(
            "Sucesso! 🍌", f"Arquivo salvo com sucesso em:\n{caminho}"
        )
        label_status.configure(text="Arquivo salvo com sucesso! 🎉", fg="#57ab5a")


# --- DESIGN / BOTÕES ---
titulo = tk.Label(
    janela,
    text="Gerador de QR Code",
    font=("Arial", 18, "bold"),
    fg="#adbac7",
    bg="#22272e",
)
titulo.pack(pady=12)

subtitulo = tk.Label(
    janela,
    text="Cole o link ou texto abaixo:",
    font=("Arial", 11),
    fg="#768390",
    bg="#22272e",
)
subtitulo.pack()

entrada_link = tk.Entry(
    janela,
    font=("Arial", 13),
    width=35,
    bg="#2d333b",
    fg="#cdd9e5",
    insertbackground="white",
    relief="flat",
)
entrada_link.pack(pady=10, ipady=6)

# Botão 1: Gerar
botao_gerar = tk.Button(
    janela,
    text="1. Gerar QR Code ⚡",
    font=("Arial", 11, "bold"),
    bg="#f2cc60",
    fg="#1c2128",
    activebackground="#e3b341",
    relief="flat",
    cursor="hand2",
    command=gerar_qrcode,
)
botao_gerar.pack(pady=6, ipadx=10, ipady=3)

# Caixa de Prévia da Imagem
label_imagem = tk.Label(
    janela,
    text="[ Prévia do QR Code ]",
    font=("Arial", 10),
    fg="#545d68",
    bg="#1c2128",
    width=28,
    height=11,
)
label_imagem.pack(pady=10)

# Botão 2: Escolher Onde Salvar
botao_salvar = tk.Button(
    janela,
    text="2. Escolher Pasta e Salvar 📁💾",
    font=("Arial", 11, "bold"),
    bg="#343941",
    fg="#768390",
    relief="flat",
    cursor="hand2",
    state="disabled",  # Começa desativado até você gerar o primeiro
    command=salvar_como,
)
botao_salvar.pack(pady=8, ipadx=10, ipady=4)

label_status = tk.Label(
    janela, text="", font=("Arial", 9, "italic"), bg="#22272e"
)
label_status.pack()

janela.mainloop()
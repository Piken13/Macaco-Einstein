from PIL import Image

# Abre a sua imagem da Área de Trabalho
foto = Image.open(r"C:\Users\yanca\Pictures\Imagem.png")

# Salva como um ICO legítimo que o Windows aceita
foto.save(r"C:\Users\yanca\Pictures\Imagem.ico", format="ICO")

print("Feitiço concluído! Criado o arquivo ícone.ico na sua Área de Trabalho!")
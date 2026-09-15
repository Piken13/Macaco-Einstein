import pygame
import random
import sys

# Inicia o motor do jogo
pygame.init()

# Tamanho da tela da floresta
LARGURA = 600
ALTURA = 400
tela = pygame.display.set_mode((LARGURA, ALTURA))
pygame.display.set_caption("🐒 Macaco Einstein: Cata-Banana! 🍌")

# Cores da selva (Vermelho, Verde, Azul)
VERDE_SELVA = (34, 139, 34)
AMARELO_BANANA = (255, 225, 53)
MARROM_MACACO = (139, 69, 19)
BRANCO = (255, 255, 255)

# Posição do Macaco (Jogador)
macaco_largura = 70
macaco_altura = 25
macaco_x = LARGURA // 2
macaco_y = ALTURA - 40
velocidade_macaco = 8

# Posição da Banana que cai do céu
banana_raio = 15
banana_x = random.randint(20, LARGURA - 20)
banana_y = 0
velocidade_banana = 5

# Placar do macaco
pontos = 0
fonte = pygame.font.SysFont("Arial", 28, bold=True)
relogio = pygame.time.Clock()

# --- LOOP PRINCIPAL DO JOGO ---
rodando = True
while rodando:
    relogio.tick(60)  # 60 frames por segundo

    # 1. Verifica se clicou no X pra fechar a janela
    for evento in pygame.event.get():
        if evento.type == pygame.QUIT:
            rodando = False

    # 2. Controles do Macaco (Setinhas Esquerda / Direita ou A / D)
    teclas = pygame.key.get_pressed()
    if (teclas[pygame.K_LEFT] or teclas[pygame.K_a]) and macaco_x > 0:
        macaco_x -= velocidade_macaco
    if (teclas[pygame.K_RIGHT] or teclas[pygame.K_d]) and macaco_x < LARGURA - macaco_largura:
        macaco_x += velocidade_macaco

    # 3. Faz a banana cair
    banana_y += velocidade_banana

    # 4. Verifica se o macaco pegou a banana!
    if (macaco_y < banana_y + banana_raio < macaco_y + macaco_altura) and \
       (macaco_x < banana_x < macaco_x + macaco_largura):
        pontos += 1
        # Cria uma banana nova lá no topo
        banana_y = 0
        banana_x = random.randint(20, LARGURA - 20)
        # O jogo vai ficando mais rápido a cada banana!
        velocidade_banana += 0.3

    # Se a banana cair no chão sem pegar
    if banana_y > ALTURA:
        banana_y = 0
        banana_x = random.randint(20, LARGURA - 20)

    # 5. Desenha as coisas na tela
    tela.fill(VERDE_SELVA)  # Fundo verde floresta

    # Desenha o macaco (retângulo marrom)
    pygame.draw.rect(tela, MARROM_MACACO, (macaco_x, macaco_y, macaco_largura, macaco_altura), border_radius=6)

    # Desenha a banana (círculo amarelo)
    pygame.draw.circle(tela, AMARELO_BANANA, (banana_x, banana_y), banana_raio)

    # Desenha o placar
    texto_pontos = fonte.render(f"Bananas: {pontos} 🍌", True, BRANCO)
    tela.blit(texto_pontos, (15, 15))

    # Atualiza a tela
    pygame.display.flip()

pygame.quit()
sys.exit()
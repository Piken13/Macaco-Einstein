import pygame
import random
import sys

# Inicia o motor do jogo
pygame.init()

# Tamanho da tela e da grade
LARGURA = 600
ALTURA = 400
TAMANHO_BLOCO = 20  # Tamanho de cada pedacinho da cobra e da fruta

tela = pygame.display.set_mode((LARGURA, ALTURA))
pygame.display.set_caption("🐍 Cobrinha Comilona de Bananas 🍌")

# Cores
PRETO = (20, 20, 20)
VERDE_CLARO = (50, 205, 50)
VERDE_ESCURO = (34, 139, 34)
AMARELO_BANANA = (255, 215, 0)
VERMELHO = (220, 20, 60)
BRANCO = (255, 255, 255)

fonte = pygame.font.SysFont("Arial", 25, bold=True)
fonte_game_over = pygame.font.SysFont("Arial", 40, bold=True)
relogio = pygame.time.Clock()

def sortear_banana():
    """Gera uma banana em uma posição alinhada com a grade"""
    x = random.randint(0, (LARGURA - TAMANHO_BLOCO) // TAMANHO_BLOCO) * TAMANHO_BLOCO
    y = random.randint(0, (ALTURA - TAMANHO_BLOCO) // TAMANHO_BLOCO) * TAMANHO_BLOCO
    return x, y

def jogar():
    # Posição inicial da cobra (no meio da tela)
    cobra_x = LARGURA // 2
    cobra_y = ALTURA // 2
    
    # Movimento inicial (começa parada)
    vel_x = 0
    vel_y = 0
    
    # Corpo da cobra (lista de pedacinhos)
    corpo = [[cobra_x, cobra_y]]
    tamanho_cobra = 1
    
    banana_x, banana_y = sortear_banana()
    pontos = 0
    
    game_over = False
    rodando = True

    while rodando:
        relogio.tick(12)  # Velocidade do jogo (12 passos por segundo)

        # 1. Trata os cliques e teclas
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            
            if evento.type == pygame.KEYDOWN:
                # Controles de direção (não pode voltar pra trás direto!)
                if (evento.key == pygame.K_LEFT or evento.key == pygame.K_a) and vel_x == 0:
                    vel_x = -TAMANHO_BLOCO
                    vel_y = 0
                elif (evento.key == pygame.K_RIGHT or evento.key == pygame.K_d) and vel_x == 0:
                    vel_x = TAMANHO_BLOCO
                    vel_y = 0
                elif (evento.key == pygame.K_UP or evento.key == pygame.K_w) and vel_y == 0:
                    vel_x = 0
                    vel_y = -TAMANHO_BLOCO
                elif (evento.key == pygame.K_DOWN or evento.key == pygame.K_s) and vel_y == 0:
                    vel_x = 0
                    vel_y = TAMANHO_BLOCO
                
                # Se perdeu e apertar R, reinicia!
                if game_over and evento.key == pygame.K_r:
                    return jogar()

        if not game_over:
            # 2. Move a cabeça da cobra
            cobra_x += vel_x
            cobra_y += vel_y

            # Só mexe o resto do corpo se a cobra já começou a andar
            if vel_x != 0 or vel_y != 0:
                cabeca = [cobra_x, cobra_y]
                corpo.append(cabeca)

                # Mantém o tamanho certo do corpo
                if len(corpo) > tamanho_cobra:
                    del corpo[0]

                # 3. Bateu na parede?
                if cobra_x < 0 or cobra_x >= LARGURA or cobra_y < 0 or cobra_y >= ALTURA:
                    game_over = True

                # 4. Mordeu o próprio rabo?
                for pedaco in corpo[:-1]:
                    if pedaco == cabeca:
                        game_over = True

                # 5. Comeu a banana?
                if cobra_x == banana_x and cobra_y == banana_y:
                    pontos += 1
                    tamanho_cobra += 1
                    banana_x, banana_y = sortear_banana()

        # 6. Desenha na tela
        tela.fill(PRETO)

        # Desenha a banana
        pygame.draw.rect(tela, AMARELO_BANANA, (banana_x, banana_y, TAMANHO_BLOCO, TAMANHO_BLOCO), border_radius=5)

        # Desenha a cobra pedaço por pedaço
        for i, pedaco in enumerate(corpo):
            # Cabeça mais clara, corpo mais escuro
            cor = VERDE_CLARO if i == len(corpo) - 1 else VERDE_ESCURO
            pygame.draw.rect(tela, cor, (pedaco[0], pedaco[1], TAMANHO_BLOCO, TAMANHO_BLOCO), border_radius=4)

        # Placar
        texto_placar = fonte.render(f"Bananas: {pontos}", True, BRANCO)
        tela.blit(texto_placar, (15, 10))

        # Tela de Game Over
        if game_over:
            texto_fim = fonte_game_over.render("MORREU! 💥", True, VERMELHO)
            texto_restart = fonte.render("Aperte [R] para jogar de novo", True, BRANCO)
            tela.blit(texto_fim, (LARGURA // 2 - 100, ALTURA // 2 - 40))
            tela.blit(texto_restart, (LARGURA // 2 - 160, ALTURA // 2 + 15))

        pygame.display.flip()

# Roda o jogo
jogar()
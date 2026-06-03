# importar o módulo pgzrun para rodar o jogo
import pgzrun

# criar um "ator"
quad1 = Actor('145423.jpg')
quad2 = Actor('145423.jpg')
# definir posição do ator (x, y)
quad1.pos = 400, 10
quad2.pos = 700, 10

# criar uma "base"
base = Actor('image.png')
# definir a posição da base
base.pos = 580, 800

# definir largura e altura da janela
WIDTH = 1200
HEIGHT = 1000

# método que vai desenhar os atores na tela
def draw():
    # limpar a tela
    screen.clear()
    # desenhar os atores
    quad1.draw()
    quad2.draw()
    base.draw()

# método que vai atualizar a posição dos atores
def update():
    # se o ator NÃO colidiu com a base...
    if not quad1.colliderect(base):
        # o ator continua "caindo"
        quad1.top += 1.3 
        quad2.top += 2


# executar o jogo
pgzrun.go()

''' EXERCÍCIOS:

a) aumentar a velocidade de queda do quadrado
b) mudar a posição inicial do quadrado (colocar o quadrado mais alto)
c) mudar a posição da base (colocar a base mais para baixo)
d) mudar as figuras da base e do quadrado
e) colocar 2 quadrados caindo ao mesmo tempo

Para fazer as atividades a seguir, você deverá buscar na Internet/IA
como realizá-las no pygame zero:

f) alterar a cor de fundo da janela
===> "como alterar a cor de fundo da janela no pygame zero"
g) centralizar a janela na tela
===> "como centralizar a janela no pygame zero"
h) colocar um título na janela
===> "como colocar um título na janela no pygame zero"

'''
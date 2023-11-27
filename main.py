import pygame
import pygame_shaders
import math
import time

pygame.init()
screen = pygame.display.set_mode((1280, 720))
pygame.display.set_caption("HOI DAAN")
clock = pygame.time.Clock()

shader = pygame_shaders.Shader(size=(600, 600), display=(600, 600),
                               pos=(0, 0), vertex_path="shaders/main.frag",
                               fragment_path="shaders/main.vert")  # Load your shader!


def color(r=0, g=0, b=0):
    return (r * 255, g * 255, b * 255)


running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    screen.fill(color(math.cos(time.time()) * 0.5 + 0.5,
                math.sin(time.time()) * 0.5 + 0.5, 0.5))

    pygame.display.flip()

    clock.tick(60)  # limits FPS to 60

pygame.quit()

import pygame
import pygame_shaders
import math
import time
import classes
from pygame.locals import *

pygame.init()
screen = pygame.display.set_mode(
    (1280, 720), pygame.OPENGL | pygame.DOUBLEBUF | pygame.HWSURFACE)
pygame.display.set_caption("HOI DAAN")
clock = pygame.time.Clock()

shader = pygame_shaders.Shader(size=(1280, 720), display=(1280, 720),
                               pos=(0, 0), vertex_path="shaders/vertex.glsl",
                               fragment_path="shaders/fragment.glsl", target_texture=screen)  # Load your shader!
red = pygame.image.load('rode auto.png')
blue = pygame.image.load('blauwe auto.png')
yellow = pygame.image.load('gele auto.png')
green = pygame.image.load('groene auto.png')

pygame.init()

# pygame_shaders.Shader.send(variable_name: str, data: List[float])

dark_graaaaaaaaaaaaaaaaaaaaaaaaaaaay = (169, 169, 169)


def draw(screen):
    pygame.draw.circle(screen, color(1, 1, 1), [200, 200], 100, 20)


def color(r=0, g=0, b=0):
    return (r * 255, g * 255, b * 255)


def main():
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        draw(screen)

        # Render the display onto the OpenGL display with the shaders!
        shader.render(screen)
        pygame.display.flip()

        clock.tick(60)  # limits FPS to 60

    pygame.quit()


if __name__ == "__main__":
    main()

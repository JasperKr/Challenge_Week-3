import pygame
import pygame_shaders
import math
import time

pygame.init()
screen = pygame.display.set_mode(
    (1280, 720), pygame.OPENGL | pygame.DOUBLEBUF | pygame.HWSURFACE)
pygame.display.set_caption("HOI DAAN")
clock = pygame.time.Clock()

shader = pygame_shaders.Shader(size=(1280, 720), display=(1280, 720),
                               pos=(0, 0), vertex_path="shaders/vertex.glsl",
                               fragment_path="shaders/fragment.glsl", target_texture=screen)  # Load your shader!


pygame.init()

# Create a new surface, this will be where you do all your pygame rendering
display = pygame.Surface((1280, 720))
display.set_colorkey((0, 0, 0))  # Make all black on the display transparent

# pygame_shaders.Shader.send(variable_name: str, data: List[float])


def color(r=0, g=0, b=0):
    return (r * 255, g * 255, b * 255)


running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    screen.fill(color(math.cos(time.time()) * 0.5 + 0.5,
                math.sin(time.time()) * 0.5 + 0.5, 0.5))
    # Render the display onto the OpenGL display with the shaders!
    shader.render(display)
    pygame.display.flip()

    clock.tick(60)  # limits FPS to 60

pygame.quit()

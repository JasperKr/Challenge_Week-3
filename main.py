import pygame
import pygame_shaders
import math
import time
from pygame.locals import *

pygame.init()


def mix(v, w, i):
    return v * (1 - i) + w * i


class Obb():
    def __init__(self, position, size, rotation) -> None:
        self.position = position
        self.size = size
        self.rotation = rotation


def dot_product(a1, a2):
    return a1[0] * a2[0] + a1[1] * a2[1]


def length(a1):
    return math.sqrt(a1[0] * a1[0] + a1[1] * a1[1])


def normalize(a1):
    i = 1 / length(a1)
    return [a1[0] * i, a1[1] * i]


def is_obb_overlap(o1, o2):
    # axes vector
    a1 = [math.cos(o1.rotation), math.sin(o1.rotation)]
    a2 = [-math.sin(o1.rotation), math.cos(o1.rotation)]
    a3 = [math.cos(o2.rotation), math.sin(o2.rotation)]
    a4 = [-math.sin(o2.rotation), math.cos(o2.rotation)]

    # edge length
    l1 = [i * 0.5 for i in o1.size]
    l2 = [i * 0.5 for i in o2.size]

    # vector between pivots
    l = [o1_p - o2_p for o1_p, o2_p in zip(o1.pivot, o2.pivot)]

    min_overlap = float('inf')
    separating_axis = None

    for a in [a1, a2, a3, a4]:
        r1 = l1[0] * abs(dot_product(a1, a))
        r2 = l1[1] * abs(dot_product(a2, a))
        r3 = l2[0] * abs(dot_product(a3, a))
        r4 = l2[1] * abs(dot_product(a4, a))
        overlap = r1 + r2 + r3 + r4 - abs(dot_product(l, a))
        if overlap <= 0:
            return None, 0
        elif overlap < min_overlap:
            min_overlap = overlap
            separating_axis = a

    return separating_axis, min_overlap


class Level():
    def __init__(self, walls) -> None:
        self.walls = walls


def blitRotate(surf, image, pos, originPos, angle):

    # offset from pivot to center
    image_rect = image.get_rect(
        topleft=(pos[0] - originPos[0], pos[1] - originPos[1]))
    offset_center_to_pivot = pygame.math.Vector2(pos) - image_rect.center

    # roatated offset from pivot to center
    rotated_offset = offset_center_to_pivot.rotate(-angle)

    # roatetd image center
    rotated_image_center = (pos[0] - rotated_offset.x,
                            pos[1] - rotated_offset.y)

    # get a rotated image
    rotated_image = pygame.transform.rotate(image, angle)
    rotated_image_rect = rotated_image.get_rect(center=rotated_image_center)

    # rotate and blit the image
    surf.blit(rotated_image, rotated_image_rect)


class Player():
    def __init__(self, position=None, radius=1.0, drag=0.5, angular_drag=4, obb=None, angle=0, car_type=0) -> None:
        if obb is None:
            obb = Obb([0.0, 0.0], [140, 190], 0)
        if position is None:
            position = [0.0, 0.0]
        self.position = position
        self.radius = radius
        self.velocity = [0.0, 0.0]
        self.drag = drag
        self.angular_drag = angular_drag
        self.obb = obb
        self.angle = angle
        self.angular_velocity = 0
        self.car_type = car_type

    def apply_force(self, x, y):
        self.velocity[0] += x
        self.velocity[1] += y

    def handle_user_input(self, input: str):
        # input: up, down, left, right
        angle = math.radians(self.angle)
        acceleration = 15
        direction = [math.cos(angle), math.sin(angle)]
        if input == "up":
            self.apply_force(direction[0] * acceleration,
                             direction[1] * acceleration)
        if input == "down":
            self.apply_force(-direction[0] *
                             acceleration, -direction[1] * acceleration)
        if input == "left":
            self.angular_velocity -= 15
        if input == "right":
            self.angular_velocity += 15

    def update(self, dt, walls):
        self.position[0] += self.velocity[0] * dt
        self.position[1] += self.velocity[1] * dt

        self.velocity[0] = mix(self.velocity[0], 0, dt * self.drag)
        self.velocity[1] = mix(self.velocity[1], 0, dt * self.drag)

        self.angular_velocity = mix(
            self.angular_velocity, 0, dt * self.angular_drag)

        self.angle += self.angular_velocity * dt

        for object in walls:
            axis, overlap = is_obb_overlap(self.obb, object.obb)
            if axis is not None:
                self.position[0] += axis[0] * overlap
                self.position[1] += axis[1] * overlap

                normal = normalize(axis)

                force = [self.velocity[0] * normal[0],
                         self.velocity[1] * normal[1]]

                self.velocity[0] -= force[0]
                self.velocity[1] -= force[1]

    def draw(self, screen: pygame.Surface, car_images: list):
        # draw car
        blitRotate(screen, car_images[self.car_type],
                   self.position, [151 / 4, 303 / 4], -self.angle - 90)


# pygame_shaders.Shader.send(variable_name: str, data: List[float])
dark_gray = (169, 169, 169)


def player_movement(key_pressed, player_1, player_2):
    if key_pressed[pygame.K_w]:
        player_1.handle_user_input("up")
    if key_pressed[pygame.K_a]:
        player_1.handle_user_input("left")
    if key_pressed[pygame.K_d]:
        player_1.handle_user_input("right")
    if key_pressed[pygame.K_s]:
        player_1.handle_user_input("down")
    if key_pressed[pygame.K_UP]:
        player_2.handle_user_input("up")
    if key_pressed[pygame.K_LEFT]:
        player_2.handle_user_input("left")
    if key_pressed[pygame.K_RIGHT]:
        player_2.handle_user_input("right")
    if key_pressed[pygame.K_DOWN]:
        player_2.handle_user_input("down")


def draw(screen, player_1, player_2, car_images):
    pygame.draw.circle(screen, color(1, 1, 1), [0, 0], 100, 20)
    player_1.draw(screen, car_images)
    player_2.draw(screen, car_images)


def color(r=0, g=0, b=0):
    return (r * 255, g * 255, b * 255)


def interface():
    bauhaus_font = pygame.font.SysFont('bauhaus93', 20)
    name_player_one = input("What is the name of player 1? ")
    name_player_two = input("What is the name of player 2? ")
    color_player_one = input(
        f"What color does {name_player_one} want to be? [Blue, Red, Yellow, Green] ")
    color_player_two = input(
        f"What color does {name_player_two} want to be? [Blue, Red, Yellow, Green] ")


def main():

    screen = pygame.display.set_mode(
        (1280, 720), pygame.OPENGL | pygame.DOUBLEBUF | pygame.HWSURFACE)
    pygame.display.set_caption("Racegame")
    clock = pygame.time.Clock()

    shader = pygame_shaders.Shader(size=(1280, 720), display=(1280, 720),
                                   pos=(0, 0), vertex_path="shaders/vertex.glsl",
                                   fragment_path="shaders/fragment.glsl", target_texture=screen)  # Load your shader!

    player_1 = Player()
    player_2 = Player(car_type=2)

    car_images = [
        pygame.image.load("assets/car_1.png"),
        pygame.image.load("assets/car_2.png"),
        pygame.image.load("assets/car_3.png"),
        pygame.image.load("assets/car_4.png"),
    ]

    # scale car images
    for i in range(len(car_images)):
        car_images[i] = pygame.transform.scale(
            car_images[i], (151 / 2, 303 / 2))

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
        keys_pressed = pygame.key.get_pressed()
        if keys_pressed[pygame.K_ESCAPE]:
            running = False
        player_movement(keys_pressed, player_1, player_2)
        player_1.update(1 / 60, [])
        player_2.update(1 / 60, [])
        screen.fill(dark_gray)
        draw(screen, player_1, player_2, car_images)

        # Render the display onto the OpenGL display with the shaders!
        shader.render(screen)
        pygame.display.flip()

        clock.tick(60)  # limits FPS to 60

    pygame.quit()


if __name__ == "__main__":
    main()

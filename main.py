import pygame
import pygame_shaders
import math
import time
from pygame.locals import *

pygame.init()


def mix(v, w, i):
    return v * (1 - i) + w * i


def dot_product(a1, a2):
    return a1[0] * a2[0] + a1[1] * a2[1]


def length(a1):
    return math.sqrt(a1[0] * a1[0] + a1[1] * a1[1])


def normalize(a1):
    l = length(a1)
    if l == 0:
        return [0, 0]
    i = 1 / l
    return [a1[0] * i, a1[1] * i]


def point_aabb(px, py, x, y, w, h):
    return px > x and py and px < x + w and py > y and py < y + h


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


def blitRotate(surf, image, pos, originPos, angle):
    # offset from pivot to center
    image_rect = image.get_rect(
        topleft=(pos[0] - originPos[0], pos[1] - originPos[1]))
    offset_center_to_pivot = pygame.math.Vector2(pos) - image_rect.center

    # roatated offset from pivot to center
    rotated_offset = offset_center_to_pivot.rotate(-angle)

    # rotated image center
    rotated_image_center = (pos[0] - rotated_offset.x,
                            pos[1] - rotated_offset.y)

    # get a rotated image
    rotated_image = pygame.transform.rotate(image, angle)
    rotated_image_rect = rotated_image.get_rect(center=rotated_image_center)

    # rotate and blit the image
    surf.blit(rotated_image, rotated_image_rect)


def rotate_point(point, pivot, angle):
    angle = math.radians(angle)
    x = point[0] - pivot[0]
    y = point[1] - pivot[1]
    rotated_x = x * math.cos(angle) - y * math.sin(angle)
    rotated_y = x * math.sin(angle) + y * math.cos(angle)
    rotated_x += pivot[0]
    rotated_y += pivot[1]
    return [rotated_x, rotated_y]


class Obb():
    def __init__(self, position, size, rotation) -> None:
        self.position = position
        self.size = size
        self.rotation = rotation


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
        self.on_finishline = False
        self.score = -1

    def apply_force(self, x, y):
        self.velocity[0] += x
        self.velocity[1] += y

    def handle_user_input(self, input: str, dt):
        # input: up, down, left, right
        angle = math.radians(self.angle)
        acceleration = self.score * 2.5 + 10
        direction = [math.cos(angle), math.sin(angle)]
        if input == "up":
            self.apply_force(direction[0] * acceleration,
                             direction[1] * acceleration)
        if input == "down":
            self.apply_force(-direction[0] *
                             acceleration, -direction[1] * acceleration)
        if input == "left":
            self.angular_velocity -= 1200 * dt
        if input == "right":
            self.angular_velocity += 1200 * dt

    def update(self, dt, walls, finishline):
        self.position[0] += self.velocity[0] * dt
        self.position[1] += self.velocity[1] * dt

        self.velocity[0] = mix(self.velocity[0], 0, dt * self.drag)
        self.velocity[1] = mix(self.velocity[1], 0, dt * self.drag)

        car_right_vector = [-math.sin(math.radians(self.angle)),
                            math.cos(math.radians(self.angle))]
        side_velocity = dot_product(car_right_vector, normalize(self.velocity))
        self.apply_force(
            car_right_vector[0] * -side_velocity * 10, car_right_vector[1] * -side_velocity * 10)

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

        if point_aabb(self.position[0], self.position[1], finishline[0], finishline[1], finishline[2], finishline[3]):
            if not self.on_finishline:
                self.on_finishline = True
                self.score += 1
        else:
            self.on_finishline = False

    def draw(self, screen: pygame.Surface, car_images: list, camera_position):
        # draw car
        blitRotate(screen, car_images[self.car_type],
                   (self.position[0] + camera_position[0], self.position[1] + camera_position[1]), [151 / 4, 303 / 4], -self.angle - 90)

    def draw_tire_marks(self, screen: pygame.Surface):
        car_right_vector = [-math.sin(math.radians(self.angle)),
                            math.cos(math.radians(self.angle))]
        if abs(dot_product(car_right_vector, normalize(self.velocity))) > 0.4 and length(self.velocity) > 200:

            x, y = self.position
            tire_1 = rotate_point([x - 303 / 6, y - 151 / 6],
                                  self.position, self.angle)
            pygame.draw.circle(screen, color(0.2, 0.2, 0.2), tire_1, 10, 0)
            tire_2 = rotate_point([x + 303 / 6, y - 151 / 6],
                                  self.position, self.angle)
            pygame.draw.circle(screen, color(0.2, 0.2, 0.2), tire_2, 10, 0)
            tire_3 = rotate_point([x - 303 / 6, y + 151 / 6],
                                  self.position, self.angle)
            pygame.draw.circle(screen, color(0.2, 0.2, 0.2), tire_3, 10, 0)
            tire_4 = rotate_point([x + 303 / 6, y + 151 / 6],
                                  self.position, self.angle)
            pygame.draw.circle(screen, color(0.2, 0.2, 0.2), tire_4, 10, 0)


# pygame_shaders.Shader.send(variable_name: str, data: List[float])
dark_gray = (169, 169, 169)


def player_movement(key_pressed, player_1, player_2, dt):
    if key_pressed[pygame.K_w]:
        player_1.handle_user_input("up", dt)
    if key_pressed[pygame.K_a]:
        player_1.handle_user_input("left", dt)
    if key_pressed[pygame.K_d]:
        player_1.handle_user_input("right", dt)
    if key_pressed[pygame.K_s]:
        player_1.handle_user_input("down", dt)
    if key_pressed[pygame.K_UP]:
        player_2.handle_user_input("up", dt)
    if key_pressed[pygame.K_LEFT]:
        player_2.handle_user_input("left", dt)
    if key_pressed[pygame.K_RIGHT]:
        player_2.handle_user_input("right", dt)
    if key_pressed[pygame.K_DOWN]:
        player_2.handle_user_input("down", dt)


def draw(screen, player_1, player_2, car_images, finishline, camera_position):
    bauhaus_font = pygame.font.SysFont('bauhaus93', 32, bold=True)
    line = (finishline[0] + camera_position[0],
            finishline[1] + camera_position[1],
            finishline[2],
            finishline[3])
    pygame.draw.rect(screen, (100, 200, 50), line)
    player_1_score_text = bauhaus_font.render(
        f"Player 1 score: {player_1.score}", True, (255, 255, 0))
    player_2_score_text = bauhaus_font.render(
        f"Player 2 score: {player_2.score}", True, (255, 255, 0))
    screen.blit(player_2_score_text,
                (1280 - player_2_score_text.get_width() - 10, 10))
    screen.blit(player_1_score_text, (10, 10))
    player_1.draw(screen, car_images, camera_position)
    player_2.draw(screen, car_images, camera_position)


def color(r=0, g=0, b=0):
    return (r * 255, g * 255, b * 255)


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

    racetrack = pygame.image.load("assets/racetrack.png")
    scale = 8
    tire_marks_screen = pygame.transform.scale(
        pygame.Surface((1280, 720)), (1280 * scale, 720 * scale))
    tire_marks_replace_surface = pygame.Surface((1280, 720), pygame.SRCALPHA)
    tire_marks_replace_surface.blit(racetrack, (0, 0))
    tire_marks_screen.set_alpha(200)
    tire_marks_replace_surface = pygame.transform.scale(
        tire_marks_replace_surface, (1280 * scale, 720 * scale))
    racetrack = pygame.transform.scale(racetrack, (1280 * scale, 720 * scale))
    tire_marks_screen.blit(tire_marks_replace_surface, (0, 0))

    finishline = [1280 // 2, 360, 40, 200]
    # scale car images
    for i in range(len(car_images)):
        car_images[i] = pygame.transform.scale(
            car_images[i], (151 / 2, 303 / 2))

    running = True
    start_time = 0
    while running:
        dt = time.time() - start_time
        start_time = time.time()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        camera_position = (-player_1.position[0] + 1280 / 2, -
                           player_1.position[1] + 720 / 2)
        player_1.draw_tire_marks(tire_marks_screen)
        player_2.draw_tire_marks(tire_marks_screen)

        keys_pressed = pygame.key.get_pressed()
        if keys_pressed[pygame.K_ESCAPE]:
            running = False
        player_movement(keys_pressed, player_1, player_2, dt)
        player_1.update(dt, [], finishline)
        player_2.update(dt, [], finishline)
        # screen.blit(racetrack,
        #            (0, 0), (-camera_position[0], -camera_position[1], -camera_position[0] + 1280, -camera_position[1] + 720))
        screen.blit(tire_marks_screen, camera_position)
        draw(screen, player_1, player_2, car_images,
             finishline, camera_position)

        # if event.type == player_1_crosses_finishline:
        #    player_1_score += 1
        # if event.type == player_2_crosses_finishline:
        #    player_2_score += 1
        # Render the display onto the OpenGL display with the shaders!
        # screen = pygame.transform.scale(screen, (1280 * 2, 720 * 2))
        shader.render(screen)
        pygame.display.flip()

        clock.tick(60)  # limits FPS to 60

    pygame.quit()


if __name__ == "__main__":
    main()

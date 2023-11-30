import pygame
import pygame_shaders
import math
import time
import random
from game_data import walls, ai_waypoints
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


def lerp(a, b, i):
    dist = b - a
    dist = (dist + math.pi) % (2 * math.pi) - math.pi
    step = i
    if abs(dist) <= step:
        return b
    else:
        if dist < 0:
            step = -step
        a += step
    return a


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


def point_abb_distance(x, y, w, h, px, py):
    d = 0
    if px < x:
        d += pow(px - x, 2)
    elif px > (x + w):
        d += pow(px - (x + w), 2)

    if py < y:
        d += pow(py - y, 2)
    elif py > (y + h):
        d += pow(py - (y + h), 2)

    return math.sqrt(d)


def closest_point_to_aabb(x, y, w, h, cx, cy):
    hit_x, hit_y = cx, cy
    if cx < x:
        hit_x = x
    elif cx > (x + w):
        hit_x = x + w
    if cy < y:
        hit_y = y
    elif cy > (y + h):
        hit_y = y + h
    return hit_x, hit_y


def aabb_circle(x, y, w, h, cx, cy, radius):
    dist = point_abb_distance(x, y, w, h, cx, cy)
    hit_pos = closest_point_to_aabb(x, y, w, h, cx, cy)
    if dist < radius:
        return hit_pos, normalize((cx - hit_pos[0], cy - hit_pos[1])), radius - dist
    else:
        return False


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
    def __init__(self, position=None, radius=40.0, drag=0.3, angular_drag=4, angle=0, car_type=0) -> None:
        if position is None:
            position = [0.0, 0.0]
        self.position = position
        self.radius = radius
        self.velocity = [0.0, 0.0]
        self.drag = drag
        self.angular_drag = angular_drag
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
        acceleration = self.score * 1 + 15
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
        if input == "break":
            break_force = 1000
            if length(self.velocity) > break_force * dt:
                direction = normalize(self.velocity)
                self.velocity[0] -= direction[0] * break_force * dt
                self.velocity[1] -= direction[1] * break_force * dt
            else:
                self.velocity[0] = 0
                self.velocity[1] = 0

    def update(self, dt, walls, finishline):
        self.position[0] += self.velocity[0] * dt
        self.position[1] += self.velocity[1] * dt

        self.velocity[0] = mix(self.velocity[0], 0, dt * self.drag)
        self.velocity[1] = mix(self.velocity[1], 0, dt * self.drag)

        car_right_vector = [-math.sin(math.radians(self.angle)),
                            math.cos(math.radians(self.angle))]
        side_velocity = dot_product(car_right_vector, normalize(self.velocity))
        self.apply_force(
            car_right_vector[0] * -side_velocity * 15, car_right_vector[1] * -side_velocity * 15)
        strength = max((1000 - length(self.velocity)) / 1000, 0)
        self.apply_force(
            car_right_vector[0] * -side_velocity * strength * 10, car_right_vector[1] * -side_velocity * strength * 10)

        self.angular_velocity = mix(
            self.angular_velocity, 0, dt * self.angular_drag)

        self.angle += self.angular_velocity * dt
        for object in walls:
            collision = aabb_circle(object.position[0], object.position[1], object.size[0],
                                    object.size[1], self.position[0], self.position[1], self.radius)
            if collision != False:  # position,normal,depth
                self.position[0] += collision[1][0] * collision[2]
                self.position[1] += collision[1][1] * collision[2]

                direction = dot_product(self.velocity, collision[1])

                self.velocity[0] -= direction * collision[1][0]
                self.velocity[1] -= direction * collision[1][1]

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
            random_variation_color = random.random() * 0.1
            tire_color = color(0.3 + random_variation_color, 0.3 +
                               random_variation_color, 0.3 + random_variation_color)
            pygame.draw.circle(screen, tire_color, tire_1, 10, 0)
            tire_2 = rotate_point([x + 303 / 6, y - 151 / 6],
                                  self.position, self.angle)
            random_variation_color = random.random() * 0.1
            tire_color = color(0.3 + random_variation_color, 0.3 +
                               random_variation_color, 0.3 + random_variation_color)
            pygame.draw.circle(screen, tire_color, tire_2, 10, 0)
            tire_3 = rotate_point([x - 303 / 6, y + 151 / 6],
                                  self.position, self.angle)
            random_variation_color = random.random() * 0.1
            tire_color = color(0.3 + random_variation_color, 0.3 +
                               random_variation_color, 0.3 + random_variation_color)
            pygame.draw.circle(screen, tire_color, tire_3, 10, 0)
            tire_4 = rotate_point([x + 303 / 6, y + 151 / 6],
                                  self.position, self.angle)
            random_variation_color = random.random() * 0.1
            tire_color = color(0.3 + random_variation_color, 0.3 +
                               random_variation_color, 0.3 + random_variation_color)
            pygame.draw.circle(screen, tire_color, tire_4, 10, 0)


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
    if key_pressed[pygame.K_LCTRL]:
        player_1.handle_user_input("break", dt)
    if key_pressed[pygame.K_UP]:
        player_2.handle_user_input("up", dt)
    if key_pressed[pygame.K_LEFT]:
        player_2.handle_user_input("left", dt)
    if key_pressed[pygame.K_RIGHT]:
        player_2.handle_user_input("right", dt)
    if key_pressed[pygame.K_DOWN]:
        player_2.handle_user_input("down", dt)
    if key_pressed[pygame.K_RCTRL]:
        player_2.handle_user_input("break", dt)


def draw(screen, player_1, player_2, car_images, finishline, camera_position, tire_marks_screen, fps):
    screen.blit(tire_marks_screen, camera_position)
    bauhaus_font = pygame.font.SysFont('bauhaus93', 32, bold=True)
    line_1 = (finishline[0] + camera_position[0],
              finishline[1] + camera_position[1],
              finishline[2],
              finishline[3])
    pygame.draw.rect(screen, (100, 200, 50), line_1)
    player_1_score_text = bauhaus_font.render(
        f"Player 1 score: {player_1.score}", True, (255, 255, 0))
    player_2_score_text = bauhaus_font.render(
        f"Player 2 score: {player_2.score}", True, (255, 255, 0))
    screen.blit(player_2_score_text,
                (1280 - player_2_score_text.get_width() - 10, 10))
    screen.blit(player_1_score_text, (10, 10))
    player_1.draw(screen, car_images, camera_position)
    player_2.draw(screen, car_images, camera_position)
    fps_text = bauhaus_font.render(f"FPS{fps}", True, (255, 255, 0))
    screen.blit(fps_text, (10, 720 - fps_text.get_height() - 10))


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

    player_1 = Player(position=[4630, 875], angle=-180)
    player_2 = Player(car_type=2, position=[4940, 635], angle=-180)

    car_images = [
        pygame.image.load("assets/car_1.png"),
        pygame.image.load("assets/car_2.png"),
        pygame.image.load("assets/car_3.png"),
        pygame.image.load("assets/car_4.png"),
    ]

    racetrack = pygame.image.load("assets/racetrack.png")
    scale = 12
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

    for wall in walls:
        wall.position[0] *= scale
        wall.position[1] *= scale
        wall.size[0] *= scale
        wall.size[1] *= scale

    # added_waypoint_last_frame = False

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
        # if keys_pressed[pygame.K_SPACE]:
        #     if not added_waypoint_last_frame:
        #         ai_waypoints.append(
        #             (player_1.position[0], player_1.position[1]))
        #         added_waypoint_last_frame = True
        # else:
        #     added_waypoint_last_frame = False
        # if keys_pressed[pygame.K_y]:
        #     print(ai_waypoints)
        player_1.update(dt, walls, finishline)
        player_2.update(dt, walls, finishline)
        # screen.blit(racetrack,
        #            (0, 0), (-camera_position[0], -camera_position[1], -camera_position[0] + 1280, -camera_position[1] + 720))

        draw(screen, player_1, player_2, car_images,
             finishline, camera_position, tire_marks_screen, clock.get_fps())

        for waypoint in ai_waypoints:
            pygame.draw.circle(
                screen, (255, 0, 0), (waypoint[0]+camera_position[0], waypoint[1]+camera_position[1]), 20, 0)

        # Render the display onto the OpenGL display with the shaders!
        # screen = pygame.transform.scale(screen, (1280 * 2, 720 * 2))
        shader.render(screen)
        pygame.display.flip()

        clock.tick(60)  # limits FPS to 60

    pygame.quit()


if __name__ == "__main__":
    main()

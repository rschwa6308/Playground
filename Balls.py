import pygame as pg
import pygame.gfxdraw
from pygame.math import Vector2 as V2

from random import random, randint
from time import time
from itertools import combinations


class Body:
    fixed = False

    def __init__(self, pos, vel, mass, color=None, elasticity=None):
        self.pos = V2(pos)
        self.vel = V2(vel)
        self.mass = mass

        if color:
            self.color = color
        else:
            self.color = (randint(0, 255), randint(0, 255), randint(0, 255))

        if elasticity:
            self.elasticity = elasticity
        else:
            self.elasticity = 1.0

    def draw(self, screen, px_per_m):
        pass

    def apply_vel(self, time_step):
        self.pos += self.vel * time_step

    def apply_gravity(self, g, time_step):
        self.vel.y -= (g * time_step)

    def collide_walls(self, room_width, room_height):
        pass

    # should be mutual (a.collide_body(b) has the exact same effect as b.collide_body(a))
    def collide_body(self, other, time_step):
        if isinstance(self, Ball) and isinstance(other, Ball):
            if self.pos.distance_to(other.pos) < self.radius + other.radius:
                d = self.pos.distance_to(other.pos)
                n = (other.pos - self.pos) / d
                p = 2 * (self.vel.dot(n) - other.vel.dot(n)) / (self.mass + other.mass)
                self.vel -= p * other.mass * n * self.elasticity  # note: not sure if this actually conserves momentum (?)
                other.vel += p * self.mass * n * other.elasticity

                # move balls to be externally tangent
                desired_distance = self.radius + other.radius
                self.pos -= n * (desired_distance - d) * other.mass / (self.mass + other.mass)
                other.pos += n * (desired_distance - d) * self.mass / (self.mass + other.mass)

        else:
            ball = self if isinstance(self, Ball) else other
            platform = self if isinstance(self, Platform) else other

            # TODO: fix this and add side collision
            if platform.pos.x - ball.radius < ball.pos.x < platform.pos.x + platform.width + ball.radius:
                if platform.pos.y - ball.radius < ball.pos.y < platform.pos.y + platform.height + ball.radius:
                    ball.pos.y = platform.pos.y - ball.radius if ball.vel.y > 0 else platform.pos.y + platform.height + ball.radius
                    ball.vel.y *= -ball.elasticity



class Ball(Body):
    fixed = False

    def __init__(self, pos, vel, mass, radius, color=None, elasticity=None):
        super().__init__(pos, vel, mass, color, elasticity)
        self.radius = radius

    def draw(self, screen, px_per_m):
        px_pos = (round(self.pos.x * px_per_m), screen.get_height() - round(self.pos.y * px_per_m))  # flip y-axis
        px_radius = round(self.radius * px_per_m)  # add 1 to improve visual appearance of collisions
        pg.gfxdraw.filled_circle(screen, px_pos[0], px_pos[1], px_radius, self.color)
        pg.gfxdraw.aacircle(screen, px_pos[0], px_pos[1], px_radius, self.color)

    def apply_gravity(self, g, time_step):
        if self.pos.y > self.radius:        # emulates normal force (and prevents infinite tiny-bounce)
            self.vel.y -= (g * time_step)

    def collide_walls(self, room_width, room_height):
        if self.pos.x < self.radius:
            self.vel.x *= -self.elasticity
            self.pos.x = self.radius
        elif self.pos.x > room_width - self.radius:
            self.vel.x *= -self.elasticity
            self.pos.x = room_width - self.radius

        if self.pos.y < self.radius:
            self.vel.y *= -self.elasticity
            self.pos.y = self.radius
        elif self.pos.y > room_height - self.radius:
            self.vel.y *= -self.elasticity
            self.pos.y = room_height - self.radius


class Platform(Body):
    fixed = True

    def __init__(self, pos, dimensions, color=None, elasticity=None):
        super().__init__(pos, (0, 0), -1, color, elasticity)
        self.width, self.height = dimensions

    def draw(self, screen, px_per_m):
        px_pos = (round(self.pos.x * px_per_m), screen.get_height() - round((self.pos.y + self.height) * px_per_m))  # flip y-axis
        px_width = round(self.width * px_per_m)
        px_height = round(self.height * px_per_m)
        pg.gfxdraw.box(screen, pg.Rect(px_pos[0], px_pos[1], px_width, px_height), self.color)


class Simulation:
    def __init__(self, room_dimensions, bodies):
        self.room_width, self.room_height = room_dimensions
        self.bodies = bodies

        self.g = 9.8

    def draw(self, screen):
        px_per_m = screen.get_width() / self.room_width
        for body in self.bodies:
            body.draw(screen, px_per_m)

    def physics_step(self, time_step):
        for body in self.bodies:
            if not body.fixed:
                body.apply_gravity(self.g, time_step)
                body.collide_walls(self.room_width, self.room_height)

        for body_pair in combinations(self.bodies, 2):
            body_pair[0].collide_body(body_pair[1], time_step)

        for body in self.bodies:
            if not body.fixed:
                body.apply_vel(time_step)


def get_screen(resolution):
    pg.init()
    return pg.display.set_mode(resolution)


def get_simulation():
    room_dimensions = (8, 6)
    bodies = []
    # for _ in range(10):
    #     pos = (1 + random() * (room_dimensions[0] - 2), 1 + random() * (room_dimensions[1] - 2))
    #     vel = (8 * (random() - 0.5), 0)
    #     mass = randint(2, 15)
    #     radius = mass ** (1 / 3) * 0.1
    #     e = 0.98 # 0.85 + 0.14 * random()
    #     bodies.append(Ball(pos, vel, mass, radius, elasticity=e))
    # bodies.append(Platform((1, 1), (2, 0.5)))

    # bodies.append(Ball((4, 2), (0, 0), 50, 0.50))
    # bodies.append(Ball((4, 4), (0, 0), 1, 0.10))
    # bodies.append(Ball((4, 4.75), (0, 0), 50, 0.50))

    n = 10
    for i in range(n):
        bodies.append(Ball((4, i*room_dimensions[1]/n), (0, 0), 50, room_dimensions[1]/(4*n)))

    return Simulation(room_dimensions, bodies)


def main():
    # Set up simulation
    sim = get_simulation()
    sim_time_scale = 1.0  # adjusts speed of simulation without effecting frame rate

    # Initialize pygame and the display
    screen = get_screen((800, 600))
    fps_font = pg.font.SysFont("Segoe UI", 20)

    # Initialize timing system (hard max of 1000fps)
    ui_frame_rate = 60  # controls ui frame rate (should be left at 60)
    sim_frame_rate = 60 * 10  # controls simulation frame rate (works well to be a multiple of 60)

    ui_time_step = 1 / ui_frame_rate
    sim_time_step = 1 / sim_frame_rate

    ui_timestamp = 0  # timestamp of last ui update
    sim_timestamp = 0  # timestamp of last simulation update

    actual_fps_log = [0 for _ in range(sim_frame_rate)]
    moving_average = 0

    clock = pg.time.Clock()
    done = False
    while not done:
        sys_time = time()

        if sys_time - ui_timestamp >= ui_time_step:
            ui_timestamp = sys_time
            for event in pg.event.get():
                if event.type == pg.QUIT:
                    done = True

            screen.fill((255, 255, 255))
            sim.draw(screen)
            screen.blit(fps_font.render("fps: " + str(moving_average), True, (0, 0, 0)), (5, 0))
            pg.display.update()

        if sys_time - sim_timestamp >= sim_time_step:
            # calculate moving average of actual frame rate over one second
            actual_fps_log = actual_fps_log[1:]
            actual_fps_log.append(int(1/(sys_time - sim_timestamp)))
            moving_average = int(sum(actual_fps_log)/sim_frame_rate)

            sim_timestamp = sys_time
            sim.physics_step(sim_time_step * sim_time_scale)

        clock.tick(1000)  # prevents max cpu usage on loop


if __name__ == "__main__":
    main()

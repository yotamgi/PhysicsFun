import pygame
import time
import numpy
import copy
import math

CIRCLE_TIME = 0.05
C = 100.0

red = (255,0,0)
green = (0,255,0)
blue = (0,0,255)
darkBlue = (0,0,128)
white = (255,255,255)
black = (0,0,0)
pink = (255,200,200)

X = numpy.array([1, 0])
Y = numpy.array([0, 1])

def v2p(v):
    return [int(a) for a in v]
def r2d(angle):
    return 360. * angle/(2*math.pi)

class ConstCharge:
    def __init__(self):
        self.pos = numpy.array([400, 300.])

    def update(self, time_delta):
        pass

    def get_pos(self):
        return copy.copy(self.pos)
    def get_vel(self):
        return numpy.array([0, 0])

class ConstVCharge:
    def __init__(self):
        self.pos = numpy.array([0, 300.])
        self.v = numpy.array([C/2, 0])

    def update(self, time_delta):
        self.pos += time_delta * self.v

    def get_pos(self):
        return copy.copy(self.pos)
    def get_vel(self):
        return copy.copy(self.v)

class ConstACharge:
    def __init__(self):
        self.pos = numpy.array([400., 300.])
        self.v = numpy.array([0., 0.])
        self.a = numpy.array([C/20, 0])

    def update(self, time_delta):
        self.v += time_delta * self.a
        self.pos += time_delta * self.v

    def get_pos(self):
        return copy.copy(self.pos)
    def get_vel(self):
        return copy.copy(self.v)

class SinCharge:
    def __init__(self):
        self.pos = numpy.array([400., 300.])
        self.dir = X * C * 0.9
        self.t = 0.

    def update(self, time_delta):
        self.t += time_delta

    def get_pos(self):
        return self.pos + self.dir * math.sin(self.t)
    def get_vel(self):
        return self.dir * math.cos(self.t)

class RotCharge:
    def __init__(self):
        self.pos = numpy.array([400., 300.])
        self.t = 0.
        self.vel = 0.7 * C

    def update(self, time_delta):
        self.t += time_delta

    def get_pos(self):
        return self.pos + self.vel * (X * math.sin(self.t) + Y * math.cos(self.t))
    def get_vel(self):
        return self.vel * (X * math.cos(self.t) - Y * math.sin(self.t))

class StepCharge:
    def __init__(self):
        self.pos = numpy.array([400., 300.])
        self.rest_time = 2.
        self.max_v = 0.7 * C
        self.v = numpy.array([0.1, 0.])
        self.a = numpy.array([C, 0])
        self.timer = 0.
        self.state = 0

    def update(self, time_delta):
        self.timer += time_delta
        self.pos += time_delta * self.v

        if self.state == 0:
            if self.timer > self.rest_time:
                self.state = 1
                self.timer = 0.

        if self.state == 1:
            self.v += time_delta * self.a
            a_dir = numpy.dot(self.a, self.v)
            vel = numpy.linalg.norm(self.v)

            if (a_dir > 0 and vel > self.max_v) or (a_dir < 0 and vel < 0):
                self.state = 0
                self.a *= -1.
                self.timer = 0.

    def get_pos(self):
        return copy.copy(self.pos)
    def get_vel(self):
        return copy.copy(self.v)

def normalize(vec):
    norm = numpy.linalg.norm(vec)
    if norm == 0:
        return vec
    return vec/norm

class MouseCharge:
    def __init__(self):
        self.pos = numpy.array([400., 300.])
        pygame.mouse.set_pos(v2p(self.pos))
        self.v = numpy.array([0., 0.])
        self.max_v = C * 0.8
        self.reaction_time = 0.3

    def update(self, time_delta):
        mouse_pos = numpy.array(pygame.mouse.get_pos())
        v = mouse_pos - self.pos
        if numpy.linalg.norm(v) > self.max_v:
            v = normalize(v) * self.max_v
        self.v += (v - self.v) * time_delta / self.reaction_time

        self.pos += time_delta * self.v

    def get_pos(self):
        return copy.copy(self.pos)
    def get_vel(self):
        return copy.copy(self.v)


def N(angle):
    return numpy.array([math.cos(angle), math.sin(angle)])

class Fps:
    def __init__(self):
        self.timer = 0.
        self.counter = 0
        self.interval = 0.3

    def update(self, time_delta):
        self.timer += time_delta
        self.counter += 1

        if self.timer >= self.interval:
            print "FPS", self.counter / self.timer
            self.timer = 0.
            self.counter = 0

def transform_angle(angle, vel):
    vel_angle = math.atan(vel[1]/vel[0])
    rel_angle = angle - vel_angle
    
    if vel[0] == 0. and vel[1] == 0.:
        return angle

    beta = numpy.linalg.norm(vel)/C
    gamma = 1. / math.sqrt(1 - beta**2)

    new_rel_angle = math.atan(math.tan(rel_angle) * gamma)
    if rel_angle <= (3./2)*math.pi and rel_angle > math.pi/2:
        new_rel_angle += math.pi

    return new_rel_angle + vel_angle

screen = pygame.display.set_mode((800, 600))

#charge = ConstCharge()
#charge = ConstVCharge()
#charge = ConstACharge()
#charge = SinCharge()
#charge = RotCharge()
#charge = StepCharge()
charge = MouseCharge()
circle_timer = 0.
circles = []
prev = time.time()
fps = Fps()

MAX_CIRCLES = 800 / C / CIRCLE_TIME / 2

while True:
    now = time.time()
    time_delta = now - prev
    prev = now

    fps.update(time_delta)
    charge.update(time_delta)
    charge_pos = charge.get_pos()
    charge_vel = charge.get_vel()
    circle_timer += time_delta
    if circle_timer > CIRCLE_TIME:
        circle_timer = 0.
        circles.append((charge_pos, charge_vel, time.time()))

    if len(circles) > MAX_CIRCLES:
        circles.pop(0)

    # Draw the scene
    screen.fill(white)

    lines = [ [] for i in range(16)]
    for (center, vel, t) in circles:
        radius = int((now - t) * C)
        
        for i in range(len(lines)):
            angle = i * 2 * math.pi / 16.
            angle = transform_angle(angle, vel)
            curr = v2p(center + radius * N(angle))
            lines[i].append(curr)

    for line in lines:
        if len(line) > 1:
            pygame.draw.lines(screen, red, False, line, 2)

    pygame.display.update()
    for event in pygame.event.get():
        pass


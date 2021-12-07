import math
import numpy
import pyautogui
import random

def factorial(n: int):
    if n == 0:
        return 1
    return n * factorial(n - 1)

def choose(n, k):
    return factorial(n) / (factorial(k) * factorial(n - k))

class BezierCurve:

    def __init__(self, control_points: list[numpy.array]):
        self.control_points = control_points

    def eval(self, t):
        r = numpy.array([0.0, 0.0])
        n = len(self.control_points) - 1
        for i in range(n + 1):
            r += choose(n, i) * (1 - t) ** (n - i) * t ** i * self.control_points[i]
        return r

def bezier_builder(source_point: numpy.array, dest_point: numpy.array):
    control_points = [numpy.array(source_point)]
    delta = dest_point - source_point
    distance = numpy.linalg.norm(dest_point - source_point)
    # add a control point in the middle, sampled from a gaussian with 
    # standard deviation dependent on the total distance travelled
    cp1 = source_point + delta / 2
    cp1_std = distance / 4
    cp1_offset = numpy.array([random.gauss(0, cp1_std), random.gauss(0, cp1_std)])
    cp1 += cp1_offset
    control_points.append(cp1)
    # see if we generate a "missed target" control point
    cp2_chance = distance / 2000
    if random.random() < cp2_chance:
        cp2 = numpy.copy(dest_point)
        cp2_std = cp1_std / 4
        cp2_offset = numpy.array([random.gauss(0, cp2_std), random.gauss(0, cp2_std)])
        cp2 += cp2_offset
        control_points.append(cp2)
    control_points.append(dest_point)
    return BezierCurve(control_points)


class MouseMover:

    def __init__(self, bezier_curve: BezierCurve):
        self.bezier_curve = bezier_curve
        self.t = 0
        distance = numpy.linalg.norm(
            bezier_curve.control_points[-1] - \
            bezier_curve.control_points[0])
        if distance == 0:
            self.d_d_t = 1
        else:
            self.d_d_t = 1 / distance * 150
        self.d_t = 0

    def done(self):
        return self.t >= 1

    def continue_move(self):
        self.advance_t()
        target = self.bezier_curve.eval(self.t)
        pyautogui.moveTo(int(round(target[0])), int(round(target[1])))

    def advance_t(self):
        if self.t > 0.5:
            self.d_t -= self.d_d_t
        else:
            self.d_t += self.d_d_t
        if self.d_t < self.d_d_t:
            # if we've past the crest of the curve, we need to make sure 
            # our velocity always advances us, since d_d_t is then 
            # effectively negative
            self.d_t = self.d_d_t
        self.t += self.d_t
        if self.t > 1.0:
            self.t = 1.0


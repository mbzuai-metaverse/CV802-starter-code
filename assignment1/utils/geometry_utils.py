import math


def create_quaternion(angle, axis):
    w = math.cos(angle / 2)
    x = axis[0] * math.sin(angle / 2)
    y = axis[1] * math.sin(angle / 2)
    z = axis[2] * math.sin(angle / 2)
    return [x, y, z, w]


def multiply_quaternions(q1, q2):
    x1, y1, z1, w1 = q1
    x2, y2, z2, w2 = q2

    x =  w1*x2 + x1*w2 + y1*z2 - z1*y2
    y =  w1*y2 - x1*z2 + y1*w2 + z1*x2
    z =  w1*z2 + x1*y2 - y1*x2 + z1*w2
    w =  w1*w2 - x1*x2 - y1*y2 - z1*z2

    return [x, y, z, w]

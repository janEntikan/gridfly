from random import randint, choice
from direct.actor.Actor import Actor
from panda3d.core import NodePath
from panda3d.core import LineSegs


def limit_node(node):
    xsize, ysize = base.map_size
    if node.get_x() > xsize:
        node.set_x(xsize)
    elif node.get_x() < -xsize:
        node.set_x(-xsize)
    if node.get_y() > ysize:
        node.set_y(ysize)
    elif node.get_y() < 0:
        node.set_y(0)


class Mine():
    def __init__(self, pos):
        self.time = 0
        self.node = NodePath("segment")
        self.cross = NodePath("cross")
        base.models["misc"]["egg"].instance_to(self.node)
        self.node.reparent_to(render)
        self.cross.reparent_to(render)
        self.node.set_pos(pos)
        self.cross.set_pos(pos)
        base.mines.append(self)
        self.blown = False

    def destroy(self):
        base.mines.remove(self)
        self.node.remove_node()
        self.cross.remove_node()

    def update(self):
        self.time += globalClock.get_dt()
        if self.time > 1:
            if not self.blown:
                self.blown = True
                base.models["lines"]["cross"].instance_to(self.cross)
            self.cross.set_scale(self.cross.get_scale()+0.2)
            self.cross.set_color((0,1,0,1))
        if self.time > 5:
            self.destroy()


class EnemySegment():
    def __init__(self, geometry, length=0, x=0, y=0, following=None):
        self.node = NodePath("segment")
        geometry.copy_to(self.node)
        self.node.reparent_to(render)
        self.node.set_y(45-y)
        self.node.set_x(x)
        self.following = following
        self.follower = None
        if length > 0:
            self.follower = EnemySegment(
                geometry, length=length-1, x=x, y=y-1, following=self)
            base.segments.append(self.follower)
        self.angle = 180
        self.head = self.node.find("**/head")
        self.mid = self.node.find("**/mid")
        self.tail = self.node.find("**/tail")

    def destroy(self):
        if self.following:
            Mine(self.node.get_pos())
            self.following.follower = None
        if self.follower:
            self.follower.angle += randint(-45,45)
            self.follower.following = None
        base.segments.remove(self)
        self.node.remove_node()

    def update(self):
        self.head.hide()
        self.mid.hide()
        self.tail.hide()
        if self.following:
            self.node.set_pos(self.following.node.get_pos())
            if self.follower:   self.mid.show()
            else:               self.tail.show()
            self.angle = self.following.angle
            self.node.set_h(self.following.angle)
        else:
            self.head.show()
            if randint(0,16) == 0:
                self.angle += randint(-45, 45)
            self.node.set_h(self.angle)
            self.node.set_pos(self.node, (0,1,0))
            x, y, z = self.node.get_pos()
            xsize, ysize = base.map_size
            if x < -xsize or x > xsize or y < 0 or y > ysize:
                self.angle += 180 + randint(-45, 45)
            limit_node(self.node)


class Bullet():
    def __init__(self, pos):
        self.node = NodePath("bullet")
        base.models["misc"]["bullet"].instance_to(self.node)
        self.node.reparent_to(render)
        pos.y += 1
        self.node.set_sy(0.1)
        self.node.set_pos(pos)
        base.bullets.append(self)
        self.speed = 0.4

    def destroy(self):
        self.node.remove_node()
        base.bullets.remove(self)

    def update(self):
        y = self.node.get_y()
        self.node.set_y(y+self.speed)

        scale = self.node.get_sy()
        if scale < 1:
            self.node.set_sy(scale+0.1)
        if y > 60:
            self.destroy()
            return
        x, y, z = self.node.get_pos()
        size = 0.60
        for segment in base.segments:
            xs, ys, zs = segment.node.get_pos()
            if x > xs-size and x < xs+size:
                if y > ys-size and y < ys+size:
                    segment.destroy()
                    self.destroy()
                    base.player.extra_bullet += 1
                    return


class Player():
    def __init__(self):
        self.node = Actor("models/butterfly.bam")
        self.node.set_scale(0.4)
        self.node.reparent_to(render)
        self.node.loop("flap")
        self.bullet_timer = [0, 0.1]
        self.movement = [0, 0, 0]
        self.extra_bullet = 0
        self.accel = 4
        self.speed = 1

    def update(self):
        context = base.device_listener.read_context('game')
        gx, gy = context["movement"]
        for a, axis in enumerate((gx, gy)):
            accel = self.accel*globalClock.get_dt()
            if axis:
                self.movement[a] += axis*accel
            elif self.movement[a] > 0.1:
                self.movement[a] -= accel
            elif self.movement[a] < -0.1:
                self.movement[a] += accel
            else:
                self.movement[a] = 0

            if self.movement[a] > self.speed:
                self.movement[a] = self.speed
            elif self.movement[a] < -self.speed:
                self.movement[a] = -self.speed

        self.node.set_pos(self.node, tuple(self.movement))
        limit_node(self.node)
        self.bullet_timer[0] += globalClock.get_dt()
        if self.bullet_timer[0] > self.bullet_timer[1]:
            self.bullet_timer[0] -= self.bullet_timer[1]
            Bullet(self.node.get_pos())
        elif self.extra_bullet > 0:
            self.extra_bullet -= 1
            Bullet(self.node.get_pos())

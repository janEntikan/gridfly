import sys
from random import randint, choice, uniform
from direct.actor.Actor import Actor
from panda3d.core import NodePath
from panda3d.core import Vec3


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


class Flower():
    def __init__(self, pos):
        self.node = NodePath("segment")
        base.models["misc"]["flower"].instance_to(self.node)
        self.node.reparent_to(render)
        self.node.set_pos(pos)
        base.flowers.append(self)
        base.announce(choice(("here_comes_flower", "little_flower")))
        self.time = 0
        self.flowerpower = 4

    def destroy(self):
        base.flowers.remove(self)
        self.node.remove_node()

    def update(self):
        self.node.set_scale(self.node.get_scale()-globalClock.get_dt()/25)
        scale = self.node.get_scale().x
        if scale <= 0.1:
            self.destroy()
            return
        self.node.set_h(self.node.get_h()+1)
        vector = base.player.node.getPos() - self.node.getPos()
        distance = vector.get_xy().length()
        if distance < 1:
            base.sounds["2d"]["zap_b"].play()
            self.destroy()
            base.announce("flower_power")
            base.player.flowerpower = self.flowerpower*scale
            base.player.zapping = self.flowerpower*scale


class Explosion():
    def __init__(self, geometry, pos, speed=1):
        self.node = NodePath("segment")
        geometry.instance_to(self.node)
        self.node.reparent_to(render)
        self.node.set_pos(pos)
        self.node.set_scale(0.01)
        base.explosions.append(self)
        self.time = 0
        self.speed = speed
        if speed > 2:
            e = "explosion_b"
            base.sounds["2d"][e].set_play_rate(1)
        else:
            e = "explosion_s"
            base.sounds["2d"][e].set_play_rate(1/speed)

        base.sounds["2d"][e].play()

    def destroy(self):
        base.explosions.remove(self)
        self.node.remove_node()

    def update(self):
        self.time += globalClock.get_dt()
        self.node.set_scale(self.node.get_scale()+((0.005/self.time)*self.speed))
        self.node.set_transparency(True)
        self.node.set_alpha_scale((0.5-self.time)*self.speed)
        if self.time > (0.5*(self.speed)):
            self.destroy()


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
        Explosion(base.models["misc"]["explosion_a"], self.node.get_pos())
        base.mines.remove(self)
        self.node.remove_node()
        self.cross.remove_node()

    def update(self):
        self.time += globalClock.get_dt()
        if self.time > 1:
            if not self.blown:
                base.sounds["2d"]["lines"].set_loop(True)
                base.sounds["2d"]["lines"].play()
                self.blown = True
                base.models["lines"]["cross"].instance_to(self.cross)
            self.cross.set_scale(self.cross.get_scale()+0.2)
            self.cross.set_color((0,1,0,1))
            # Hittest with player
            x, y, z = self.node.get_pos()
            s = self.cross.get_scale()
            px, py, pz = base.player.node.get_pos()
            width = 0.2
            if (x < px+width and x > px-width) or (y < py+width and y > py-width):
                vector = base.player.node.getPos() - self.node.getPos()
                distance = vector.get_xy().length()
                if distance < s:
                    base.player.die()
        if self.time > 5:
            self.destroy()
            return


class Chaser():
    def __init__(self, geometry, pos, speed=6):
        self.node = NodePath("segment")
        geometry.instance_to(self.node)
        self.node.reparent_to(render)
        self.node.set_pos(pos)
        self.speed = speed
        self.flash = False

    def destroy(self):
        base.chasers.remove(self)
        self.node.remove_node()

    def update(self):
        dt = globalClock.get_dt()
        if self.flash:
            self.flash = False
            self.node.set_color(1,1,1,1)
        else:
            self.node.clear_color()
        if base.player.alive:
            vector = base.player.node.getPos() - self.node.getPos()
            distance = vector.get_xy().length()
            if distance < 0.8:
                base.player.die(spider=True)
            vector.normalize()
            self.node.set_pos(self.node.get_pos()+(vector*(self.speed*dt)))
            self.node.look_at(base.player.node)
        else:
            self.node.set_pos(self.node, (0,self.speed*dt,0))

class EnemySegment():
    def __init__(self, geometry, length=0, x=0, y=0, following=None):
        self.node = NodePath("segment")
        geometry.copy_to(self.node)
        self.node.reparent_to(render)
        self.node.set_y(base.map_size[1]+y)
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
        self.ouch = 0

    def destroy(self, zapped=False):
        Explosion(base.models["misc"]["explosion_a"], self.node.get_pos(), speed=uniform(1,2))
        if self.following:
            if not zapped:
                Mine(self.node.get_pos())
            self.following.follower = None
        if self.follower:
            if base.flower_time[0] >= base.flower_time[1]:
                Flower(self.node.get_pos())
                base.flower_time[0] = 0
            if not self.following:
                self.follower.ouch = 0.3
            else:
                self.follower.angle += randint(-45,45)
            self.follower.following = None
        base.segments.remove(self)
        self.node.remove_node()

    def update(self):
        dt =  globalClock.get_dt()
        if self.ouch > 0:
            self.ouch -= dt
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
            if randint(0,16) == 0 and self.ouch <= 0:
                self.angle += randint(-45, 45)
            self.node.set_h(self.angle)
            self.node.set_pos(self.node, (0,1,0))
            x, y, z = self.node.get_pos()
            xsize, ysize = base.map_size
            if x < -xsize or x > xsize or y < 0 or y > ysize:
                self.angle += 180 + randint(-45, 45)
            limit_node(self.node)

        vector = base.player.node.getPos() - self.node.getPos()
        distance = vector.get_xy().length()
        if distance < 0.8:
            base.player.die()


class Bullet():
    def __init__(self, pos, scale=1):
        self.node = NodePath("bullet")
        base.models["misc"]["bullet"].instance_to(self.node)
        self.node.reparent_to(render)
        pos.y += 1
        self.node.set_sy(0.1)
        self.node.set_scale(scale)
        self.node.set_pos(pos)
        base.bullets.append(self)
        self.speed = 0.4
        self.scale = scale

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
        enemy_size = self.scale
        me_size = 0.1
        for segment in base.segments:
            vector = segment.node.getPos() - self.node.getPos()
            distance = vector.get_xy().length()
            if distance < 0.5:
                segment.destroy()
                self.destroy()
                base.player.flowerpower += 0.05
                return
        for chaser in base.chasers:
            vector = chaser.node.getPos() - self.node.getPos()
            distance = vector.get_xy().length()
            if distance < 0.5:
                chaser.flash = True
                base.sounds["2d"]["bounce"].play()
                self.destroy()
                return


class Player():
    def __init__(self):
        self.node = Actor("models/butterfly.bam")
        self.node.set_scale(0.4)
        self.node.reparent_to(render)
        self.node.loop("flap")
        self.node.hide()
        self.bullet_timer = [0, 0.1]
        self.movement = [0, 0, 0]
        self.accel = 4
        self.speed = 1
        self.zapping = 0
        self.flowerpower = 0
        self.alive = False

    def spawn(self, pos):
        self.node.show()
        self.node.set_pos(pos)
        self.alive = True
        self.zapping = self.flowerpower = 0

    def update(self):
        dt = globalClock.get_dt()
        context = base.device_listener.read_context('game')
        gx, gy = context["movement"]
        for a, axis in enumerate((gx, gy)):
            accel = self.accel*dt
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
        if self.flowerpower > 0:
            self.flowerpower -= dt
            self.bullet_timer[1] = 0.05
            offset = uniform(-0.5, 0.5)
            scale = 2
        else:
            offset = 0
            self.bullet_timer[1] = 0.1
            scale = 1

        self.bullet_timer[0] += dt
        if self.bullet_timer[0] > self.bullet_timer[1]:
            base.sounds["2d"]["bullet"].set_play_rate(uniform(0.8,1.2))
            base.sounds["2d"]["bullet"].play()
            self.bullet_timer[0] -= self.bullet_timer[1]
            pos = self.node.get_pos()
            pos.x += offset
            Bullet(pos, scale)

        if self.zapping > 0:
            self.zapping -= dt
            self.zap()

    def zap(self):
        if len(base.mines) > 0:
            base.sounds["2d"]["zap_a"].play()
            mine = choice(base.mines)
            base.zapline(self.node, mine.node)
            mine.destroy()
        if len(base.segments) > 0:
            base.sounds["2d"]["zap_a"].play()
            segment = choice(base.segments)
            base.zapline(self.node, segment.node)
            segment.destroy(zapped=True)

    def die(self, spider=False):
        if self.alive:
            base.sounds["2d"]["die"].play()
            if not spider:
                base.announce(choice(("you_die", "die")))
            else:
                base.announce("got_you")
            self.node.hide()
            Explosion(base.models["misc"]["explosion_b"], self.node.get_pos(), speed=3)
        self.alive = False

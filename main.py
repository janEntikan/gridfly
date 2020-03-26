import sys
import math
from random import randint
from collections import defaultdict

from direct.showbase.ShowBase import ShowBase
import panda3d
import pman.shim

from keybindings.device_listener import add_device_listener
from keybindings.device_listener import SinglePlayerAssigner

from lines import *
from objects import *

panda3d.core.load_prc_file(
    panda3d.core.Filename.expand_from('$MAIN_DIR/settings.prc')
)


class GameApp(ShowBase):
    def __init__(self):
        ShowBase.__init__(self)
        pman.shim.init(self)
        base.win.set_clear_color((0,0,0,1))
        self.accept('escape', sys.exit)
        add_device_listener(
            config_file='keybindings.toml',
            assigner=SinglePlayerAssigner(),
        )

        self.level = 0
        self.map_size = [25,50]
        self.camera = NodePath("camera")
        #base.cam.set_pos(0,-25,50)
        base.cam.set_pos(0, -30, 40)
        base.cam.set_p(-50)
        base.cam.reparent_to(self.camera)
        self.camera.reparent_to(render)

        self.load_models()
        draw_lines(self)

        self.player = Player()
        self.player.node.set_y(20)
        self.segment_time = [0, 0.06]

        self.segments = []
        self.chasers = []
        self.bullets = []
        self.mines = []
        self.explosions = []
        self.zaplines = []

        self.task_mgr.add(self.update_objects)

        self.chasers.append(Chaser(self.models["chasers"]["spider"], (0,40,0)))

        for i in range(3):
            bg = NodePath("bg")
            self.models["backgrounds"]["0"].instance_to(bg)
            bg.reparent_to(render)
            bg.set_pos(0,0,-20-(i*20))
            bg.set_scale(self.map_size[0]*4, self.map_size[1]*2, 1)
            bg.set_transparency(True)
            bg.set_alpha_scale(0.03)

    def zapline(self, a, b):
        color = choice(((1,0,1,1), (1,0,0,1), (0,1,0,1), (0,1,1,1), (0,0,1,1)))

        base.linesegs.set_color(color)

        base.linesegs.move_to(a.get_pos())
        base.linesegs.draw_to(b.get_pos())
        line = render.attach_new_node(base.linesegs.create())
        base.zaplines.append(line)

    def load_models(self):
        models = ["enemies", "misc"]
        self.models = {}
        for model in models:
            self.models[model] = {}
            for child in loader.loadModel("models/{}.bam".format(model)).get_children():
                for child_child in child.get_children():
                    child_child.set_pos(child, (0,0,0))
                child.set_pos((0,0,0))
                child.detach_node()
                self.models[model][child.name] = child
        self.models["chasers"] = {}
        self.models["chasers"]["spider"] = Actor("models/spider.bam")
        self.models["chasers"]["spider"].loop("walk")
        self.models["chasers"]["spider"].set_play_rate(2, "walk")

        self.models["backgrounds"] = {}
        self.models["backgrounds"]["0"] = Actor("models/bg_0.bam")
        self.models["backgrounds"]["0"].loop("animation")

    def make_enemies(self):
        amount = self.level
        gap = (self.map_size[0]*2)/amount
        for i in range(amount):
            self.segments.append(EnemySegment(self.models["enemies"]["cent1"], length=16, x=-self.map_size[0]+(gap*i)))

    def update_objects(self, task):
        dt = globalClock.get_dt()
        for zapline in self.zaplines:
            zapline.remove_node()
            self.zaplines.remove(zapline)

        if self.player.alive:
            self.player.update()
        for explosion in self.explosions:
            explosion.update()
        for bullet in self.bullets:
            bullet.update()
        for mine in self.mines:
            mine.update()
        for chaser in self.chasers:
            chaser.update()
        # segments
        self.segment_time[0] += dt
        if self.segment_time[0] > self.segment_time[1]:
            self.segment_time[0] -= self.segment_time[1]
            for s, segment in enumerate(self.segments):
                try:
                    segment.update()
                except:
                    pass
        # end wave
        if len(self.segments) == 0:
            self.level += 1
            self.player.zapping = -1
            self.make_enemies()

        # camera
        vector = base.player.node.getPos() - self.camera.getPos()
        self.camera.set_pos(self.camera.get_pos()+(vector*(4*dt)))
        return task.cont


def main():
    app = GameApp()
    app.run()

if __name__ == '__main__':
    main()

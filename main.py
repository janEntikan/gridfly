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

        self.level = 1
        self.camera = NodePath("camera")
        #base.cam.set_pos(0,-25,50)
        base.cam.set_pos(0, -30, 40)
        base.cam.set_p(-50)
        base.cam.reparent_to(self.camera)
        self.camera.reparent_to(render)

        self.map_size = [25,50]
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

        self.task_mgr.add(self.update_player)
        self.task_mgr.add(self.update_segments)
        self.task_mgr.add(self.update_chasers)
        self.task_mgr.add(self.update_bullets)
        self.task_mgr.add(self.update_mines)
        self.task_mgr.add(self.update_explosions)

        self.task_mgr.add(self.update_camera)

    def make_enemies(self, amount):
        self.chasers.append(Chaser(self.models["chasers"]["spider"], (0,40,0)))
        gap = (self.map_size[0]*2)/amount
        for i in range(amount):
            self.segments.append(EnemySegment(self.models["enemies"]["cent1"], length=16, x=-self.map_size[0]+(gap*i)))

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

    def update_player(self, task):
        self.player.update()
        return task.cont

    def update_explosions(self, task):
        for explosion in self.explosions:
            explosion.update()
        return task.cont

    def update_bullets(self, task):
        for bullet in self.bullets:
            bullet.update()
        return task.cont

    def update_mines(self, task):
        for mine in self.mines:
            mine.update()
        return task.cont

    def update_chasers(self, task):
        for chaser in self.chasers:
            chaser.update()
        return task.cont

    def update_segments(self, task):
        self.segment_time[0] += globalClock.get_dt()
        if self.segment_time[0] > self.segment_time[1]:
            self.segment_time[0] -= self.segment_time[1]
            for segment in self.segments:
                segment.update()
        if len(self.segments) == 0:
            self.level += 1
            self.make_enemies(self.level)
        return task.cont

    def update_camera(self, task):
        dt = globalClock.get_dt()
        #self.camera.set_pos(self.player.node.get_pos())
        vector = base.player.node.getPos() - self.camera.getPos()
        #distance = vector.get_xy().length()
        #vector.normalize()
        self.camera.set_pos(self.camera.get_pos()+(vector*(4*dt)))

        return task.cont


def main():
    app = GameApp()
    app.run()

if __name__ == '__main__':
    main()

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
        base.cam.set_pos(0,-25,50)
        base.cam.set_p(-50)
        base.cam.reparent_to(self.camera)
        self.camera.reparent_to(render)

        self.map_size = [25,45]
        self.load_models()
        draw_lines(self)

        self.player = Player()
        self.bullets = []
        self.segments = []
        self.mines = []
        self.segment_time = [0, 0.06]

        self.taskMgr.add(self.update_player)
        self.taskMgr.add(self.update_bullets)
        self.taskMgr.add(self.update_segments)
        self.taskMgr.add(self.update_mines)
        self.taskMgr.add(self.update_camera)

    def make_enemies(self, amount):
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

    def update_player(self, task):
        self.player.update()
        return task.cont

    def update_bullets(self, task):
        for bullet in self.bullets:
            bullet.update()
        return task.cont

    def update_mines(self, task):
        for mine in self.mines:
            mine.update()
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
        self.camera.set_pos(render, self.player.node.get_pos())



def main():
    app = GameApp()
    app.run()

if __name__ == '__main__':
    main()

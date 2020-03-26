import sys
import math
from random import randint
from collections import defaultdict

from direct.showbase.ShowBase import ShowBase
import panda3d
import pman.shim

from keybindings.device_listener import add_device_listener
from keybindings.device_listener import SinglePlayerAssigner

from sounds import load_sounds
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

        self.map_size = [25,50]
        self.segment_time = [0, 0.06]
        self.flower_time = [0, 4]
        self.camera = NodePath("camera")
        #base.cam.set_pos(0,-25,50)
        base.cam.set_pos(0, -30, 40)
        base.cam.set_p(-50)
        base.cam.reparent_to(self.camera)
        self.camera.reparent_to(render)
        self.sounds = load_sounds()
        self.load_models()
        self.music = loader.load_sfx("music/song1.ogg")
        self.music.set_loop(True)
        self.music.play()
        self.bg = NodePath("bg")
        for i in range(3):
            bg = self.bg.attach_new_node("bg-"+str(i))
            self.models["backgrounds"]["0"].instance_to(bg)
            bg.set_pos(0,0,-20-(i*20))
        self.bg.set_scale(self.map_size[0]*4, self.map_size[1]*2, 1)
        self.bg.set_transparency(True)
        self.bg.set_alpha_scale(0.03)
        self.bg.reparent_to(render)
        self.segments = []
        self.chasers = []
        self.flowers = []
        self.bullets = []
        self.mines = []
        self.explosions = []
        self.zaplines = []
        self.player = Player()
        self.task_mgr.add(self.update_objects)

    def destroy(self):
        while len(self.segments) > 0: self.segments[0].destroy()
        while len(self.chasers) > 0: self.chasers[0].destroy()
        while len(self.flowers) > 0: self.flowers[0].destroy()
        while len(self.bullets) > 0: self.bullets[0].destroy()
        while len(self.mines) > 0: self.mines[0].destroy()
        while len(self.explosions) > 0: self.explosions[0].destroy()
        while len(self.zaplines) > 0: self.zaplines[0].destroy()

    def start(self):
        self.destroy()
        self.announce("starting_game")
        draw_lines(self)
        self.level = 1
        self.player.spawn((0,20,0))
        self.chasers.append(Chaser(self.models["chasers"]["spider"], (0,40,0)))
        self.make_enemies()

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
            self.flower_time[0] += dt
            self.player.update()
            if self.player.zapping > 0:
                self.bg.set_alpha_scale(0.2)
            else:
                self.bg.set_alpha_scale(0.03)
        for explosion in self.explosions:
            explosion.update()
        for bullet in self.bullets:
            bullet.update()
        for mine in self.mines:
            mine.update()
        if len(self.mines) == 0:
            self.sounds["2d"]["lines"].stop()
        for chaser in self.chasers:
            chaser.update()
        for flower in self.flowers:
            flower.update()
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
        if len(self.segments) == 0 and base.player.alive:
            self.announce(choice(("give_it_to_me", "oh_baby", "sexy", "thats_the_stuff")))
            self.level += 1
            self.player.zapping = -1
            self.player.flowerpower = 0
            self.flower_time[0] = 0
            self.make_enemies()

        # camera
        vector = base.player.node.getPos() - self.camera.getPos()
        self.camera.set_pos(self.camera.get_pos()+(vector*(4*dt)))

        if not self.player.alive:
            if self.device_listener.read_context('game')["spawn"]:
                self.start()

        return task.cont

    def announce(self, say):
        base.sounds["announce"][say].play()

def main():
    app = GameApp()
    app.run()

if __name__ == '__main__':
    main()

import sys
import math
from random import randint
from collections import defaultdict

from direct.showbase.ShowBase import ShowBase
import panda3d
import pman.shim

from keybindings.device_listener import add_device_listener
from keybindings.device_listener import SinglePlayerAssigner

from panda3d.core import TextNode

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
        self.flower_time = [0, 4, 0]
        self.camera = NodePath("camera")
        #base.cam.set_pos(0,-25,50)
        base.cam.set_pos(0, -30, 40)
        base.cam.set_p(-50)
        base.cam.reparent_to(self.camera)
        self.camera.reparent_to(render)
        self.sounds = load_sounds()
        self.music = loader.load_sfx("music/song1.ogg")
        self.music.set_loop(True)
        self.music.play()
        self.load_models()
        self.bg = self.bg_model = None
        self.make_background()

        self.fonts = {}
        self.fonts["dot"] = loader.loadFont("fonts/dotrice.otf")
        self.fonts["pixel"] = loader.loadFont("fonts/pressstart2p.ttf")

        ## FLOATING TEXT GARBAGE
        self.textimation = Actor("models/textimation.bam")
        self.textimation.loop("animation")
        self.announcement = TextNode("announcement")
        self.announcement.font = self.fonts["dot"]
        self.announcement.text = ">>GRIDFLY<<\n\nPRESS SPACE TO START\n\n\nMADE BY HENDRIK-JAN\n\nFOR PYWEEK29\n\nPANDA3D FOR THE WIN"
        self.announcement.align = 2
        self.announcement.set_text_color((1,0,1,1))
        self.a_root = render.attach_new_node("announcement")
        self.a_node = NodePath("announcement")
        self.announcement_node = self.a_node.attach_new_node(self.announcement)
        self.announcement_node.set_scale(5)
        self.announcement_node.set_p(-130)
        for i in range(4):
            n = self.a_root.attach_new_node(str("t"+str(i)))
            self.a_node.instance_to(n)
            n.set_z(i)
        self.textimation.expose_joint(self.a_node, jointName="text", partName="modelRoot")
        self.a_root.reparent_to(self.camera)
        self.a_root.set_pos((0,70,-50))
        self.a_root.set_transparency(True)
        self.a_root.set_alpha_scale(0.5)
        self.text_timer = 0
        ## END FLOATING TEXT GARBAGE

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
        self.a_root.set_pos((0,40,-50))
        self.announcement_node.set_scale(6)
        self.flower_time[0] = 0
        self.destroy()
        self.announce("starting_game", "LEVEL 1")
        draw_lines(self)
        self.level = 1
        self.player.spawn((0,20,0))
        self.chasers.append(Chaser(self.models["chasers"]["spider"], (0,120,0)))
        self.make_enemies()

    def zapline(self, a, b):
        color = choice(((1,0,1,1), (1,0,0,1), (0,1,0,1), (0,1,1,1), (0,0,1,1)))
        base.linesegs.set_thickness(randint(3,5))
        base.linesegs.set_color(color)
        base.linesegs.move_to(a.get_pos())
        base.linesegs.draw_to(b.get_pos())
        line = render.attach_new_node(base.linesegs.create())
        base.zaplines.append(line)

    def make_background(self, n=0):
        if self.bg_model:
            self.bg_model.remove_node()
        if self.bg:
            self.bg.remove_node()
        self.bg_model = Actor("models/bg_"+str(n)+".bam")
        self.bg_model.loop("animation")
        self.bg = NodePath("bg")
        for i in range(3):
            bg = self.bg.attach_new_node("bg-"+str(i))
            self.bg_model.instance_to(bg)
            bg.set_pos(0,0,-20-(i*20))
        self.bg.set_scale(self.map_size[0]*4, self.map_size[1]*2, 1)
        self.bg.set_transparency(True)
        self.bg.set_alpha_scale(0.03)
        self.bg.reparent_to(render)

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

    def make_enemies(self):
        amount = self.level
        gap = (self.map_size[0]*2)/amount
        for i in range(amount):
            self.segments.append(EnemySegment(self.models["enemies"]["cent1"], length=16, x=-self.map_size[0]+(gap*i)))

    def update_objects(self, task):
        dt = globalClock.get_dt()
        if self.text_timer > 0 and self.player.alive:
            self.text_timer -= dt
            if self.text_timer < 0:
                self.text_timer = 0
                self.announcement.text = ""

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
            self.level += 1
            self.player.zapping = -1
            self.player.flowerpower = 0
            self.flower_time[0] = 0
            self.announce(choice(("give_it_to_me", "oh_baby", "sexy", "thats_the_stuff")), "LEVEL " + str(self.level))
            self.make_enemies()
        # camera
        vector = base.player.node.getPos() - self.camera.getPos()
        self.camera.set_pos(self.camera.get_pos()+(vector*(4*dt)))
        if not self.player.alive:
            if self.device_listener.read_context('game')["spawn"]:
                self.start()
        return task.cont

    def announce(self, say, extra=""):
        for sound in base.sounds["announce"]:
            base.sounds["announce"][sound].stop()
        base.sounds["announce"][say].play()
        s = say.split("_")
        s = " ".join(s)
        self.textimation.loop("animation")
        self.announcement.text = s.upper() + "!!!"+"\n\n"+extra
        self.text_timer = 2

def main():
    app = GameApp()
    app.run()

if __name__ == '__main__':
    main()

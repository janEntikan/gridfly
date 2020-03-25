from panda3d.core import NodePath, SequenceNode, LineSegs

def draw_lines(base):
    linesegs = LineSegs("lines")

    # Border
    xs, ys = base.map_size
    sequence = SequenceNode("border")
    for color in ((0,0,0.1,1), (0,0,0.2,1), (0,0,0.3,1), (0,0,0.2,1)):
        linesegs.set_color(color)
        linesegs.set_thickness(3)
        linesegs.move_to((-xs,0,0))
        linesegs.draw_to((-xs,ys,0))
        linesegs.draw_to((xs,ys,0))
        linesegs.draw_to((xs,0,0))
        linesegs.draw_to((-xs,0,0))
        lines = linesegs.create()
        sequence.add_child(lines)
    sequence.loop(True)
    sequence.set_frame_rate(30)
    base.border = render.attach_new_node(sequence)
    for i in range(2):
        n = NodePath("border")
        base.border.instance_to(n)
        n.reparent_to(render)
        n.set_z(-(i*5))



    # Mine cross
    base.models["lines"] = {}
    base.models["lines"]["cross"] = NodePath("cross")
    sequence = SequenceNode("cross")
    for color in ((1,0,0,1), (1,0,1,1), (0,1,0,1), (1,1,0,1)):
        linesegs.set_thickness(3)
        linesegs.move_to((1,0,0))
        linesegs.draw_to((-1,0,0))
        linesegs.move_to((0,1,0))
        linesegs.draw_to((0,-1,0))
        linesegs.set_color(color)
        lines = linesegs.create()
        sequence.add_child(lines)
    sequence.loop(True)
    sequence.set_frame_rate(60)
    base.models["lines"]["cross"].attach_new_node(sequence)

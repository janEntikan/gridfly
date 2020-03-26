def load_sounds():
    loaded_sounds = {}
    # 2d sounds
    loaded_sounds["2d"] = {}
    sounds = (
        "bounce", "bullet", "die", "explosion_s", "explosion_b",
        "gameover", "lines", "zap_a", "zap_b"
    )
    for sound in sounds:
        loaded_sounds["2d"][sound] = loader.load_sfx("sfx/"+sound+".ogg")
        loaded_sounds["2d"][sound].set_volume(2)
    # 3d sounds
    loaded_sounds["3d"] = {}
    sounds = (
        "spider",
    )
    for sound in sounds:
        loaded_sounds["3d"][sound] = loader.load_sfx("sfx/"+sound+".ogg")
    # announcer
    loaded_sounds["announce"] = {}
    sounds = (
        "butterzapper", "die", "flowerpower", "gameover", "giveittome",
        "goodbye", "gotyou", "herecomesflower", "littleflower", "obaby",
        "sexy", "soclose", "startinggame", "supercombo", "sure",
        "thatsthestuff", "youdie"
    )
    for sound in sounds:
        loaded_sounds["announce"][sound] = loader.load_sfx("announcer/"+sound+".ogg")
        loaded_sounds["announce"][sound].set_volume(0.5)
    return loaded_sounds

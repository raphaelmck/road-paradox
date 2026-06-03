from manim import *

# Color palette
BACKGROUND = "#0F0F0F"
PRIMARY = WHITE
ACCENT = "#58C4DD"
HIGHLIGHT = "#FFFF00"
DIM = "#888888"

# Typography
FONT = "SF Pro Display"

# Standard camera config overrides (apply in scene's setup())
def apply_style(scene: Scene):
    scene.camera.background_color = BACKGROUND

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

from manim import *
from src.style import apply_style, BACKGROUND, DIM, FONT
import numpy as np

HOME     = np.array([-4.8, 0, 0])
DOWNTOWN = np.array([ 4.8, 0, 0])

ROUTE_COLOR    = "#666666"
SHORTCUT_COLOR = "#FFD700"
ARC_ANGLE      = PI * 0.62   # pronounced bow without leaving the frame

CAR_PALETTE = [
    "#58C4DD", "#3DB8D0", "#72D4E8",
    "#26A8C4", "#89DCF0", "#1E9CB8",
    "#A0E4F8", "#4EC8DC",
]

_RNG = np.random.default_rng(42)


class ObviousSolution(Scene):
    def setup(self):
        apply_style(self)

    def construct(self):
        self.add(self._grid())
        self._phase_nodes()
        self._phase_cars()        # sets up jitter timer before routes draw
        self._phase_upper()
        self._phase_lower()
        self._phase_shortcut()
        self._phase_question()

    # ── helpers ──────────────────────────────────────────────────────────────

    def _grid(self):
        g = VGroup()
        for x in np.arange(-7, 7.1, 1.5):
            g.add(Line([x, -5, 0], [x, 5, 0], stroke_width=0.7, stroke_color="#1B1B1B"))
        for y in np.arange(-4, 4.1, 1.5):
            g.add(Line([-8, y, 0], [8, y, 0], stroke_width=0.7, stroke_color="#1B1B1B"))
        return g

    def _node(self, name: str, pos, outward: np.ndarray):
        outer = Circle(radius=0.22, stroke_width=2.5, stroke_color=WHITE, fill_opacity=0)
        inner = Dot(pos, radius=0.10, color=WHITE)
        outer.move_to(pos)
        label = Text(name, font=FONT, font_size=26, color=DIM)
        label.next_to(outer, DOWN, buff=0.45)
        label.shift(outward * 0.45)
        return VGroup(outer, inner), label

    def _route_label(self, text: str, arc: VMobject, v_dir: np.ndarray, t: float):
        lbl = Text(text, font=FONT, font_size=20, color=DIM)
        lbl.move_to(arc.point_from_proportion(t) + v_dir * 0.48)
        return lbl

    # ── phases ───────────────────────────────────────────────────────────────

    def _phase_nodes(self):
        home,  home_lbl  = self._node("HOME",     HOME,     LEFT)
        dtown, dtown_lbl = self._node("DOWNTOWN", DOWNTOWN, RIGHT)
        self.play(
            FadeIn(home,  scale=1.3), Write(home_lbl),
            FadeIn(dtown, scale=1.3), Write(dtown_lbl),
            run_time=1.1,
        )
        self.wait(0.6)

    def _phase_cars(self):
        n = 38

        # symmetric spread centered on HOME
        offsets = _RNG.uniform(low=[-0.42, -0.32, 0], high=[0.42, 0.32, 0], size=(n, 3))
        offsets[:, 2] = 0

        colors = [CAR_PALETTE[i % len(CAR_PALETTE)] for i in range(n)]

        # per-dot jitter parameters
        freqs_x  = _RNG.uniform(0.25, 0.7, n)
        freqs_y  = _RNG.uniform(0.25, 0.7, n)
        phases_x = _RNG.uniform(0, TAU, n)
        phases_y = _RNG.uniform(0, TAU, n)
        amp = 0.035

        # single timer drives all dots
        self._timer = ValueTracker(0)
        self._timer.add_updater(lambda m, dt: m.increment_value(dt))
        self.add(self._timer)

        self.cars = VGroup()
        for i in range(n):
            base = (HOME + offsets[i]).copy()
            dot  = Dot(base, radius=0.065, color=colors[i], fill_opacity=0.88)

            def make_updater(b, fx, fy, px, py):
                def u(d):
                    t = self._timer.get_value()
                    d.move_to(b + np.array([
                        amp * np.sin(TAU * fx * t + px),
                        amp * np.sin(TAU * fy * t + py),
                        0,
                    ]))
                return u

            dot.add_updater(make_updater(base, freqs_x[i], freqs_y[i], phases_x[i], phases_y[i]))
            self.cars.add(dot)

        self.play(FadeIn(self.cars, lag_ratio=0.03), run_time=1.0)
        self.wait(1.0)

    def _phase_upper(self):
        self.upper = ArcBetweenPoints(HOME, DOWNTOWN, angle=ARC_ANGLE)
        self.upper.set_stroke(color=ROUTE_COLOR, width=3)
        # label on outer arc, pushed toward the DOWNTOWN end
        lbl = self._route_label("top road", self.upper, UP, t=0.72)

        self.play(Create(self.upper), run_time=1.1)
        self.play(FadeIn(lbl), run_time=0.5)
        self.wait(0.6)

    def _phase_lower(self):
        self.lower = ArcBetweenPoints(HOME, DOWNTOWN, angle=-ARC_ANGLE)
        self.lower.set_stroke(color=ROUTE_COLOR, width=3)
        lbl = self._route_label("bottom road", self.lower, DOWN, t=0.72)

        self.play(Create(self.lower), run_time=1.1)
        self.play(FadeIn(lbl), run_time=0.5)
        self.wait(1.5)

    def _phase_shortcut(self):
        top_pt = self.upper.point_from_proportion(0.5)
        bot_pt = self.lower.point_from_proportion(0.5)

        self.play(
            self.upper.animate.set_stroke(color="#BBBBBB", width=4),
            self.lower.animate.set_stroke(color="#BBBBBB", width=4),
            run_time=0.5,
        )

        glow = DashedLine(
            top_pt, bot_pt,
            dash_length=0.20, dashed_ratio=0.55,
            stroke_color=SHORTCUT_COLOR, stroke_width=18,
        ).set_stroke(opacity=0.12)

        shortcut = DashedLine(
            top_pt, bot_pt,
            dash_length=0.20, dashed_ratio=0.55,
            stroke_color=SHORTCUT_COLOR, stroke_width=4,
        )

        self.play(
            LaggedStart(FadeIn(glow), Create(shortcut), lag_ratio=0.1),
            run_time=1.4,
        )
        self.wait(0.9)

    def _phase_question(self):
        q = Text("More roads = less traffic?", font=FONT, font_size=40, color=WHITE)
        q.to_edge(DOWN, buff=0.65)
        self.play(Write(q), run_time=1.1)
        self.wait(2.5)

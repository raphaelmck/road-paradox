import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

from manim import *
from src.style import apply_style, DIM
import numpy as np

HOME     = np.array([-4.8, 0, 0])
DOWNTOWN = np.array([ 4.8, 0, 0])

ROUTE_COLOR    = "#666666"
SHORTCUT_COLOR = "#FFD700"
ARC_ANGLE      = PI * 0.62

# route labels: right-align both at this x so the trailing "d" of "road" lines up
LABEL_RIGHT_X = 6.2

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
        self._phase_cars()
        self._phase_labels_settle()
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

    def _node(self, name: str, pos):
        outer = Circle(radius=0.22, stroke_width=2.5, stroke_color=WHITE, fill_opacity=0)
        inner = Dot(pos, radius=0.10, color=WHITE)
        outer.move_to(pos)
        # label starts white and centered below the dot
        label = Tex(name, font_size=26, color=WHITE)
        label.next_to(outer, DOWN, buff=0.28)
        return VGroup(outer, inner), label

    def _route_label(self, text: str, y_pos: float):
        """Right-align label to LABEL_RIGHT_X so both trailing 'd's share an x."""
        lbl = Tex(text, font_size=20, color=DIM)
        lbl.align_to(np.array([LABEL_RIGHT_X, 0, 0]), RIGHT)
        lbl.set_y(y_pos)
        return lbl

    # ── phases ───────────────────────────────────────────────────────────────

    def _phase_nodes(self):
        self.home_node, self.home_lbl  = self._node("HOME",     HOME)
        self.dtown_node, self.dtown_lbl = self._node("DOWNTOWN", DOWNTOWN)
        self.play(
            FadeIn(self.home_node,  scale=1.3), Write(self.home_lbl),
            FadeIn(self.dtown_node, scale=1.3), Write(self.dtown_lbl),
            run_time=1.1,
        )
        self.wait(0.6)

    def _phase_cars(self):
        n = 38
        offsets = _RNG.uniform(low=[-0.42, -0.32, 0], high=[0.42, 0.32, 0], size=(n, 3))
        offsets[:, 2] = 0
        colors   = [CAR_PALETTE[i % len(CAR_PALETTE)] for i in range(n)]
        freqs_x  = _RNG.uniform(0.25, 0.7,  n)
        freqs_y  = _RNG.uniform(0.25, 0.7,  n)
        phases_x = _RNG.uniform(0,    TAU,  n)
        phases_y = _RNG.uniform(0,    TAU,  n)
        amp = 0.035

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

    def _phase_labels_settle(self):
        """Animate node labels from white/centered to grey/edge-aligned."""
        self.play(
            self.home_lbl.animate.set_color(DIM).shift(DOWN * 0.30 + LEFT * 0.55),
            self.dtown_lbl.animate.set_color(DIM).shift(DOWN * 0.30 + RIGHT * 0.55),
            run_time=0.7,
        )
        self.wait(0.3)

    def _phase_upper(self):
        self.upper = ArcBetweenPoints(HOME, DOWNTOWN, angle=ARC_ANGLE)
        self.upper.set_stroke(color=ROUTE_COLOR, width=3)

        # anchor y to arc at t=0.82 (right portion) then step outside the curve
        top_y = self.upper.point_from_proportion(0.82)[1] + 0.44
        lbl   = self._route_label("top road", top_y)

        self.play(Create(self.upper), run_time=1.1)
        self.play(FadeIn(lbl), run_time=0.5)
        self.wait(0.6)

    def _phase_lower(self):
        self.lower = ArcBetweenPoints(HOME, DOWNTOWN, angle=-ARC_ANGLE)
        self.lower.set_stroke(color=ROUTE_COLOR, width=3)

        bot_y = self.lower.point_from_proportion(0.82)[1] - 0.44
        lbl   = self._route_label("bottom road", bot_y)

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
        q = Tex(r"More roads $=$ less traffic?", font_size=40, color=WHITE)
        q.to_edge(DOWN, buff=0.65)
        self.play(Write(q), run_time=1.1)
        self.wait(2.5)

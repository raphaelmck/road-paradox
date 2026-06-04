import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

from manim import *
from src.style import apply_style, DIM, FONT
import numpy as np

START = np.array([-4.5,  0.0, 0])
END   = np.array([ 4.5,  0.0, 0])
A_POS = np.array([ 0.0,  2.5, 0])
B_POS = np.array([ 0.0, -2.5, 0])

NODE_R      = 0.22
ROUTE_COLOR = "#666666"

CAR_PALETTE = [
    "#58C4DD", "#3DB8D0", "#72D4E8",
    "#26A8C4", "#89DCF0", "#1E9CB8",
    "#A0E4F8", "#4EC8DC",
]

_RNG = np.random.default_rng(7)


class RoadNetwork(Scene):
    def setup(self):
        apply_style(self)

    def construct(self):
        self.add(self._grid())
        self._phase_nodes()
        self._phase_cars()
        self._phase_roads()
        self._phase_fixed_labels()
        self._phase_dynamic_labels()
        self._phase_closing()

    # ── helpers ──────────────────────────────────────────────────────────────

    def _grid(self):
        g = VGroup()
        for x in np.arange(-7, 7.1, 1.5):
            g.add(Line([x, -5, 0], [x, 5, 0], stroke_width=0.7, stroke_color="#1B1B1B"))
        for y in np.arange(-4, 4.1, 1.5):
            g.add(Line([-8, y, 0], [8, y, 0], stroke_width=0.7, stroke_color="#1B1B1B"))
        return g

    def _node(self, name: str, pos, label_dir):
        outer = Circle(radius=NODE_R, stroke_width=2.5, stroke_color=WHITE, fill_opacity=0)
        inner = Dot(pos, radius=0.10, color=WHITE)
        outer.move_to(pos)
        lbl = Text(name, font=FONT, font_size=26, color=DIM)
        lbl.next_to(outer, label_dir, buff=0.3)
        return VGroup(outer, inner), lbl

    def _road(self, p1, p2):
        return Arrow(
            p1, p2,
            buff=NODE_R + 0.06,
            stroke_width=3,
            color=ROUTE_COLOR,
            tip_length=0.22,
            max_stroke_width_to_length_ratio=999,
        )

    def _road_label(self, text, road, perp_offset):
        mid = road.point_from_proportion(0.5)
        lbl = Text(text, font=FONT, font_size=19, color=DIM)
        lbl.move_to(mid + perp_offset)
        return lbl

    # ── phases ───────────────────────────────────────────────────────────────

    def _phase_nodes(self):
        s_node, s_lbl = self._node("Start", START, LEFT)
        e_node, e_lbl = self._node("End",   END,   RIGHT)
        a_node, a_lbl = self._node("A",     A_POS, UP)
        b_node, b_lbl = self._node("B",     B_POS, DOWN)

        self.play(
            LaggedStart(
                AnimationGroup(FadeIn(s_node, scale=1.3), Write(s_lbl)),
                AnimationGroup(FadeIn(e_node, scale=1.3), Write(e_lbl)),
                AnimationGroup(FadeIn(a_node, scale=1.3), Write(a_lbl)),
                AnimationGroup(FadeIn(b_node, scale=1.3), Write(b_lbl)),
                lag_ratio=0.25,
            ),
            run_time=1.8,
        )
        self.wait(0.6)

    def _phase_cars(self):
        n = 180
        offsets       = _RNG.uniform([-0.50, -0.28, 0], [0.50, 0.28, 0], (n, 3))
        offsets[:, 2] = 0
        freqs_x  = _RNG.uniform(0.20, 0.65, n)
        freqs_y  = _RNG.uniform(0.20, 0.65, n)
        phases_x = _RNG.uniform(0, TAU, n)
        phases_y = _RNG.uniform(0, TAU, n)
        amp = 0.022

        self._timer = ValueTracker(0)
        self._timer.add_updater(lambda m, dt: m.increment_value(dt))
        self.add(self._timer)

        self.cars = VGroup()
        for i in range(n):
            base  = (START + offsets[i]).copy()
            color = CAR_PALETTE[i % len(CAR_PALETTE)]
            dot   = Dot(base, radius=0.040, color=color, fill_opacity=0.82)

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

        count_lbl = Text("4,000 drivers", font=FONT, font_size=22, color=DIM)
        count_lbl.move_to(START + UP * 0.62)

        self.play(
            FadeIn(self.cars, lag_ratio=0.008),
            FadeIn(count_lbl),
            run_time=1.2,
        )
        self.wait(1.2)

    def _phase_roads(self):
        self.road_sa = self._road(START, A_POS)   # Start → A  (top-left)
        self.road_ae = self._road(A_POS, END)     # A → End    (top-right)
        self.road_sb = self._road(START, B_POS)   # Start → B  (bottom-left)
        self.road_be = self._road(B_POS, END)     # B → End    (bottom-right)

        self.play(
            LaggedStart(
                Create(self.road_sa),
                Create(self.road_ae),
                Create(self.road_sb),
                Create(self.road_be),
                lag_ratio=0.30,
            ),
            run_time=2.0,
        )
        self.wait(0.6)

    def _phase_fixed_labels(self):
        # Top-right (A → End) and bottom-left (Start → B) are fixed at 45 min.
        # Perpendicular offsets push labels away from the road line.
        self.lbl_ae = self._road_label("45 min", self.road_ae, np.array([ 0.30,  0.55, 0]))
        self.lbl_sb = self._road_label("45 min", self.road_sb, np.array([-0.30, -0.55, 0]))

        self.play(
            LaggedStart(FadeIn(self.lbl_ae), FadeIn(self.lbl_sb), lag_ratio=0.4),
            run_time=0.9,
        )
        self.wait(2.0)

    def _phase_dynamic_labels(self):
        # Top-left (Start → A) and bottom-right (B → End) are traffic-dependent.
        self.lbl_sa = self._road_label("t = cars / 100", self.road_sa, np.array([-0.30,  0.55, 0]))
        self.lbl_be = self._road_label("t = cars / 100", self.road_be, np.array([ 0.30, -0.55, 0]))

        self.play(
            LaggedStart(FadeIn(self.lbl_sa), FadeIn(self.lbl_be), lag_ratio=0.4),
            run_time=0.9,
        )
        self.wait(2.8)

    def _phase_closing(self):
        q = Text(
            "Each person just wants to get there as fast as possible.",
            font=FONT, font_size=32, color=WHITE,
        )
        q.to_edge(DOWN, buff=0.65)
        self.play(Write(q), run_time=1.2)
        self.wait(2.5)

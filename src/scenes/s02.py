import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

from manim import *
from src.style import apply_style, DIM, FONT
import numpy as np

# ── s01 constants (to reconstruct the end state) ──────────────────────────────
_HOME           = np.array([-4.8, 0, 0])
_DOWNTOWN       = np.array([ 4.8, 0, 0])
_ARC_ANGLE      = PI * 0.62
_SHORTCUT_COLOR = "#FFD700"
_LABEL_RIGHT_X  = -4.6

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
        self._load_s01_state()
        self._phase_transition()
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

    # ── s01 end-state reconstruction ─────────────────────────────────────────

    def _load_s01_state(self):
        """Add every element that was visible at the end of s01, with no animation."""
        home_outer = Circle(radius=0.22, stroke_width=2.5, stroke_color=WHITE, fill_opacity=0)
        home_outer.move_to(_HOME)
        home_inner = Dot(_HOME, radius=0.10, color=WHITE)

        dtown_outer = Circle(radius=0.22, stroke_width=2.5, stroke_color=WHITE, fill_opacity=0)
        dtown_outer.move_to(_DOWNTOWN)
        dtown_inner = Dot(_DOWNTOWN, radius=0.10, color=WHITE)

        # Settled label positions from s01's _phase_labels_settle
        home_lbl = Tex("HOME", font_size=26, color=DIM)
        home_lbl.next_to(home_outer, DOWN, buff=0.28)
        home_lbl.shift(DOWN * 0.30 + LEFT * 0.55)

        dtown_lbl = Tex("DOWNTOWN", font_size=26, color=DIM)
        dtown_lbl.next_to(dtown_outer, DOWN, buff=0.28)
        dtown_lbl.shift(DOWN * 0.30 + RIGHT * 0.55)

        upper = ArcBetweenPoints(_HOME, _DOWNTOWN, angle=_ARC_ANGLE)
        upper.set_stroke(color="#BBBBBB", width=4)
        lower = ArcBetweenPoints(_HOME, _DOWNTOWN, angle=-_ARC_ANGLE)
        lower.set_stroke(color="#BBBBBB", width=4)

        top_y = upper.point_from_proportion(0.5)[1] + 0.36
        top_lbl = Tex("top road", font_size=20, color=DIM)
        top_lbl.align_to(np.array([_LABEL_RIGHT_X, 0, 0]), RIGHT)
        top_lbl.set_y(top_y)

        bot_y = lower.point_from_proportion(0.5)[1] - 0.36
        bot_lbl = Tex("bottom road", font_size=20, color=DIM)
        bot_lbl.align_to(np.array([_LABEL_RIGHT_X, 0, 0]), RIGHT)
        bot_lbl.set_y(bot_y)

        top_pt = upper.point_from_proportion(0.5)
        bot_pt = lower.point_from_proportion(0.5)
        glow = DashedLine(
            top_pt, bot_pt,
            dash_length=0.20, dashed_ratio=0.55,
            stroke_color=_SHORTCUT_COLOR, stroke_width=18,
        ).set_stroke(opacity=0.12)
        shortcut = DashedLine(
            top_pt, bot_pt,
            dash_length=0.20, dashed_ratio=0.55,
            stroke_color=_SHORTCUT_COLOR, stroke_width=4,
        )

        q = Tex(r"More roads $=$ less traffic?", font_size=40, color=WHITE)
        q.to_edge(DOWN, buff=0.65)

        _PAL = ["#58C4DD", "#3DB8D0", "#72D4E8", "#26A8C4",
                "#89DCF0", "#1E9CB8", "#A0E4F8", "#4EC8DC"]
        try:
            positions = np.load("media/s01_car_positions.npy")
        except FileNotFoundError:
            positions = np.empty((0, 3))

        self._s01_cars = VGroup(*[
            Dot(positions[i], radius=0.065,
                color=_PAL[i % len(_PAL)], fill_opacity=0.88)
            for i in range(len(positions))
        ])

        self._s01_overlay = VGroup(
            VGroup(home_outer, home_inner),
            VGroup(dtown_outer, dtown_inner),
            home_lbl, dtown_lbl,
            upper, lower, top_lbl, bot_lbl,
            glow, shortcut, q,
        )
        self.add(self._s01_overlay, self._s01_cars)

    def _phase_transition(self):
        self.play(
            FadeOut(self._s01_overlay),
            FadeOut(self._s01_cars),
            run_time=0.8,
        )

    # ── phases ───────────────────────────────────────────────────────────────

    def _phase_nodes(self):
        s_node, s_lbl = self._node("Start", START, LEFT)
        e_node, e_lbl = self._node("End",   END,   RIGHT)
        a_node, a_lbl = self._node("A",     A_POS, UP)
        b_node, b_lbl = self._node("B",     B_POS, DOWN)

        self.s_node, self.s_lbl = s_node, s_lbl
        self.e_node, self.e_lbl = e_node, e_lbl
        self.a_node, self.a_lbl = a_node, a_lbl
        self.b_node, self.b_lbl = b_node, b_lbl

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

        self.count_lbl = Text("4,000 drivers", font=FONT, font_size=22, color=DIM)
        self.count_lbl.move_to(START + UP * 0.62)

        self.play(
            FadeIn(self.cars, lag_ratio=0.008),
            FadeIn(self.count_lbl),
            run_time=1.2,
        )
        self.wait(1.2)

    def _phase_roads(self):
        self.road_sa = self._road(START, A_POS)
        self.road_ae = self._road(A_POS, END)
        self.road_sb = self._road(START, B_POS)
        self.road_be = self._road(B_POS, END)

        self.play(
            LaggedStart(
                GrowArrow(self.road_sa),
                GrowArrow(self.road_ae),
                GrowArrow(self.road_sb),
                GrowArrow(self.road_be),
                lag_ratio=0.30,
            ),
            run_time=2.0,
        )
        self.wait(0.6)

    def _phase_fixed_labels(self):
        self.lbl_ae = self._road_label("45 min", self.road_ae, np.array([ 0.30,  0.55, 0]))
        self.lbl_sb = self._road_label("45 min", self.road_sb, np.array([-0.30, -0.55, 0]))

        self.play(
            LaggedStart(FadeIn(self.lbl_ae), FadeIn(self.lbl_sb), lag_ratio=0.4),
            run_time=0.9,
        )
        self.wait(2.0)

    def _phase_dynamic_labels(self):
        self.lbl_sa = self._road_label("t = cars / 100", self.road_sa, np.array([-0.30,  0.55, 0]))
        self.lbl_be = self._road_label("t = cars / 100", self.road_be, np.array([ 0.30, -0.55, 0]))

        self.play(
            LaggedStart(FadeIn(self.lbl_sa), FadeIn(self.lbl_be), lag_ratio=0.4),
            run_time=0.9,
        )
        self.wait(2.8)

    def _phase_closing(self):
        # Stop jitter so the cars can be shifted cleanly
        for dot in self.cars:
            dot.clear_updaters()
        self._timer.clear_updaters()

        # Shift all network content up; A/B labels get an extra nudge left
        content = VGroup(
            self.s_node, self.s_lbl, self.e_node, self.e_lbl,
            self.a_node, self.b_node,
            self.road_sa, self.road_ae, self.road_sb, self.road_be,
            self.lbl_ae, self.lbl_sb, self.lbl_sa, self.lbl_be,
            self.cars, self.count_lbl,
        )
        self.play(
            content.animate.shift(UP * 0.5),
            self.a_lbl.animate.shift(UP * 0.5 + LEFT * 0.25),
            self.b_lbl.animate.shift(UP * 0.5 + LEFT * 0.25),
            run_time=0.6,
        )

        q = Tex(
            "Each person wants to get there as fast as possible.",
            font_size=32, color=WHITE,
        )
        q.to_edge(DOWN, buff=0.65)
        self.play(Write(q), run_time=1.2)
        self.wait(2.5)

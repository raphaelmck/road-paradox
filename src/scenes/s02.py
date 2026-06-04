import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

from manim import *
from src.style import apply_style, DIM, FONT
import numpy as np

# ── s01 constants (for seamless continuation) ─────────────────────────────────
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


class RoadNetwork(Scene):
    def setup(self):
        apply_style(self)

    def construct(self):
        self.add(self._grid())
        self._load_s01_state()
        self._phase_transition()
        self._phase_nodes()
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
        lbl = Tex(text, font_size=19, color=DIM)
        lbl.move_to(mid + perp_offset)
        return lbl

    # ── s01 end-state reconstruction ─────────────────────────────────────────

    def _load_s01_state(self):
        """Reconstruct s01's end state. Timer + jitter start on frame 1."""
        # Trackers shared by all car updaters for the whole scene
        self._timer   = ValueTracker(0)
        self._x_shift = ValueTracker(0)
        self._y_shift = ValueTracker(0)
        self._timer.add_updater(lambda m, dt: m.increment_value(dt))
        self.add(self._timer, self._x_shift, self._y_shift)

        # ── nodes ─────────────────────────────────────────────────────────────
        home_outer = Circle(radius=0.22, stroke_width=2.5, stroke_color=WHITE, fill_opacity=0)
        home_outer.move_to(_HOME)
        home_inner = Dot(_HOME, radius=0.10, color=WHITE)

        dtown_outer = Circle(radius=0.22, stroke_width=2.5, stroke_color=WHITE, fill_opacity=0)
        dtown_outer.move_to(_DOWNTOWN)
        dtown_inner = Dot(_DOWNTOWN, radius=0.10, color=WHITE)

        # ── node labels — kept alive, morphed via ReplacementTransform ────────
        self._s01_home_lbl = Tex("HOME", font_size=26, color=DIM)
        self._s01_home_lbl.next_to(home_outer, DOWN, buff=0.28)
        self._s01_home_lbl.shift(DOWN * 0.30 + LEFT * 0.55)

        self._s01_dtown_lbl = Tex("DOWNTOWN", font_size=26, color=DIM)
        self._s01_dtown_lbl.next_to(dtown_outer, DOWN, buff=0.28)
        self._s01_dtown_lbl.shift(DOWN * 0.30 + RIGHT * 0.55)

        # ── edges / shortcut / question — faded out in transition ─────────────
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

        self._s01_fading = VGroup(
            upper, lower, top_lbl, bot_lbl,
            glow, shortcut, q,
        )

        # ── cars: identical style to s01, jittering from frame 1 ─────────────
        try:
            bases = np.load("media/s01_car_positions.npy")
        except FileNotFoundError:
            bases = np.empty((0, 3))

        n   = len(bases)
        amp = 0.035                        # matches s01 amplitude exactly
        rng = np.random.default_rng(13)
        fx  = rng.uniform(0.25, 0.70, max(n, 1))
        fy  = rng.uniform(0.25, 0.70, max(n, 1))
        px  = rng.uniform(0, TAU,  max(n, 1))
        py  = rng.uniform(0, TAU,  max(n, 1))

        def make_updater(b, fxi, fyi, pxi, pyi):
            def u(d):
                t  = self._timer.get_value()
                dx = self._x_shift.get_value()
                dy = self._y_shift.get_value()
                d.move_to(b + np.array([
                    amp * np.sin(TAU * fxi * t + pxi) + dx,
                    amp * np.sin(TAU * fyi * t + pyi) + dy,
                    0,
                ]))
            return u

        self._s01_cars = VGroup()
        for i in range(n):
            dot = Dot(bases[i], radius=0.065,
                      color=CAR_PALETTE[i % len(CAR_PALETTE)], fill_opacity=0.88)
            dot.add_updater(make_updater(bases[i].copy(), fx[i], fy[i], px[i], py[i]))
            self._s01_cars.add(dot)

        self._s01_home_node  = VGroup(home_outer, home_inner)
        self._s01_dtown_node = VGroup(dtown_outer, dtown_inner)

        self.add(
            self._s01_home_node, self._s01_dtown_node,
            self._s01_home_lbl, self._s01_dtown_lbl,
            self._s01_fading,
            self._s01_cars,
        )

    def _phase_transition(self):
        """Fade out old edges, shortcut, and edge labels only."""
        self.play(FadeOut(self._s01_fading), run_time=0.8)
        self.wait(0.3)

    # ── phases ───────────────────────────────────────────────────────────────

    def _phase_nodes(self):
        s_lbl = Tex("Start", font_size=26, color=DIM)
        s_lbl.next_to(Circle(radius=NODE_R).move_to(START), LEFT, buff=0.3)

        e_lbl = Tex("End", font_size=26, color=DIM)
        e_lbl.next_to(Circle(radius=NODE_R).move_to(END), RIGHT, buff=0.3)

        a_node, a_lbl = self._node("A", A_POS, UP)
        b_node, b_lbl = self._node("B", B_POS, DOWN)

        # Cars follow the node slide via the x_shift tracker
        x_delta = float(START[0] - _HOME[0])   # +0.3

        self.play(
            self._s01_home_node.animate.move_to(START),
            self._s01_dtown_node.animate.move_to(END),
            self._x_shift.animate.set_value(x_delta),
            ReplacementTransform(self._s01_home_lbl,  s_lbl),
            ReplacementTransform(self._s01_dtown_lbl, e_lbl),
            LaggedStart(
                AnimationGroup(FadeIn(a_node, scale=1.3), Write(a_lbl)),
                AnimationGroup(FadeIn(b_node, scale=1.3), Write(b_lbl)),
                lag_ratio=0.4,
            ),
            run_time=1.8,
        )

        self.s_node = self._s01_home_node
        self.s_lbl  = s_lbl
        self.e_node = self._s01_dtown_node
        self.e_lbl  = e_lbl
        self.a_node, self.a_lbl = a_node, a_lbl
        self.b_node, self.b_lbl = b_node, b_lbl

        self.wait(0.6)

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
        self.lbl_sa = self._road_label(
            r"$t = \mathrm{cars}/100$", self.road_sa, np.array([-0.30,  0.55, 0]))
        self.lbl_be = self._road_label(
            r"$t = \mathrm{cars}/100$", self.road_be, np.array([ 0.30, -0.55, 0]))

        self.play(
            LaggedStart(FadeIn(self.lbl_sa), FadeIn(self.lbl_be), lag_ratio=0.4),
            run_time=0.9,
        )
        self.wait(2.8)

    def _phase_closing(self):
        # Network elements shift up directly; cars shift via _y_shift (jitter keeps running)
        content = VGroup(
            self.s_node, self.s_lbl, self.e_node, self.e_lbl,
            self.a_node, self.b_node,
            self.road_sa, self.road_ae, self.road_sb, self.road_be,
            self.lbl_ae, self.lbl_sb, self.lbl_sa, self.lbl_be,
        )
        self.play(
            content.animate.shift(UP * 0.5),
            # A: further left + slightly down toward center axis
            self.a_lbl.animate.shift(UP * 0.35 + LEFT * 0.35),
            # B: further left + slightly up toward center axis
            self.b_lbl.animate.shift(UP * 0.65 + LEFT * 0.35),
            self._y_shift.animate.set_value(0.5),
            run_time=0.6,
        )

        q = Tex(
            "Each person wants to get there as fast as possible.",
            font_size=32, color=WHITE,
        )
        q.to_edge(DOWN, buff=0.65)
        self.play(Write(q), run_time=1.2)
        self.wait(2.5)

        # Idle with live jitter, then freeze and save for the next scene
        self.wait(3.0)
        for dot in self._s01_cars:
            dot.clear_updaters()
        self._timer.clear_updaters()
        positions = np.array([dot.get_center() for dot in self._s01_cars])
        os.makedirs("media", exist_ok=True)
        np.save("media/s02_car_positions.npy", positions)

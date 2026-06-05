import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

from manim import *
from src.style import apply_style, DIM, FONT
import numpy as np

_S2_START = np.array([-4.5,  0.0, 0])
_S2_END   = np.array([ 4.5,  0.0, 0])
_S2_A     = np.array([ 0.0,  2.5, 0])
_S2_B     = np.array([ 0.0, -2.5, 0])

_D    = np.array([0, 0.5, 0])
S_POS = _S2_START + _D
E_POS = _S2_END   + _D
A_POS = _S2_A     + _D
B_POS = _S2_B     + _D

NODE_R      = 0.22
ROUTE_COLOR = "#666666"

CAR_PALETTE = [
    "#58C4DD", "#3DB8D0", "#72D4E8",
    "#26A8C4", "#89DCF0", "#1E9CB8",
    "#A0E4F8", "#4EC8DC",
]


class BeforeShortcut(Scene):
    def setup(self):
        apply_style(self)

    def construct(self):
        self.add(self._grid())
        self._load_s02_state()
        self._phase_transition()
        self._phase_push_labels()
        self._phase_setup_timers()
        self._phase_reveal_formula()
        self._phase_first_legs()
        self._phase_second_legs()
        self._phase_closing()

    # ── helpers ──────────────────────────────────────────────────────────────

    def _grid(self):
        g = VGroup()
        for x in np.arange(-7, 7.1, 1.5):
            g.add(Line([x, -5, 0], [x, 5, 0], stroke_width=0.7, stroke_color="#1B1B1B"))
        for y in np.arange(-4, 4.1, 1.5):
            g.add(Line([-8, y, 0], [8, y, 0], stroke_width=0.7, stroke_color="#1B1B1B"))
        return g

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
        lbl = Tex(text, font_size=19, color=DIM)
        lbl.move_to(road.point_from_proportion(0.5) + perp_offset)
        return lbl

    def _glow(self, road):
        return Line(
            road.get_start(), road.get_end(),
            stroke_width=10, stroke_color=WHITE,
        ).set_stroke(opacity=0.20)

    def _start_jitter(self, cars, bases, seed):
        amp = 0.035
        rng = np.random.default_rng(seed)
        n   = len(cars)
        fx  = rng.uniform(0.25, 0.70, max(n, 1))
        fy  = rng.uniform(0.25, 0.70, max(n, 1))
        px  = rng.uniform(0, TAU,  max(n, 1))
        py  = rng.uniform(0, TAU,  max(n, 1))
        for i, dot in enumerate(cars):
            b = bases[i].copy()
            def u(d, b=b, fx=fx[i], fy=fy[i], px=px[i], py=py[i]):
                t = self._timer.get_value()
                d.move_to(b + np.array([
                    amp * np.sin(TAU * fx * t + px),
                    amp * np.sin(TAU * fy * t + py),
                    0,
                ]))
            dot.add_updater(u)

    def _stop_jitter(self, cars):
        for dot in cars:
            dot.clear_updaters()

    # ── s02 end-state reconstruction ─────────────────────────────────────────

    def _load_s02_state(self):
        self._timer = ValueTracker(0)
        self._timer.add_updater(lambda m, dt: m.increment_value(dt))
        self.add(self._timer)

        def make_node(pos):
            outer = Circle(radius=NODE_R, stroke_width=2.5, stroke_color=WHITE, fill_opacity=0)
            outer.move_to(pos)
            return VGroup(outer, Dot(pos, radius=0.10, color=WHITE))

        self.s_node = make_node(S_POS)
        self.e_node = make_node(E_POS)
        self.a_node = make_node(A_POS)
        self.b_node = make_node(B_POS)

        self.s_lbl = Tex("Start", font_size=26, color=DIM)
        self.s_lbl.next_to(self.s_node, LEFT, buff=0.3)
        self.e_lbl = Tex("End", font_size=26, color=DIM)
        self.e_lbl.next_to(self.e_node, RIGHT, buff=0.3)

        a_ref = Circle(radius=NODE_R).move_to(_S2_A)
        self.a_lbl = Text("A", font=FONT, font_size=26, color=DIM)
        self.a_lbl.next_to(a_ref, UP, buff=0.3)
        self.a_lbl.shift(UP * 0.35 + LEFT * 0.35)

        b_ref = Circle(radius=NODE_R).move_to(_S2_B)
        self.b_lbl = Text("B", font=FONT, font_size=26, color=DIM)
        self.b_lbl.next_to(b_ref, DOWN, buff=0.3)
        self.b_lbl.shift(UP * 0.65 + LEFT * 0.35)

        self.road_sa = self._road(S_POS, A_POS)
        self.road_ae = self._road(A_POS, E_POS)
        self.road_sb = self._road(S_POS, B_POS)
        self.road_be = self._road(B_POS, E_POS)

        # Fixed-time roads at normal offset
        self.lbl_ae = self._road_label("45 min", self.road_ae, np.array([ 0.30,  0.55, 0]))
        self.lbl_sb = self._road_label("45 min", self.road_sb, np.array([-0.30, -0.55, 0]))
        # Traffic-dependent labels at s02 end positions — pushed outward in _phase_push_labels
        self.lbl_sa = self._road_label(
            r"$t = \mathrm{cars}/100$", self.road_sa, np.array([-0.30,  0.55, 0]))
        self.lbl_be = self._road_label(
            r"$t = \mathrm{cars}/100$", self.road_be, np.array([ 0.30, -0.55, 0]))

        self._s02_closing = Tex(
            "Each person wants to get there as fast as possible.",
            font_size=32, color=WHITE,
        )
        self._s02_closing.to_edge(DOWN, buff=0.65)

        try:
            bases = np.load("media/s02_car_positions.npy")
        except FileNotFoundError:
            bases = np.empty((0, 3))

        self._cars = VGroup(*[
            Dot(bases[i], radius=0.065,
                color=CAR_PALETTE[i % len(CAR_PALETTE)], fill_opacity=0.88)
            for i in range(len(bases))
        ])
        self._bases = bases

        self._start_jitter(list(self._cars), list(bases), seed=42)

        self.add(
            self.s_node, self.e_node, self.a_node, self.b_node,
            self.s_lbl,  self.e_lbl,  self.a_lbl,  self.b_lbl,
            self.road_sa, self.road_ae, self.road_sb, self.road_be,
            self.lbl_ae, self.lbl_sb, self.lbl_sa, self.lbl_be,
            self._s02_closing,
            self._cars,
        )

    def _phase_transition(self):
        self.play(FadeOut(self._s02_closing), run_time=0.8)
        self.wait(0.3)

    def _phase_push_labels(self):
        """Animate formula labels away from the road edges."""
        # delta from s02 offset [-0.30, 0.55] → target [-0.65, 1.0]
        self.play(
            self.lbl_sa.animate.shift(np.array([-0.35,  0.45, 0])),
            self.lbl_be.animate.shift(np.array([ 0.35, -0.45, 0])),
            run_time=0.7,
        )
        self.wait(0.3)

    # ── phases ───────────────────────────────────────────────────────────────

    def _phase_setup_timers(self):
        self._top_val = ValueTracker(0)
        self._bot_val = ValueTracker(0)

        # Top counter — unit tracks DecimalNumber so no overlap as digits grow
        top_prefix = Tex("Top route:", font_size=20, color=DIM)
        self._top_disp = DecimalNumber(0, num_decimal_places=0, color=WHITE, font_size=34)
        self._top_unit = Tex("min", font_size=26, color=DIM)
        top_row = VGroup(top_prefix, self._top_disp, self._top_unit).arrange(RIGHT, buff=0.18)
        top_row.move_to(np.array([0.0, 1.5, 0]))
        self._top_disp.add_updater(lambda m: m.set_value(self._top_val.get_value()))
        self._top_unit.add_updater(lambda m: m.next_to(self._top_disp, RIGHT, buff=0.18))

        # Bottom counter
        bot_prefix = Tex("Bottom route:", font_size=20, color=DIM)
        self._bot_disp = DecimalNumber(0, num_decimal_places=0, color=WHITE, font_size=34)
        self._bot_unit = Tex("min", font_size=26, color=DIM)
        bot_row = VGroup(bot_prefix, self._bot_disp, self._bot_unit).arrange(RIGHT, buff=0.18)
        bot_row.move_to(np.array([0.0, -0.3, 0]))
        self._bot_disp.add_updater(lambda m: m.set_value(self._bot_val.get_value()))
        self._bot_unit.add_updater(lambda m: m.next_to(self._bot_disp, RIGHT, buff=0.18))

        self._top_row = top_row
        self._bot_row = bot_row

        self.play(FadeIn(top_row), FadeIn(bot_row), run_time=0.6)

    def _phase_reveal_formula(self):
        """Write '= 2000/100' next to each traffic label before cars move."""
        self._ext_sa = Tex(r"$= 2000/100$", font_size=19, color=DIM)
        self._ext_sa.next_to(self.lbl_sa, DOWN, buff=0.12)

        self._ext_be = Tex(r"$= 2000/100$", font_size=19, color=DIM)
        self._ext_be.next_to(self.lbl_be, DOWN, buff=0.12)

        self.play(
            LaggedStart(Write(self._ext_sa), Write(self._ext_be), lag_ratio=0.3),
            run_time=1.0,
        )
        self.wait(0.6)

    def _phase_first_legs(self):
        """Top: Start→A (+20 min)  |  Bottom: Start→B (+45 min)."""
        n     = len(self._cars)
        n_top = n // 2
        top_cars = [self._cars[i]         for i in range(n_top)]
        bot_cars = [self._cars[n_top + i] for i in range(n - n_top)]

        self._stop_jitter(list(self._cars))

        glow_sa = self._glow(self.road_sa)
        glow_sb = self._glow(self.road_sb)

        self.play(
            LaggedStart(*[c.animate.move_to(A_POS) for c in top_cars], lag_ratio=0.06),
            LaggedStart(*[c.animate.move_to(B_POS) for c in bot_cars], lag_ratio=0.06),
            Create(glow_sa),
            Create(glow_sb),
            self._top_val.animate.set_value(20),
            self._bot_val.animate.set_value(45),
            run_time=3.0,
        )
        self.play(FadeOut(glow_sa), FadeOut(glow_sb), run_time=0.4)

        a_bases = [A_POS.copy() for _ in top_cars]
        b_bases = [B_POS.copy() for _ in bot_cars]
        self._start_jitter(top_cars, a_bases, seed=13)
        self._start_jitter(bot_cars, b_bases, seed=17)

        self._top_cars = top_cars
        self._bot_cars = bot_cars
        self.wait(0.5)

    def _phase_second_legs(self):
        """Top: A→End (+45 min)  |  Bottom: B→End (+20 min)."""
        self._stop_jitter(self._top_cars + self._bot_cars)

        glow_ae = self._glow(self.road_ae)
        glow_be = self._glow(self.road_be)

        self.play(
            LaggedStart(*[c.animate.move_to(E_POS) for c in self._top_cars], lag_ratio=0.06),
            LaggedStart(*[c.animate.move_to(E_POS) for c in self._bot_cars], lag_ratio=0.06),
            Create(glow_ae),
            Create(glow_be),
            self._top_val.animate.set_value(65),
            self._bot_val.animate.set_value(65),
            run_time=3.0,
        )
        self.play(FadeOut(glow_ae), FadeOut(glow_be), run_time=0.4)

        e_bases = [E_POS.copy() for _ in self._top_cars + self._bot_cars]
        self._start_jitter(self._top_cars + self._bot_cars, e_bases, seed=99)
        self.wait(1.5)

    def _phase_closing(self):
        self._q = Tex(
            r"Before shortcut: everyone takes \textbf{65 minutes}",
            font_size=30, color=WHITE,
        )
        self._q.to_edge(DOWN, buff=0.65)
        self.play(Write(self._q), run_time=1.2)
        self.wait(3.0)

        # Clear all updaters before fade-out
        self._stop_jitter(list(self._cars))
        self._timer.clear_updaters()
        self._top_disp.clear_updaters()
        self._bot_disp.clear_updaters()
        self._top_unit.clear_updaters()
        self._bot_unit.clear_updaters()

        # Fade out formula extensions and un-push the t=cars/100 labels simultaneously
        self.play(
            FadeOut(self._ext_sa), FadeOut(self._ext_be),
            self.lbl_sa.animate.shift(np.array([ 0.35, -0.45, 0])),
            self.lbl_be.animate.shift(np.array([-0.35,  0.45, 0])),
            run_time=0.8,
        )

        # Fade out dots, counters, and closing text — keep graph + edge labels
        self.play(
            FadeOut(self._cars),
            FadeOut(self._top_row), FadeOut(self._bot_row),
            FadeOut(self._q),
            run_time=1.2,
        )
        self.wait(0.5)

        positions = np.array([dot.get_center() for dot in self._cars])
        os.makedirs("media", exist_ok=True)
        np.save("media/s03_car_positions.npy", positions)

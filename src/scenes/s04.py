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

NODE_R         = 0.22
ROUTE_COLOR    = "#666666"
SHORTCUT_COLOR = "#FFD700"
OVERLOAD_COLOR = "#FF4444"

CAR_PALETTE = [
    "#58C4DD", "#3DB8D0", "#72D4E8",
    "#26A8C4", "#89DCF0", "#1E9CB8",
    "#A0E4F8", "#4EC8DC",
]


class CityAddsShortcut(Scene):
    def setup(self):
        apply_style(self)

    def construct(self):
        self.add(self._grid())
        self._load_s03_state()
        self._phase_shortcut()
        self._phase_solo_driver()
        self._phase_everyone()
        self._phase_cleanup()

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

    def _glow_line(self, road, color=WHITE, width=12, opacity=0.22):
        return Line(
            road.get_start(), road.get_end(),
            stroke_width=width, stroke_color=color,
        ).set_stroke(opacity=opacity)

    # ── s03 end-state reconstruction ─────────────────────────────────────────
    # s03 _phase_closing: fades out cars, timer rows, closing text, ext formulas,
    # and un-shifts lbl_sa/lbl_be back to their original s02 offsets.
    # Result: clean graph only, no overlays.

    def _load_s03_state(self):
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

        # Labels at original (un-pushed) offsets — matches s03 end state
        self.lbl_ae = self._road_label("45 min",   self.road_ae, np.array([ 0.30,  0.55, 0]))
        self.lbl_sb = self._road_label("45 min",   self.road_sb, np.array([-0.30, -0.55, 0]))
        self.lbl_sa = self._road_label(
            r"$t = \mathrm{cars}/100$", self.road_sa, np.array([-0.30,  0.55, 0]))
        self.lbl_be = self._road_label(
            r"$t = \mathrm{cars}/100$", self.road_be, np.array([ 0.30, -0.55, 0]))

        self.add(
            self.s_node, self.e_node, self.a_node, self.b_node,
            self.s_lbl, self.e_lbl, self.a_lbl, self.b_lbl,
            self.road_sa, self.road_ae, self.road_sb, self.road_be,
            self.lbl_ae, self.lbl_sb, self.lbl_sa, self.lbl_be,
        )

    # ── phases ───────────────────────────────────────────────────────────────

    def _phase_shortcut(self):
        """Build the A→B shortcut with a brief caption."""
        vo = Tex("The city adds a new road.", font_size=30, color=WHITE)
        vo.to_edge(DOWN, buff=0.65)
        self.play(FadeIn(vo), run_time=0.5)
        self.wait(0.7)

        self.road_ab = Arrow(
            A_POS, B_POS,
            buff=NODE_R + 0.06,
            stroke_width=3.5,
            color=SHORTCUT_COLOR,
            tip_length=0.22,
            max_stroke_width_to_length_ratio=999,
        )

        ab_glow_outer = Line(
            self.road_ab.get_start(), self.road_ab.get_end(),
            stroke_width=28, stroke_color=SHORTCUT_COLOR,
        ).set_stroke(opacity=0.10)

        self._ab_glow = Line(
            self.road_ab.get_start(), self.road_ab.get_end(),
            stroke_width=12, stroke_color=SHORTCUT_COLOR,
        ).set_stroke(opacity=0.22)

        ab_mid = self.road_ab.point_from_proportion(0.5)
        lbl_zero = Tex(r"\textbf{0 min}", font_size=22, color=SHORTCUT_COLOR)
        lbl_sc   = Tex("shortcut", font_size=17, color=DIM)
        self.lbl_ab = VGroup(lbl_zero, lbl_sc).arrange(DOWN, buff=0.06)
        self.lbl_ab.move_to(ab_mid + np.array([0.75, 0, 0]))

        self.play(FadeIn(ab_glow_outer), GrowArrow(self.road_ab), run_time=1.3)
        self.play(
            FadeIn(self._ab_glow),
            ab_glow_outer.animate.set_stroke(opacity=0.04),
            FadeIn(self.lbl_ab),
            run_time=0.6,
        )
        self.play(FadeOut(vo), run_time=0.5)
        self.wait(0.5)

    def _phase_solo_driver(self):
        """One driver at Start rationally picks S → A → B → E.
        Emphasis is purely on the cost labels: cars/100 beats fixed 45."""
        solo = Dot(S_POS, radius=0.11, color=WHITE, fill_opacity=1.0)
        self.play(FadeIn(solo, scale=1.6), run_time=0.5)
        self.wait(0.5)

        # ── Choice 1: cars/100 (SA) beats fixed 45 min (SB) ───────────────
        self.play(
            self.lbl_sa.animate.set_color(WHITE),
            self.lbl_sb.animate.set_opacity(0.22),
            run_time=0.5,
        )
        self.wait(2.0)

        self.play(
            self.lbl_sa.animate.set_color(DIM),
            self.lbl_sb.animate.set_opacity(1.0),
            solo.animate.move_to(A_POS),
            run_time=1.2,
        )
        self.wait(0.5)

        # ── Choice 2: 0 + cars/100 (A→B→E) beats fixed 45 min (AE) ───────
        self.play(
            self.lbl_be.animate.set_color(WHITE),
            self.lbl_ae.animate.set_opacity(0.22),
            run_time=0.5,
        )
        self.wait(2.0)

        self.play(
            self.lbl_be.animate.set_color(DIM),
            self.lbl_ae.animate.set_opacity(1.0),
            solo.animate.move_to(B_POS),
            run_time=1.0,
        )
        self.play(solo.animate.move_to(E_POS), run_time=0.9)
        self.wait(0.8)
        self._solo = solo

    def _phase_everyone(self):
        """All drivers follow the same path — SA and BE turn red."""
        rng = np.random.default_rng(55)
        n = 40
        offsets = rng.uniform(low=[-0.35, -0.25, 0], high=[0.35, 0.25, 0], size=(n, 3))
        offsets[:, 2] = 0

        cars = VGroup(*[
            Dot(S_POS + offsets[i], radius=0.065,
                color=CAR_PALETTE[i % len(CAR_PALETTE)], fill_opacity=0.88)
            for i in range(n)
        ])

        self.play(
            FadeOut(self._solo),
            FadeIn(cars, lag_ratio=0.02),
            run_time=0.7,
        )
        self.wait(0.3)

        # All flow S→A — SA road turns red from overload
        self.play(
            LaggedStart(*[c.animate.move_to(A_POS) for c in cars], lag_ratio=0.04),
            self.road_sa.animate.set_color(OVERLOAD_COLOR),
            run_time=2.5,
        )
        self.wait(0.2)

        # All flow A→B via shortcut — shortcut glows brighter
        self.play(
            LaggedStart(*[c.animate.move_to(B_POS) for c in cars], lag_ratio=0.04),
            self._ab_glow.animate.set_stroke(opacity=0.45),
            run_time=1.5,
        )
        self.wait(0.2)

        # All flow B→E — BE road turns red, both red roads glow
        red_glow_sa = self._glow_line(self.road_sa, color=OVERLOAD_COLOR, width=18, opacity=0.25)
        red_glow_be = self._glow_line(self.road_be, color=OVERLOAD_COLOR, width=18, opacity=0.25)
        self.play(
            LaggedStart(*[c.animate.move_to(E_POS) for c in cars], lag_ratio=0.04),
            self.road_be.animate.set_color(OVERLOAD_COLOR),
            FadeIn(red_glow_sa),
            FadeIn(red_glow_be),
            run_time=2.0,
        )
        self.wait(3.5)

        self._red_glow_sa = red_glow_sa
        self._red_glow_be = red_glow_be
        self._crowd = cars

    def _phase_cleanup(self):
        """Restore graph to clean state — no red roads, no glows, no cars."""
        self.play(
            FadeOut(self._red_glow_sa),
            FadeOut(self._red_glow_be),
            FadeOut(self._crowd),
            self.road_sa.animate.set_color(ROUTE_COLOR),
            self.road_be.animate.set_color(ROUTE_COLOR),
            self._ab_glow.animate.set_stroke(opacity=0.22),
            run_time=1.2,
        )
        self.wait(0.5)

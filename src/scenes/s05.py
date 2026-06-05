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
ACCENT         = "#58C4DD"


class TheParadox(Scene):
    def setup(self):
        apply_style(self)

    def construct(self):
        self.add(self._grid())
        self._load_s04_state()
        self._phase_calc()
        self._phase_comparison()
        self._phase_closing()

    # ── helpers ──────────────────────────────────────────────────────────────

    def _grid(self):
        g = VGroup()
        for x in np.arange(-7, 7.1, 1.5):
            g.add(Line([x, -5, 0], [x, 5, 0], stroke_width=0.7, stroke_color="#1B1B1B"))
        for y in np.arange(-4, 4.1, 1.5):
            g.add(Line([-8, y, 0], [8, y, 0], stroke_width=0.7, stroke_color="#1B1B1B"))
        return g

    def _road(self, p1, p2, color=ROUTE_COLOR, width=3):
        return Arrow(
            p1, p2,
            buff=NODE_R + 0.06,
            stroke_width=width,
            color=color,
            tip_length=0.22,
            max_stroke_width_to_length_ratio=999,
        )

    def _road_label(self, text, road, perp_offset, color=DIM, size=19):
        lbl = Tex(text, font_size=size, color=color)
        lbl.move_to(road.point_from_proportion(0.5) + perp_offset)
        return lbl

    def _glow_line(self, road, color=WHITE, width=12, opacity=0.22):
        return Line(
            road.get_start(), road.get_end(),
            stroke_width=width, stroke_color=color,
        ).set_stroke(opacity=opacity)

    # ── s04 end-state reconstruction ─────────────────────────────────────────

    def _load_s04_state(self):
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

        self.lbl_ae = self._road_label("45 min",   self.road_ae, np.array([ 0.30,  0.55, 0]))
        self.lbl_sb = self._road_label("45 min",   self.road_sb, np.array([-0.30, -0.55, 0]))
        self.lbl_sa = self._road_label(
            r"$t = \mathrm{cars}/100$", self.road_sa, np.array([-0.30,  0.55, 0]))
        self.lbl_be = self._road_label(
            r"$t = \mathrm{cars}/100$", self.road_be, np.array([ 0.30, -0.55, 0]))

        # A→B shortcut (s04 added this)
        self.road_ab = self._road(A_POS, B_POS, color=SHORTCUT_COLOR, width=3.5)
        self._ab_glow = self._glow_line(self.road_ab, color=SHORTCUT_COLOR, width=12, opacity=0.22)

        ab_mid = self.road_ab.point_from_proportion(0.5)
        lbl_zero = Tex(r"\textbf{0 min}", font_size=22, color=SHORTCUT_COLOR)
        lbl_sc   = Tex("shortcut", font_size=17, color=DIM)
        self.lbl_ab = VGroup(lbl_zero, lbl_sc).arrange(DOWN, buff=0.06)
        self.lbl_ab.move_to(ab_mid + np.array([0.75, 0, 0]))

        self.add(
            self.s_node, self.e_node, self.a_node, self.b_node,
            self.s_lbl, self.e_lbl, self.a_lbl, self.b_lbl,
            self.road_sa, self.road_ae, self.road_sb, self.road_be,
            self.lbl_ae, self.lbl_sb, self.lbl_sa, self.lbl_be,
            self._ab_glow, self.road_ab, self.lbl_ab,
        )

    # ── phases ───────────────────────────────────────────────────────────────

    def _phase_calc(self):
        """Step through Start→A→B→End cost, then show total."""

        # Dim non-active roads first
        self.play(
            self.road_ae.animate.set_opacity(0.18),
            self.road_sb.animate.set_opacity(0.18),
            self.lbl_ae.animate.set_opacity(0.18),
            self.lbl_sb.animate.set_opacity(0.18),
            run_time=0.6,
        )

        # ── Start → A : 40 min ───────────────────────────────────────────
        glow_sa = self._glow_line(self.road_sa, color=WHITE, width=14, opacity=0.28)
        lbl_sa_new = Tex(r"\textbf{40 min}", font_size=22, color=WHITE)
        lbl_sa_new.move_to(self.lbl_sa.get_center())

        self.play(FadeIn(glow_sa), run_time=0.4)
        self.play(
            ReplacementTransform(self.lbl_sa, lbl_sa_new),
            run_time=0.5,
        )
        self.lbl_sa = lbl_sa_new
        self.wait(1.4)

        # ── A → B : 0 min (already labeled) ─────────────────────────────
        glow_ab = self._glow_line(self.road_ab, color=SHORTCUT_COLOR, width=16, opacity=0.38)
        self.play(FadeIn(glow_ab), run_time=0.4)
        self.wait(1.2)

        # ── B → End : 40 min ─────────────────────────────────────────────
        glow_be = self._glow_line(self.road_be, color=WHITE, width=14, opacity=0.28)
        lbl_be_new = Tex(r"\textbf{40 min}", font_size=22, color=WHITE)
        lbl_be_new.move_to(self.lbl_be.get_center())

        self.play(FadeIn(glow_be), run_time=0.4)
        self.play(
            ReplacementTransform(self.lbl_be, lbl_be_new),
            run_time=0.5,
        )
        self.lbl_be = lbl_be_new
        self.wait(1.4)

        # ── Total: 80 min ─────────────────────────────────────────────────
        total = Tex(r"\textbf{80 minutes}", font_size=52, color=WHITE)
        total.to_edge(DOWN, buff=0.9)
        self.play(Write(total), run_time=0.9)
        self.wait(2.5)

        # Clean up glows before comparison
        self.play(
            FadeOut(glow_sa), FadeOut(glow_ab), FadeOut(glow_be),
            run_time=0.5,
        )
        self._total_lbl = total

    def _phase_comparison(self):
        """Before 65 min → After 80 min side-by-side."""

        # Restore dimmed roads
        self.play(
            self.road_ae.animate.set_opacity(1.0),
            self.road_sb.animate.set_opacity(1.0),
            self.lbl_ae.animate.set_opacity(1.0),
            self.lbl_sb.animate.set_opacity(1.0),
            FadeOut(self._total_lbl),
            run_time=0.7,
        )

        before_lbl = Tex(r"Before: \textbf{65 min}", font_size=36, color=DIM)
        after_lbl  = Tex(r"After: \textbf{80 min}",  font_size=36, color=WHITE)
        comparison = VGroup(before_lbl, after_lbl).arrange(RIGHT, buff=1.2)
        comparison.to_edge(DOWN, buff=0.85)

        self.play(FadeIn(before_lbl), run_time=0.6)
        self.wait(0.4)
        self.play(FadeIn(after_lbl), run_time=0.6)
        self.wait(2.8)

        self._comparison = comparison

    def _phase_closing(self):
        """Replace comparison with the paradox statement."""
        closing = VGroup(
            Tex(r"Before: \textbf{65 min}", font_size=30, color=DIM),
            Tex(r"After adding shortcut: \textbf{80 min}", font_size=30, color=WHITE),
        ).arrange(DOWN, buff=0.3)
        closing.to_edge(DOWN, buff=0.75)

        self.play(
            ReplacementTransform(self._comparison, closing),
            run_time=0.7,
        )
        self.wait(1.2)

        paradox = Tex(
            r"\textit{The shortcut made the system worse.}",
            font_size=34, color=ACCENT,
        )
        paradox.next_to(closing, UP, buff=0.5)
        self.play(Write(paradox), run_time=1.0)
        self.wait(4.0)

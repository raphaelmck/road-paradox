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
        self._phase_transition()
        self._phase_build_shortcut()
        self._phase_voiceover()
        self._phase_closing_text()

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

    # ── s03 end-state reconstruction ─────────────────────────────────────────

    def _load_s03_state(self):
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

        self.lbl_ae = self._road_label("45 min", self.road_ae, np.array([ 0.30,  0.55, 0]))
        self.lbl_sb = self._road_label("45 min", self.road_sb, np.array([-0.30, -0.55, 0]))
        self.lbl_sa = self._road_label(
            r"$t = \mathrm{cars}/100$", self.road_sa, np.array([-0.65, 1.0, 0]))
        self.lbl_be = self._road_label(
            r"$t = \mathrm{cars}/100$", self.road_be, np.array([ 0.65,-1.0, 0]))

        ext_sa = Tex(r"$= 2000/100$", font_size=19, color=DIM)
        ext_sa.next_to(self.lbl_sa, DOWN, buff=0.12)
        ext_be = Tex(r"$= 2000/100$", font_size=19, color=DIM)
        ext_be.next_to(self.lbl_be, DOWN, buff=0.12)

        top_prefix = Tex("Top route:", font_size=20, color=DIM)
        top_disp   = DecimalNumber(65, num_decimal_places=0, color=WHITE, font_size=34)
        top_unit   = Tex("min", font_size=26, color=DIM)
        self._top_row = VGroup(top_prefix, top_disp, top_unit).arrange(RIGHT, buff=0.14)
        self._top_row.move_to(np.array([0.0, 1.5, 0]))

        bot_prefix = Tex("Bottom route:", font_size=20, color=DIM)
        bot_disp   = DecimalNumber(65, num_decimal_places=0, color=WHITE, font_size=34)
        bot_unit   = Tex("min", font_size=26, color=DIM)
        self._bot_row = VGroup(bot_prefix, bot_disp, bot_unit).arrange(RIGHT, buff=0.14)
        self._bot_row.move_to(np.array([0.0, -0.3, 0]))

        self._s03_closing = Tex(
            r"Before shortcut: everyone takes \textbf{65 minutes}",
            font_size=30, color=WHITE,
        )
        self._s03_closing.to_edge(DOWN, buff=0.65)

        try:
            bases = np.load("media/s03_car_positions.npy")
        except FileNotFoundError:
            bases = np.empty((0, 3))

        self._cars = VGroup(*[
            Dot(bases[i], radius=0.065,
                color=CAR_PALETTE[i % len(CAR_PALETTE)], fill_opacity=0.88)
            for i in range(len(bases))
        ])

        e_bases = [E_POS.copy() for _ in range(len(bases))]
        self._start_jitter(list(self._cars), e_bases, seed=99)

        self.add(
            self.s_node, self.e_node, self.a_node, self.b_node,
            self.s_lbl, self.e_lbl, self.a_lbl, self.b_lbl,
            self.road_sa, self.road_ae, self.road_sb, self.road_be,
            self.lbl_ae, self.lbl_sb, self.lbl_sa, self.lbl_be,
            ext_sa, ext_be,
            self._top_row, self._bot_row,
            self._s03_closing,
            self._cars,
        )

    def _phase_transition(self):
        self.play(
            FadeOut(self._s03_closing),
            FadeOut(self._top_row),
            FadeOut(self._bot_row),
            run_time=0.8,
        )
        self.wait(0.3)

    # ── phases ───────────────────────────────────────────────────────────────

    def _phase_build_shortcut(self):
        vo = Tex("Now the city builds a new road.", font_size=30, color=WHITE)
        vo.to_edge(DOWN, buff=0.65)
        self.play(FadeIn(vo), run_time=0.6)
        self.wait(1.2)

        vo2 = Tex("A beautiful shortcut from A to B.", font_size=30, color=WHITE)
        vo2.to_edge(DOWN, buff=0.65)
        self.play(ReplacementTransform(vo, vo2), run_time=0.45)
        self.wait(0.4)

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

        ab_glow_inner = Line(
            self.road_ab.get_start(), self.road_ab.get_end(),
            stroke_width=12, stroke_color=SHORTCUT_COLOR,
        ).set_stroke(opacity=0.22)

        ab_mid = self.road_ab.point_from_proportion(0.5)
        lbl_zero = Tex(r"\textbf{0 min}", font_size=22, color=SHORTCUT_COLOR)
        lbl_sc   = Tex("shortcut", font_size=17, color=DIM)
        self.lbl_ab = VGroup(lbl_zero, lbl_sc).arrange(DOWN, buff=0.06)
        self.lbl_ab.move_to(ab_mid + np.array([0.75, 0, 0]))

        self.play(
            FadeIn(ab_glow_outer),
            GrowArrow(self.road_ab),
            run_time=1.4,
        )
        self.play(
            FadeIn(ab_glow_inner),
            ab_glow_outer.animate.set_stroke(opacity=0.04),
            FadeIn(self.lbl_ab),
            run_time=0.7,
        )
        self.wait(0.9)
        self._vo_current = vo2

    def _phase_voiceover(self):
        lines = [
            r"And to make the effect as dramatic as possible,",
            r"let's say this shortcut is basically instant.",
            r"Zero minutes.",
            r"Surely this can only help.",
            r"After all, nobody is being forced to use it.",
            r"It just gives drivers one more option.",
            r"More options should make things better.",
        ]
        pauses = [1.6, 2.0, 2.2, 2.0, 2.2, 2.0, 2.5]

        cur = self._vo_current
        for line, pause in zip(lines, pauses):
            nxt = Tex(line, font_size=30, color=WHITE)
            nxt.to_edge(DOWN, buff=0.65)
            self.play(ReplacementTransform(cur, nxt), run_time=0.45)
            self.wait(pause)
            cur = nxt
        self._vo_current = cur

    def _phase_closing_text(self):
        self.play(FadeOut(self._vo_current), run_time=0.5)
        self.wait(0.4)

        txt1 = Tex(r"\textbf{A new option appears.}", font_size=42, color=WHITE)
        txt1.to_edge(DOWN, buff=0.65)
        self.play(Write(txt1), run_time=1.0)
        self.wait(2.8)

        txt2 = Tex(r"\textbf{So what do drivers do?}", font_size=42, color=WHITE)
        txt2.to_edge(DOWN, buff=0.65)
        self.play(ReplacementTransform(txt1, txt2), run_time=0.8)
        self.wait(3.0)

        self._stop_jitter(list(self._cars))
        self._timer.clear_updaters()
        positions = np.array([dot.get_center() for dot in self._cars])
        os.makedirs("media", exist_ok=True)
        np.save("media/s04_car_positions.npy", positions)

from manim import *
from custom_voiceover_scene import CustomVoiceoverScene
from manim_voiceover.services.gtts import GTTSService

class ACCurrentExplanation(CustomVoiceoverScene):
    def construct(self):
        gtts_service = GTTSService(lang="en", tld="com")
        self.set_speech_service(gtts_service)

        # Introduction
        with self.voiceover(text="In this video, we will explain the concept of alternating current, also known as AC.") as tracker:
            title = Text("Alternating Current (AC)", font_size=36)
            self.play(Write(title), run_time=tracker.duration / 2)
            self.wait(tracker.duration / 2)
            self.play(FadeOut(title))

        self.clear()

        # Problem Statement
        with self.voiceover(text="AC current, or alternating current, is the type of current used in most household and commercial power supplies.") as tracker:
            statement = Text("What is Alternating Current?", font_size=24)
            self.play(Write(statement), run_time=tracker.duration / 2)
            self.wait(tracker.duration / 2)
            self.play(FadeOut(statement))

        self.clear()

        # Visualization
        with self.voiceover(text="Alternating current continuously changes its direction, flowing back and forth in a circuit.") as tracker:
            ac_wave = MathTex(r"I(t) = I_0 \\sin(\\omega t)", font_size=24)
            axis = Axes(x_range=[0, 2*PI, PI/2], y_range=[-1, 1, 0.5],
                        x_length=8, y_length=4, tips=False)
            sin_wave = axis.plot(lambda x: np.sin(x), x_range=[0, 2*PI], color=BLUE)
            ac_label = Text("AC Current Waveform", font_size=24).next_to(axis, UP)
            self.play(Create(axis), run_time=tracker.duration * 0.3)
            self.play(Write(ac_wave), run_time=tracker.duration * 0.3)
            self.play(Create(sin_wave), run_time=tracker.duration * 0.4)
            self.play(Write(ac_label))

        self.wait(2)
        self.clear()

        # Explanation
        with self.voiceover(text="Unlike direct current, or DC, where current flows in one direction, AC reverses direction periodically. This allows it to be easily transmitted over long distances.") as tracker:
            dc_vs_ac = Text("AC vs. DC Current", font_size=24).to_edge(UP)
            dc_arrow = Arrow(LEFT, RIGHT, color=RED).shift(DOWN * 0.5)
            ac_arrow = DoubleArrow(LEFT, RIGHT, color=BLUE).shift(UP * 0.5)
            dc_label = Text("Direct Current (DC)", font_size=24, color=RED).next_to(dc_arrow, DOWN)
            ac_label = Text("Alternating Current (AC)", font_size=24, color=BLUE).next_to(ac_arrow, UP)
            self.play(Write(dc_vs_ac), run_time=tracker.duration * 0.2)
            self.play(GrowArrow(dc_arrow), run_time=tracker.duration * 0.3)
            self.play(Write(dc_label), run_time=tracker.duration * 0.2)
            self.play(GrowArrow(ac_arrow), run_time=tracker.duration * 0.3)
            self.play(Write(ac_label), run_time=tracker.duration * 0.2)

        self.wait(2)
        self.clear()

        # Conclusion
        with self.voiceover(text="In conclusion, AC current is used widely because of its efficiency in transmitting energy over long distances and its compatibility with transformers to adjust voltage levels.") as tracker:
            conclusion = Text("Key Takeaways", font_size=24).to_edge(UP)
            point1 = Text("Efficient for long-distance transmission", font_size=24).next_to(conclusion, DOWN, buff=0.3)
            point2 = Text("Easily converted to different voltages", font_size=24).next_to(point1, DOWN, buff=0.3)
            self.play(Write(conclusion), run_time=tracker.duration * 0.2)
            self.play(Write(point1), run_time=tracker.duration * 0.4)
            self.play(Write(point2), run_time=tracker.duration * 0.4)

        self.wait(2)

if __name__ == "__main__":
    scene = ACCurrentExplanation()
    scene.render()

from manim import *
from manim_voiceover import VoiceoverScene
from manim_voiceover.services.gtts import GTTSService
from manim_voiceover.services.pyttsx3 import TTSService

class IntroductionToCalculus(VoiceoverScene):
    def construct(self):
        # Set up the scene with 16:9 aspect ratio
        self.camera.frame_width = 16
        self.camera.frame_height = 9
        
        # Configure voiceover service with fallback option
        try:
            # Try to use Google TTS first
            self.set_speech_service(GTTSService())
        except:
            # Fallback to offline TTS if Google TTS fails
            self.set_speech_service(TTSService())
        
        # Title
        title = Text("Introduction to Calculus", font="Sans", color=BLUE)
        title.scale(1.5)
        
        # Introduction
        with self.voiceover("Welcome to this introduction to calculus. Today, we'll explore the fundamental concepts that make calculus so powerful.") as tracker:
            self.play(Write(title))
            
        # Clear the screen for the main content
        self.play(FadeOut(title))
        
        # Section 1: What is Calculus?
        section_title = Text("What is Calculus?", font="Sans", color=YELLOW)
        section_title.to_edge(UP)
        
        with self.voiceover("What exactly is calculus? At its core, calculus is the mathematics of change.") as tracker:
            self.play(Write(section_title))
        
        # Create a simple graph to illustrate change
        axes = Axes(
            x_range=[-3, 3, 1],
            y_range=[-2, 8, 2],
            axis_config={"color": WHITE},
        )
        
        # Parabola function
        graph = axes.plot(lambda x: x**2, color=RED)
        graph_label = Text("f(x) = x²", font="Sans", color=RED).next_to(graph, UP).scale(0.8)
        
        with self.voiceover("It allows us to analyze how quantities change over time or space. For example, consider this parabola.") as tracker:
            self.play(Create(axes), run_time=1)
            self.play(Create(graph), Write(graph_label), run_time=2)
        
        # Section 2: Derivatives
        derivative_title = Text("Derivatives: The Rate of Change", font="Sans", color=GREEN)
        derivative_title.to_edge(UP)
        
        with self.voiceover("One of the key concepts in calculus is the derivative, which measures the rate of change of a function.") as tracker:
            self.play(FadeOut(section_title))
            self.play(Write(derivative_title))
        
        # Tangent line to illustrate derivative
        point = Dot(axes.coords_to_point(1, 1), color=YELLOW)
        tangent_line = axes.get_secant_slope_group(
            x=1, graph=graph, dx=0.01, secant_line_color=GREEN, secant_line_length=4
        )
        
        with self.voiceover("The derivative at a point gives us the slope of the tangent line at that point. For our parabola, at x equals 1, the derivative is 2.") as tracker:
            self.play(Create(point))
            self.play(Create(tangent_line))
        
        # Derivative formula
        derivative_formula = MathTex(
            "\\frac{d}{dx}(x^2) = 2x", 
            color=GREEN
        ).scale(1.2)
        derivative_formula.to_edge(DOWN, buff=1.5)
        
        with self.voiceover("The derivative of x squared is two x. This means that the rate of change of our function depends on the x value.") as tracker:
            self.play(Write(derivative_formula))
        
        # Section 3: Integrals
        self.play(
            FadeOut(derivative_title),
            FadeOut(derivative_formula),
            FadeOut(tangent_line),
            FadeOut(point)
        )
        
        integral_title = Text("Integrals: The Area Under the Curve", font="Sans", color=CYAN)
        integral_title.to_edge(UP)
        
        with self.voiceover("The other fundamental concept in calculus is the integral, which gives us the area under a curve.") as tracker:
            self.play(Write(integral_title))
        
        # Area under the curve
        area = axes.get_area(graph, x_range=[0, 2], color=CYAN, opacity=0.5)
        
        with self.voiceover("For our parabola, we can find the area under the curve from zero to two.") as tracker:
            self.play(Create(area))
        
        # Integral formula
        integral_formula = MathTex(
            "\\int_{0}^{2} x^2 dx = \\left[ \\frac{x^3}{3} \\right]_{0}^{2} = \\frac{8}{3}",
            color=CYAN
        ).scale(1.2)
        integral_formula.to_edge(DOWN, buff=1.5)
        
        with self.voiceover("The integral of x squared from zero to two equals eight thirds. This represents the exact area under our parabola in that interval.") as tracker:
            self.play(Write(integral_formula))
        
        # Conclusion
        self.play(
            FadeOut(integral_title),
            FadeOut(integral_formula),
            FadeOut(area),
            FadeOut(graph),
            FadeOut(graph_label),
            FadeOut(axes)
        )
        
        conclusion = Text("Calculus: The Mathematics of Change", font="Sans", color=BLUE)
        conclusion.scale(1.2)
        
        bullet1 = Text("• Derivatives measure rates of change", font="Sans", color=GREEN).scale(0.8)
        bullet2 = Text("• Integrals calculate accumulated change", font="Sans", color=CYAN).scale(0.8)
        
        bullet1.next_to(conclusion, DOWN, buff=0.8).align_to(conclusion, LEFT).shift(RIGHT)
        bullet2.next_to(bullet1, DOWN, buff=0.5).align_to(bullet1, LEFT)
        
        with self.voiceover("In conclusion, calculus gives us powerful tools to understand how things change. Derivatives help us analyze rates of change, while integrals allow us to calculate accumulated change.") as tracker:
            self.play(Write(conclusion))
            self.play(Write(bullet1))
            self.play(Write(bullet2))
        
        with self.voiceover("Thank you for watching this introduction to calculus. In future lessons, we'll explore these concepts in greater depth.") as tracker:
            self.wait(2)
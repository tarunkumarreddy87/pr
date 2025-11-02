from manim import *
from manim_voiceover.voiceover import VoiceoverScene
from manim_voiceover.services.gtts import gTTSVoiceoverService

class ComputerParts(VoiceoverScene):
    def construct(self):
        self.set_speech_service(gTTSVoiceoverService())

        # --- Constants and Styling ---
        section_title_font_size = 38
        component_label_font_size = 28
        connection_color = YELLOW
        label_color = WHITE
        arrow_color = RED_E
        
        # --- Title ---
        title = Text("Parts of a Computer", font_size=50).to_edge(UP)
        with self.voiceover(text="Let's explore the essential components that make up a computer.") as tracker:
            self.play(Create(title), run_time=tracker.duration)
        self.wait(0.5)

        # --- Motherboard (Central Hub) ---
        motherboard_rect = Rectangle(width=6, height=4, color=GRAY_B, fill_opacity=0.2, stroke_width=2)
        motherboard_label = Text("Motherboard", font_size=component_label_font_size, color=label_color)
        motherboard_group = VGroup(motherboard_rect, motherboard_label).arrange(DOWN, buff=0.2)
        motherboard_group.move_to(ORIGIN + DOWN * 0.5) 
        
        with self.voiceover(text="At the heart of every computer is the Motherboard, acting as the main circuit board connecting all internal parts.") as tracker:
            self.play(FadeIn(motherboard_rect), run_time=tracker.duration * 0.5)
            self.play(Write(motherboard_label), run_time=tracker.duration * 0.5)
        self.wait(1)

        # --- CPU (Central Processing Unit) ---
        cpu_rect = Rectangle(width=1.0, height=1.0, color=ORANGE, fill_opacity=0.8).next_to(motherboard_rect, UP, buff=0.3).shift(LEFT*0.7)
        cpu_label = Text("CPU (Processor)", font_size=component_label_font_size, color=label_color).next_to(cpu_rect, UP, buff=0.3)
        cpu_connection = Arrow(cpu_rect.get_bottom(), motherboard_rect.get_top() + LEFT*0.7, buff=0.1, color=connection_color, stroke_width=2)
        
        with self.voiceover(text="The CPU, or Central Processing Unit, is the 'brain' of the computer, executing most instructions and calculations.") as tracker:
            self.play(FadeIn(cpu_rect), Write(cpu_label), run_time=tracker.duration * 0.6)
            self.play(Create(cpu_connection), run_time=tracker.duration * 0.4)
        self.wait(0.5)

        # --- RAM (Random Access Memory) ---
        ram_rect1 = Rectangle(width=0.4, height=1.5, color=GREEN_B, fill_opacity=0.8).next_to(cpu_rect, RIGHT, buff=0.8)
        ram_rect2 = Rectangle(width=0.4, height=1.5, color=GREEN_B, fill_opacity=0.8).next_to(ram_rect1, RIGHT, buff=0.2)
        ram_group_rects = VGroup(ram_rect1, ram_rect2)
        ram_label = Text("RAM (Memory)", font_size=component_label_font_size, color=label_color).next_to(ram_group_rects, UP, buff=0.3)
        ram_connection = Arrow(ram_group_rects.get_bottom(), motherboard_rect.get_top() + RIGHT*1.5, buff=0.1, color=connection_color, stroke_width=2)
        
        with self.voiceover(text="RAM, or Random Access Memory, stores data the CPU needs quickly for active tasks, but it's volatile.") as tracker:
            self.play(FadeIn(ram_group_rects), Write(ram_label), run_time=tracker.duration * 0.6)
            self.play(Create(ram_connection), run_time=tracker.duration * 0.4)
        self.wait(0.5)

        # --- GPU (Graphics Processing Unit) ---
        gpu_rect = Rectangle(width=2.5, height=0.8, color=PURPLE_B, fill_opacity=0.8).next_to(motherboard_rect, DOWN, buff=0.5).shift(RIGHT*0.5)
        gpu_label = Text("GPU (Graphics Card)", font_size=component_label_font_size, color=label_color).next_to(gpu_rect, DOWN, buff=0.3)
        gpu_connection = Arrow(gpu_rect.get_top(), motherboard_rect.get_bottom() + RIGHT*0.5, buff=0.1, color=connection_color, stroke_width=2)
        
        with self.voiceover(text="The GPU, or Graphics Processing Unit, is vital for rendering images and videos, especially for gaming and design.") as tracker:
            self.play(FadeIn(gpu_rect), Write(gpu_label), run_time=tracker.duration * 0.6)
            self.play(Create(gpu_connection), run_time=tracker.duration * 0.4)
        self.wait(0.5)

        # --- Storage (SSD/HDD) ---
        storage_rect = Rectangle(width=1.5, height=1.0, color=TEAL_B, fill_opacity=0.8).next_to(motherboard_rect, LEFT, buff=0.8).shift(UP*0.5)
        storage_label = Text("Storage (SSD/HDD)", font_size=component_label_font_size, color=label_color).next_to(storage_rect, UP, buff=0.3)
        storage_connection = Arrow(storage_rect.get_right(), motherboard_rect.get_left() + UP*0.5, buff=0.1, color=connection_color, stroke_width=2)
        
        with self.voiceover(text="For long-term data storage, we use SSDs or HDDs, where your operating system, programs, and files are permanently saved.") as tracker:
            self.play(FadeIn(storage_rect), Write(storage_label), run_time=tracker.duration * 0.6)
            self.play(Create(storage_connection), run_time=tracker.duration * 0.4)
        self.wait(0.5)

        # --- Power Supply (PSU) ---
        psu_rect = Rectangle(width=2.0, height=1.2, color=YELLOW_B, fill_opacity=0.8).next_to(motherboard_rect, RIGHT, buff=2.0).shift(DOWN*0.5)
        psu_label = Text("Power Supply (PSU)", font_size=component_label_font_size, color=label_color).next_to(psu_rect, UP, buff=0.3)
        psu_connection_arrow = Arrow(psu_rect.get_left(), motherboard_rect.get_right() + DOWN*0.5, buff=0.1, color=connection_color, stroke_width=2)
        
        with self.voiceover(text="The Power Supply Unit, or PSU, converts wall current into usable electricity for all components.") as tracker:
            self.play(FadeIn(psu_rect), Write(psu_label), run_time=tracker.duration * 0.6)
            self.play(Create(psu_connection_arrow), run_time=tracker.duration * 0.4)
        self.wait(0.5)

        # --- Data Flow Indicators ---
        data_flow_cpu_ram = Arrow(cpu_rect.get_right(), ram_group_rects.get_left(), buff=0.1, color=arrow_color, stroke_width=3)
        data_flow_ram_cpu = Arrow(ram_group_rects.get_left(), cpu_rect.get_right(), buff=0.1, color=arrow_color, stroke_width=3)
        data_flow_label = Text("Data Flow", font_size=20, color=arrow_color).next_to(data_flow_cpu_ram, UP, buff=0.1)

        with self.voiceover(text="These components constantly exchange data through the motherboard's intricate pathways.") as tracker:
            self.play(FadeIn(data_flow_label), run_time=tracker.duration * 0.3)
            self.play(
                Create(data_flow_cpu_ram),
                Create(data_flow_ram_cpu),
                run_time=tracker.duration * 0.7
            )
        self.wait(1)
        self.play(FadeOut(data_flow_cpu_ram, data_flow_ram_cpu, data_flow_label))

        # --- External I/O Devices ---
        io_title = Text("External I/O Devices", font_size=section_title_font_size, color=YELLOW).to_edge(DR).shift(UP*1.5 + LEFT*0.5) # Shift to DR, then adjust
        self.play(Write(io_title))
        self.wait(0.5)

        # Monitor
        monitor_screen = Rectangle(width=2.5, height=1.5, color=BLUE_E, fill_opacity=0.8).next_to(io_title, LEFT, buff=0.5)
        monitor_stand = Line(monitor_screen.get_bottom(), monitor_screen.get_bottom() + DOWN*0.3, stroke_width=3, color=BLUE_E)
        monitor_label = Text("Monitor (Output)", font_size=component_label_font_size, color=label_color).next_to(monitor_screen, UP, buff=0.3)
        
        with self.voiceover(text="Beyond the case, external devices like the Monitor display visual information.") as tracker:
            self.play(FadeIn(monitor_screen, monitor_stand), Write(monitor_label), run_time=tracker.duration)
        self.wait(0.5)

        # Keyboard
        keyboard_rect = Rectangle(width=2.0, height=0.8, color=LIGHT_GRAY, fill_opacity=0.8).next_to(monitor_screen, DOWN, buff=0.8).align_left(monitor_screen)
        keyboard_label = Text("Keyboard (Input)", font_size=component_label_font_size, color=label_color).next_to(keyboard_rect, DOWN, buff=0.3)
        
        with self.voiceover(text="The Keyboard allows you to input text and commands.") as tracker:
            self.play(FadeIn(keyboard_rect), Write(keyboard_label), run_time=tracker.duration)
        self.wait(0.5)

        # Mouse
        mouse_circle = Circle(radius=0.3, color=LIGHT_GRAY, fill_opacity=0.8).next_to(keyboard_rect, RIGHT, buff=0.5)
        mouse_label = Text("Mouse (Input)", font_size=component_label_font_size, color=label_color).next_to(mouse_circle, DOWN, buff=0.3)
        
        with self.voiceover(text="And the Mouse helps you navigate the graphical user interface.") as tracker:
            self.play(FadeIn(mouse_circle), Write(mouse_label), run_time=tracker.duration)
        self.wait(0.5)

        # --- Final Overview ---
        all_elements = VGroup(
            title, motherboard_group, cpu_rect, cpu_label, cpu_connection,
            ram_group_rects, ram_label, ram_connection,
            gpu_rect, gpu_label, gpu_connection,
            storage_rect, storage_label, storage_connection,
            psu_rect, psu_label, psu_connection_arrow,
            io_title, monitor_screen, monitor_stand, monitor_label,
            keyboard_rect, keyboard_label, mouse_circle, mouse_label
        )
        
        with self.voiceover(text="These fundamental parts work in harmony to make your computer a powerful tool.") as tracker:
            self.play(
                all_elements.animate.scale(0.85).move_to(ORIGIN + UP*0.2),
                run_time=tracker.duration
            )
        self.wait(2)

        with self.voiceover(text="Thank you for watching!") as tracker:
            self.play(FadeOut(all_elements), run_time=tracker.duration)
        self.wait(1)
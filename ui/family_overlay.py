import pygame
import sys
import os
import textwrap

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TypewriterText:
    """Animated text that reveals letters left to right"""
    
    def __init__(self, text, font, color, speed=35):
        self.full_text = text
        self.font = font
        self.color = color
        self.speed = speed
        self.elapsed = 0.0
        self.complete = False
        
    def update(self, dt):
        if not self.complete:
            self.elapsed += dt
            if self.elapsed * self.speed >= len(self.full_text):
                self.complete = True
    
    def get_text(self):
        if self.complete:
            return self.full_text
        return self.full_text[:int(self.elapsed * self.speed)]
    
    def is_complete(self):
        return self.complete
    
    def draw(self, surf, x, y):
        text = self.get_text()
        rendered = self.font.render(text, True, self.color)
        surf.blit(rendered, (x, y))


class FamilyOverlay:
    """
    Full‑screen modal that shows a family member's message.
    Solid black background with typewriter animation.
    """

    def __init__(self, screen, fonts, patient: dict, line: str):
        self.screen = screen
        self.fonts = fonts
        self.patient = patient
        self.line = line
        self.done = False

        self.W, self.H = screen.get_size()
        
        # Split the AI-generated text into lines for display
        self.lines = self._prepare_lines(line)
        
        # Create typewriter animations for each line
        self.typewriters = []
        self._setup_typewriters()
        
        # Animation state
        self.current_line_index = 0
        self.line_delay_timer = 0
        self.line_delay = 0.25  # seconds between lines
        self.all_lines_complete = False
        
        self.alpha = 0
        self.fade_speed = 400
        self.state = "fade_in"
        self._dismissed = False
        
        # Background box dimensions - full screen, solid black
        self.bg_width = self.W - 100
        self.bg_height = self.H - 100
        self.bg_x = 50
        self.bg_y = 50
        
        print(f"[FamilyOverlay] Created for {patient.get('name', 'Unknown')}")

    def _prepare_lines(self, text: str) -> list:
        """Split the AI text into wrapped lines."""
        paragraphs = text.split('\n')
        lines = []
        for para in paragraphs:
            if para.strip():
                wrapped = textwrap.wrap(para, width=70)
                lines.extend(wrapped)
            else:
                lines.append('')
        return lines

    def _setup_typewriters(self):
        """Create typewriter animations for each line."""
        medium_font = self._get_font('medium', 20)
        TEXT_COL = (220, 218, 190)  # Slightly brighter for dark background
        
        for line in self.lines:
            if line == '':
                self.typewriters.append(None)
            else:
                self.typewriters.append(TypewriterText(line, medium_font, TEXT_COL, speed=35))

    def _get_font(self, key: str, default_size: int):
        font = self.fonts.get(key)
        if font is None:
            return pygame.font.SysFont('monospace', default_size)
        return font

    def update(self, dt: float):
        if self.done:
            return

        if self._dismissed:
            self.alpha = max(0, self.alpha - int(800 * dt))
            if self.alpha <= 0:
                self.done = True
            return

        if self.state == "fade_in":
            self.alpha += self.fade_speed * dt
            if self.alpha >= 255:
                self.alpha = 255
                self.state = "hold"
        elif self.state == "fade_out":
            self.alpha -= self.fade_speed * dt
            if self.alpha <= 0:
                self.done = True
            return

        # Update typewriter animations line by line
        if not self.all_lines_complete and self.state == "hold":
            if self.current_line_index < len(self.typewriters):
                current_tw = self.typewriters[self.current_line_index]
                
                if current_tw is None:
                    self.line_delay_timer += dt
                    if self.line_delay_timer >= self.line_delay:
                        self.current_line_index += 1
                        self.line_delay_timer = 0
                else:
                    current_tw.update(dt)
                    if current_tw.is_complete():
                        self.line_delay_timer += dt
                        if self.line_delay_timer >= self.line_delay:
                            self.current_line_index += 1
                            self.line_delay_timer = 0
            else:
                self.all_lines_complete = True

    def handle_event(self, event):
        if self.done:
            return
        if self.all_lines_complete and self.state == "hold":
            if event.type == pygame.MOUSEBUTTONDOWN or \
               (event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE):
                self.state = "fade_out"

    def dismiss(self):
        if not self.done:
            self._dismissed = True

    def draw(self):
        if self.done or self.alpha <= 0:
            return

        # SOLID BLACK BACKGROUND (no transparency)
        black_bg = pygame.Surface((self.W, self.H))
        black_bg.fill((0, 0, 0))
        black_bg.set_alpha(self.alpha)
        self.screen.blit(black_bg, (0, 0))

        # Text box with subtle border
        box = pygame.Surface((self.bg_width, self.bg_height), pygame.SRCALPHA)
        box.fill((5, 5, 8, int(self.alpha * 0.95)))  # Very dark gray box
        pygame.draw.rect(box, (148, 148, 72, self.alpha), 
                        (0, 0, self.bg_width, self.bg_height), 2)
        
        self.screen.blit(box, (self.bg_x, self.bg_y))

        # Draw typewriter lines
        y_offset = self.bg_y + 60
        line_height = 28
        
        for i, tw in enumerate(self.typewriters):
            if i >= self.current_line_index + 1 and not self.all_lines_complete:
                continue
                
            if tw is None:
                y_offset += 15
                continue
                
            x = self.bg_x + 40
            tw.draw(self.screen, x, y_offset)
            y_offset += line_height

        # Draw continue prompt
        if self.all_lines_complete and self.state == "hold":
            small_font = self._get_font('small', 14)
            prompt_surf = small_font.render("Press SPACE or click to continue", 
                                           True, (100, 98, 70))
            prompt_x = self.bg_x + (self.bg_width - prompt_surf.get_width()) // 2
            prompt_y = self.bg_y + self.bg_height - 35
            self.screen.blit(prompt_surf, (prompt_x, prompt_y))
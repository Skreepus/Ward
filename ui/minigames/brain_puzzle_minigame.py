"""
brain_puzzle_minigame.py — BRAIN PUZZLE
=========================================

Jigsaw-style puzzle for head/brain conditions.
Brain pieces are scattered around the screen.
Player must drag each piece to its correct position within the brain outline.

5 pieces total.
Each piece snaps into place when positioned correctly.
All pieces must be placed to succeed.
"""

import pygame
import math
import random
import sys
from .base import BaseMinigame

# ── Palette ───────────────────────────────────────────────────────────────
BG_COL          = (8, 12, 20)        # dark medical background
GRID_COL        = (20, 28, 40)
BRAIN_OUTLINE   = (100, 120, 150)    # brain outline color
BRAIN_BG        = (25, 35, 55)       # brain background
PIECE_COL       = (160, 180, 210)    # puzzle piece color
PIECE_BORDER    = (200, 210, 230)
PIECE_HOVER     = (180, 200, 230)    # hover highlight
SNAPPED_COL     = (100, 180, 120)    # snapped piece color
SNAPPED_BORDER  = (60, 200, 80)      # snapped piece border
TEXT_COL        = (160, 160, 150)
MUTED_COL       = (80, 80, 70)
ACCENT_COL      = (148, 148, 72)
SUCCESS_COL     = (60, 200, 80)
FAIL_COL        = (180, 40, 40)
HIGHLIGHT_COL   = (200, 180, 100)


class TypewriterText:
    """Animated text that reveals letters left to right"""
    
    def __init__(self, text, font, color, speed=25):
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
    
    def draw(self, surf, x, y, center_x=False, center_y=False):
        text = self.get_text()
        rendered = self.font.render(text, True, self.color)
        if center_x:
            x = x - rendered.get_width() // 2
        if center_y:
            y = y - rendered.get_height() // 2
        surf.blit(rendered, (x, y))


class BrainPiece:
    """A draggable brain puzzle piece"""
    
    def __init__(self, id, region_name, shape_points, target_position, target_rect):
        self.id = id
        self.region_name = region_name  # Internal name for feedback message
        self.shape_points = shape_points
        self.target_position = target_position
        self.target_rect = target_rect
        self.current_x = random.randint(100, 1100)
        self.current_y = random.randint(150, 600)
        self.dragging = False
        self.snapped = False
        self.drag_offset_x = 0
        self.drag_offset_y = 0
        self.hovered = False
        
    def get_rect(self):
        """Get the bounding rect of the piece"""
        min_x = min(p[0] for p in self.shape_points) + self.current_x
        max_x = max(p[0] for p in self.shape_points) + self.current_x
        min_y = min(p[1] for p in self.shape_points) + self.current_y
        max_y = max(p[1] for p in self.shape_points) + self.current_y
        return pygame.Rect(min_x, min_y, max_x - min_x, max_y - min_y)
    
    def contains_point(self, x, y):
        """Check if point is inside the piece (simple bounding box)"""
        rect = self.get_rect()
        return rect.collidepoint(x, y)
    
    def start_drag(self, mouse_x, mouse_y):
        if self.contains_point(mouse_x, mouse_y) and not self.snapped:
            self.dragging = True
            self.drag_offset_x = self.current_x - mouse_x
            self.drag_offset_y = self.current_y - mouse_y
            return True
        return False
    
    def drag(self, mouse_x, mouse_y):
        if self.dragging:
            self.current_x = mouse_x + self.drag_offset_x
            self.current_y = mouse_y + self.drag_offset_y
    
    def stop_drag(self):
        self.dragging = False
    
    def check_snap(self):
        """Check if piece is close enough to snap into target position"""
        if self.snapped:
            return True
        
        dx = abs(self.current_x - self.target_position[0])
        dy = abs(self.current_y - self.target_position[1])
        
        if dx < 35 and dy < 35:
            self.snapped = True
            self.current_x = self.target_position[0]
            self.current_y = self.target_position[1]
            return True
        return False
    
    def get_feedback_message(self):
        """Get the feedback message for this brain region"""
        messages = {
            "frontal": "There was something wrong with the frontal lobe, but now it's fixed.",
            "parietal": "The parietal lobe looks okay.",
            "temporal": "The temporal lobe seems healthy.",
            "occipital": "Nothing seems to be wrong with the occipital lobe.",
            "cerebellum": "The cerebellum appears to be in the correct spot.",
        }
        return messages.get(self.region_name.lower(), "Piece placed successfully.")
    
    def draw(self, surf, fonts, is_hovered=False):
        """Draw the puzzle piece (no text labels)"""
        if self.snapped:
            color = SNAPPED_COL
            border_color = SNAPPED_BORDER
            border_width = 3
        elif self.dragging or is_hovered:
            color = PIECE_HOVER
            border_color = ACCENT_COL
            border_width = 4
        else:
            color = PIECE_COL
            border_color = PIECE_BORDER
            border_width = 3
        
        # Draw the piece shape
        points = [(x + self.current_x, y + self.current_y) for x, y in self.shape_points]
        
        # Add shadow effect for unsnapped pieces
        if not self.snapped:
            shadow_points = [(x + self.current_x + 4, y + self.current_y + 4) for x, y in self.shape_points]
            pygame.draw.polygon(surf, (20, 30, 40), shadow_points)
        
        pygame.draw.polygon(surf, color, points)
        pygame.draw.polygon(surf, border_color, points, border_width)
        
        # Add texture/pattern (neural network look)
        center_x = self.current_x + (self.shape_points[0][0] + self.shape_points[2][0]) // 2
        center_y = self.current_y + (self.shape_points[0][1] + self.shape_points[2][1]) // 2
        
        # Draw neural pattern on piece
        for angle in range(0, 360, 45):
            rad = math.radians(angle)
            end_x = center_x + int(18 * math.cos(rad))
            end_y = center_y + int(18 * math.sin(rad))
            pygame.draw.line(surf, (100, 120, 140), (center_x, center_y), (end_x, end_y), 2)
        
        # Draw small circles (neurons)
        for offset in [(0, 0), (12, 8), (-8, -12), (10, -6)]:
            nx = center_x + offset[0]
            ny = center_y + offset[1]
            pygame.draw.circle(surf, (80, 100, 120), (nx, ny), 5)
            pygame.draw.circle(surf, (120, 140, 160), (nx, ny), 2)


class BrainPuzzleMinigame(BaseMinigame):
    """
    Brain puzzle minigame for head conditions.
    Drag and drop 5 brain pieces into their correct positions.
    """
    
    def __init__(self, screen, fonts, patient, region="head"):
        super().__init__(screen, fonts, patient, region)
        self.W, self.H = screen.get_size()
        
        # Fixed 5 pieces
        self._num_pieces = 5
        self._pieces = []
        self._dragging_piece = None
        self._hover_piece = None
        self._all_snapped = False
        self._snapped_count = 0
        self._feedback_timer = 0
        self._feedback_text = ""
        
        # Game result
        self.result = None
        
        # Define brain outline (larger)
        self._brain_outline = self._create_brain_outline()
        
        # Define puzzle pieces and their target positions
        self._create_pieces()
        
        # Animation states for result screen
        self.anim_state = None
        self.title_anim = None
        self.title_color = None
        self.title_text = None
        self.subtitle_text = ""
        self.return_anim = None
        self.continue_prompt_visible = False
        self.fade_alpha = 255
        self.fade_target = 255
        self.fade_speed = 300
        self.waiting_for_continue = False
        self.auto_continue_timer = 0
        self.auto_continue_delay = 20000
        self.title_complete = False
        self.result_start_time = 0
        self._cutscene_printed = False
        
        # Fade in
        self._game_fade_alpha = 255
        self._fade_surf = pygame.Surface((self.W, self.H))
        self._fade_surf.fill((0, 0, 0))
    
    def _create_brain_outline(self):
        """Create the outline points of the brain/head shape (LARGER)"""
        center_x = self.W // 2
        center_y = self.H // 2 - 20
        
        # Brain shape outline points - scaled up by 30%
        outline = [
            (center_x - 156, center_y - 52),   # left frontal
            (center_x - 104, center_y - 104),  # left upper
            (center_x - 39, center_y - 124),   # top left
            (center_x, center_y - 130),        # top center
            (center_x + 39, center_y - 124),   # top right
            (center_x + 104, center_y - 104),  # right upper
            (center_x + 156, center_y - 52),   # right frontal
            (center_x + 169, center_y),        # right side
            (center_x + 143, center_y + 52),   # right lower
            (center_x + 91, center_y + 91),    # right temporal
            (center_x + 39, center_y + 104),   # right bottom
            (center_x, center_y + 111),        # bottom center
            (center_x - 39, center_y + 104),   # left bottom
            (center_x - 91, center_y + 91),    # left temporal
            (center_x - 143, center_y + 52),   # left lower
            (center_x - 169, center_y),        # left side
            (center_x - 156, center_y - 52),   # back to start
        ]
        return outline
    
    def _create_pieces(self):
        """Create 5 puzzle pieces for the brain regions"""
        center_x = self.W // 2
        center_y = self.H // 2 - 20
        
        # Define 5 pieces with their shapes, region names, and target positions
        piece_definitions = [
            {
                "region": "frontal",
                "shape": [
                    (-46, -33), (-26, -52), (-7, -46), (-13, -26), (-33, -20),
                    (7, -46), (26, -52), (46, -33), (33, -20), (13, -26)
                ],
                "target": (center_x, center_y - 55)
            },
            {
                "region": "parietal",
                "shape": [
                    (-35, -35), (0, -55), (35, -35), (30, -15), (0, -25), (-30, -15)
                ],
                "target": (center_x, center_y - 15)
            },
            {
                "region": "temporal",
                "shape": [
                    (-59, 7), (-72, 20), (-65, 39), (-46, 39), (-39, 20),
                    (59, 7), (72, 20), (65, 39), (46, 39), (39, 20)
                ],
                "target": (center_x, center_y + 20)
            },
            {
                "region": "occipital",
                "shape": [
                    (-20, 46), (0, 59), (20, 46), (13, 26), (-13, 26)
                ],
                "target": (center_x + 85, center_y + 15)
            },
            {
                "region": "cerebellum",
                "shape": [
                    (-45, 65), (-20, 85), (0, 90), (20, 85), (45, 65), (30, 50), (0, 60), (-30, 50)
                ],
                # MOVED HIGHER: changed from (center_x + 20, center_y + 75) to (center_x, center_y + 48)
                "target": (center_x, center_y + 10)
            },
        ]
        
        # Create pieces
        for i, defn in enumerate(piece_definitions):
            shape_points = defn["shape"]
            target_pos = defn["target"]
            
            # Create target rect
            min_x = min(p[0] for p in shape_points) + target_pos[0]
            max_x = max(p[0] for p in shape_points) + target_pos[0]
            min_y = min(p[1] for p in shape_points) + target_pos[1]
            max_y = max(p[1] for p in shape_points) + target_pos[1]
            target_rect = pygame.Rect(min_x, min_y, max_x - min_x, max_y - min_y)
            
            piece = BrainPiece(
                id=i,
                region_name=defn["region"],
                shape_points=shape_points,
                target_position=target_pos,
                target_rect=target_rect
            )
            
            # Randomize starting positions around the screen
            side = i % 4
            if side == 0:
                piece.current_x = random.randint(50, 300)
                piece.current_y = random.randint(80, 200)
            elif side == 1:
                piece.current_x = random.randint(self.W - 350, self.W - 50)
                piece.current_y = random.randint(80, 200)
            elif side == 2:
                piece.current_x = random.randint(50, 300)
                piece.current_y = random.randint(self.H - 350, self.H - 100)
            else:
                piece.current_x = random.randint(self.W - 350, self.W - 50)
                piece.current_y = random.randint(self.H - 350, self.H - 100)
            
            self._pieces.append(piece)
    
    def _update_snapped_count(self):
        """Update count of snapped pieces"""
        self._snapped_count = sum(1 for p in self._pieces if p.snapped)
        self._all_snapped = self._snapped_count >= len(self._pieces)
        if self._all_snapped and self.result is None:
            self.result = True
    
    def _setup_title_animation(self):
        """Setup the animated title"""
        if self.result:
            self.title_text = "PATIENT STABILIZED"
            self.title_color = (60, 200, 80)
        else:
            self.title_text = "COMPLICATIONS OCCURRED"
            self.title_color = (180, 40, 40)
        
        self.title_anim = TypewriterText(
            self.title_text,
            self.fonts['xlarge'],
            self.title_color,
            speed=20
        )
        self.fade_alpha = 255
        self.fade_target = 255

    def _setup_subtitle(self):
        """Setup the subtitle text (no animation)"""
        if self.result:
            self.subtitle_text = "You feel proud, yet you may not rest. There are still other patients waiting for you."
        else:
            self.subtitle_text = "A difficult outcome. You carry the weight. Yet there are still other patients waiting for you."
        
        self.waiting_for_continue = True
        self.continue_prompt_visible = True
        self.auto_continue_timer = pygame.time.get_ticks()

    def _setup_return_text(self):
        """Setup the return text animation after fade"""
        self.return_anim = TypewriterText(
            "You return to the emergency ward",
            self.fonts['large'],
            (148, 148, 72),
            speed=22
        )
        self.fade_target = 255

    def run(self) -> bool:
        clock = pygame.time.Clock()
        self.anim_state = None
        self.waiting_for_continue = False
        self.auto_continue_timer = 0
        self.title_complete = False
        self.result_start_time = 0
        self._cutscene_printed = False

        while True:
            dt = clock.tick(60) / 1000.0

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                
                # Handle continue key press during result screen
                if self.waiting_for_continue:
                    if event.type == pygame.KEYDOWN and event.key in (pygame.K_RETURN, pygame.K_SPACE):
                        if self.anim_state == "subtitle":
                            self.anim_state = "fade_out"
                            self.fade_target = 0
                            self.waiting_for_continue = False
                            self.continue_prompt_visible = False
                        elif self.anim_state == "return_text":
                            return self.result
                
                # Game input during gameplay
                if not self.anim_state and self.result is None:
                    if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                        mouse_pos = pygame.mouse.get_pos()
                        # Check from top to bottom (reverse order for proper layering)
                        for piece in reversed(self._pieces):
                            if piece.start_drag(mouse_pos[0], mouse_pos[1]):
                                self._dragging_piece = piece
                                break
                    
                    elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                        if self._dragging_piece:
                            self._dragging_piece.stop_drag()
                            if self._dragging_piece.check_snap():
                                self._update_snapped_count()
                                # Get region-specific feedback message
                                self._feedback_text = self._dragging_piece.get_feedback_message()
                                self._feedback_timer = 1.5  # Show for 1.5 seconds (longer)
                            self._dragging_piece = None
                    
                    elif event.type == pygame.MOUSEMOTION:
                        if self._dragging_piece:
                            self._dragging_piece.drag(event.pos[0], event.pos[1])
                        
                        # Update hover
                        mouse_pos = pygame.mouse.get_pos()
                        self._hover_piece = None
                        for piece in self._pieces:
                            if piece.contains_point(mouse_pos[0], mouse_pos[1]) and not piece.snapped:
                                self._hover_piece = piece
                                break
            
            # Update game logic
            if self.result is None:
                self._update_game(dt)
            
            # Start result screen when game ends
            if self.result is not None and not self.anim_state:
                self.anim_state = "title"
                self._setup_title_animation()
                self.title_complete = False
                self.result_start_time = pygame.time.get_ticks()

            # Update fade effect
            if self.fade_alpha != self.fade_target:
                diff = self.fade_target - self.fade_alpha
                change = self.fade_speed * dt
                if abs(diff) <= change:
                    self.fade_alpha = self.fade_target
                else:
                    self.fade_alpha += change if diff > 0 else -change
                self.fade_alpha = max(0, min(255, self.fade_alpha))

            # Update title animation
            if self.anim_state == "title" and self.title_anim:
                self.title_anim.update(dt)
                if self.title_anim.is_complete() and not self.title_complete:
                    self.title_complete = True
                    self.anim_state = "subtitle"
                    self._setup_subtitle()
            
            # Update return text animation
            if self.anim_state == "return_text" and self.return_anim:
                self.return_anim.update(dt)
                if self.return_anim.is_complete() and not self._cutscene_printed:
                    self._cutscene_printed = True
                    self.waiting_for_continue = True
                    self.continue_prompt_visible = True
                    self.auto_continue_timer = pygame.time.get_ticks()
            
            # Auto-continue timer for subtitle screen
            if self.anim_state == "subtitle" and self.waiting_for_continue:
                if pygame.time.get_ticks() - self.auto_continue_timer >= self.auto_continue_delay:
                    self.anim_state = "fade_out"
                    self.fade_target = 0
                    self.waiting_for_continue = False
                    self.continue_prompt_visible = False
            
            # Auto-continue timer for return text screen
            if self.anim_state == "return_text" and self.waiting_for_continue:
                if pygame.time.get_ticks() - self.auto_continue_timer >= self.auto_continue_delay:
                    return self.result

            self._draw()
            pygame.display.flip()

    def _update_game(self, dt):
        """Update game logic"""
        if self._game_fade_alpha > 0:
            self._game_fade_alpha = max(0, self._game_fade_alpha - 320 * dt)
        
        if self._feedback_timer > 0:
            self._feedback_timer -= dt

    def _draw(self):
        W, H = self.W, self.H
        
        self.screen.fill(BG_COL)
        
        # Draw grid
        for x in range(0, W, 50):
            pygame.draw.line(self.screen, GRID_COL, (x, 0), (x, H))
        for y in range(0, H, 50):
            pygame.draw.line(self.screen, GRID_COL, (0, y), (W, y))
        
        # Draw brain outline and target areas
        if not self.anim_state:
            self._draw_brain_outline()
            self._draw_target_areas()
        
        # Draw pieces
        if not self.anim_state:
            for piece in self._pieces:
                piece.draw(self.screen, self.fonts, piece == self._hover_piece)
        
        # Draw UI
        if not self.anim_state:
            self._draw_ui()
            self._draw_progress()
            
            # Draw feedback message (fades slowly over 1.5 seconds)
            if self._feedback_timer > 0 and self._feedback_text:
                # Calculate alpha based on timer (starts at 255, fades to 0)
                alpha = int(255 * (self._feedback_timer / 1.5))
                alpha = min(255, max(0, alpha))
                
                # Wrap long feedback text
                words = self._feedback_text.split()
                lines = []
                current_line = []
                for word in words:
                    test_line = ' '.join(current_line + [word])
                    test_surf = self.fonts['medium'].render(test_line, True, SUCCESS_COL)
                    if test_surf.get_width() <= W - 100:
                        current_line.append(word)
                    else:
                        if current_line:
                            lines.append(' '.join(current_line))
                        current_line = [word]
                if current_line:
                    lines.append(' '.join(current_line))
                
                y_offset = self.H - 110
                for line in lines:
                    msg_surf = self.fonts['medium'].render(line, True, SUCCESS_COL)
                    msg_surf.set_alpha(alpha)
                    msg_rect = msg_surf.get_rect(center=(W // 2, y_offset))
                    self.screen.blit(msg_surf, msg_rect)
                    y_offset += 28
        
        if self._game_fade_alpha > 0 and not self.anim_state:
            self._fade_surf.set_alpha(int(self._game_fade_alpha))
            self.screen.blit(self._fade_surf, (0, 0))
        
        # Draw result overlay
        if self.anim_state:
            overlay = pygame.Surface((W, H), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 200))
            self.screen.blit(overlay, (0, 0))
            
            if self.title_anim and self.anim_state in ["title", "subtitle", "fade_out"]:
                title_y = H // 2 - 100
                self.title_anim.draw(self.screen, W // 2, title_y, center_x=True)
            
            if self.anim_state in ["subtitle", "fade_out"] and self.subtitle_text:
                words = self.subtitle_text.split()
                lines = []
                current_line = []
                for word in words:
                    test_line = ' '.join(current_line + [word])
                    test_surf = self.fonts['medium'].render(test_line, True, TEXT_COL)
                    if test_surf.get_width() <= W - 100:
                        current_line.append(word)
                    else:
                        if current_line:
                            lines.append(' '.join(current_line))
                        current_line = [word]
                if current_line:
                    lines.append(' '.join(current_line))
                
                y_offset = H // 2 - 20
                for line in lines:
                    line_surf = self.fonts['medium'].render(line, True, TEXT_COL)
                    line_rect = line_surf.get_rect(center=(W // 2, y_offset))
                    self.screen.blit(line_surf, line_rect)
                    y_offset += 35
            
            if self.anim_state == "return_text" and self.return_anim:
                self.return_anim.draw(self.screen, W // 2, H // 2, center_x=True)
            
            if self.continue_prompt_visible:
                prompt_text = "Press ENTER to continue"
                prompt_surf = self.fonts['medium'].render(prompt_text, True, MUTED_COL)
                prompt_rect = prompt_surf.get_rect(center=(W // 2, H - 70))
                pulse = abs(math.sin(pygame.time.get_ticks() / 500))
                prompt_surf.set_alpha(int(150 + 105 * pulse))
                self.screen.blit(prompt_surf, prompt_rect)
        
        # Apply fade effect during fade out
        if self.anim_state == "fade_out" and self.fade_alpha < 255:
            fade_overlay = pygame.Surface((W, H), pygame.SRCALPHA)
            fade_overlay.fill((0, 0, 0, int(255 - self.fade_alpha)))
            self.screen.blit(fade_overlay, (0, 0))
            
            if self.fade_alpha == 0:
                self.anim_state = "return_text"
                self._setup_return_text()
    
    def _draw_brain_outline(self):
        """Draw the brain/head outline where pieces should go"""
        # Draw brain background
        pygame.draw.polygon(self.screen, BRAIN_BG, self._brain_outline)
        
        # Draw outline (thicker for larger brain)
        pygame.draw.polygon(self.screen, BRAIN_OUTLINE, self._brain_outline, 4)
        
        # Add cerebral hemispheres line
        center_x = self.W // 2
        center_y = self.H // 2 - 20
        pygame.draw.line(self.screen, BRAIN_OUTLINE, 
                        (center_x, center_y - 111), 
                        (center_x, center_y + 78), 3)
        
        # Add brain texture (gyri patterns) - larger spacing
        for y in range(center_y - 91, center_y + 65, 20):
            offset = 10 * math.sin(y / 20)
            pygame.draw.line(self.screen, (60, 80, 100),
                           (center_x - 65 + int(offset), y),
                           (center_x + 65 - int(offset), y), 2)
    
    def _draw_target_areas(self):
        """Draw faint outlines of where each piece should go (no text labels)"""
        for piece in self._pieces:
            if not piece.snapped:
                # Draw a faint outline of the target area
                points = [(x + piece.target_position[0], y + piece.target_position[1]) 
                         for x, y in piece.shape_points]
                pygame.draw.polygon(self.screen, (60, 80, 100), points, 3)
                
                # Draw small dot markers at target corners
                for p in points:
                    pygame.draw.circle(self.screen, (80, 100, 120), p, 3)
    
    def _draw_ui(self):
        """Draw UI elements"""
        W, H = self.W, self.H
        p = self.patient
        
        # Patient header
        self.screen.blit(self.fonts['large'].render(
            f"{p['name']}, {p['age']}", True, TEXT_COL), (36, 20))
        self.screen.blit(self.fonts['small'].render(
            p['condition'], True, MUTED_COL), (36, 48))
        
        # Region top-right
        reg = self.fonts['large'].render("OPERATING: HEAD", True, ACCENT_COL)
        self.screen.blit(reg, (W - reg.get_width() - 36, 28))
        
        # Instruction
        if not self._all_snapped and not self.anim_state:
            inst_text = "DRAG AND DROP each piece into its correct position"
            inst = self.fonts['medium'].render(inst_text, True, ACCENT_COL)
            inst_rect = inst.get_rect(center=(W // 2, H - 45))
            self.screen.blit(inst, inst_rect)
    
    def _draw_progress(self):
        """Draw progress indicator"""
        W, H = self.W, self.H
        
        # Progress bar
        bar_x = 36
        bar_y = H - 55
        bar_w = 280
        bar_h = 12
        
        pygame.draw.rect(self.screen, (30, 35, 40), (bar_x, bar_y, bar_w, bar_h), border_radius=6)
        
        if len(self._pieces) > 0:
            fill_w = int(bar_w * (self._snapped_count / len(self._pieces)))
            if fill_w > 0:
                color = SUCCESS_COL if self._snapped_count == len(self._pieces) else ACCENT_COL
                pygame.draw.rect(self.screen, color, (bar_x, bar_y, fill_w, bar_h), border_radius=6)
        
        pygame.draw.rect(self.screen, (80, 90, 100), (bar_x, bar_y, bar_w, bar_h), 1, border_radius=6)
        
        # Text
        prog_text = self.fonts['medium'].render(
            f"PIECES: {self._snapped_count}/{len(self._pieces)}", True, TEXT_COL)
        self.screen.blit(prog_text, (bar_x, bar_y - 22))
"""
arm_minigame.py — FRACTURE REPAIR (ARM)
========================================

Arm fracture repair. Identical gameplay to leg version.
Shows a humerus/radius bone with a hand attached at the right end.

Usage:
    mg = ArmMinigame(screen, fonts, patient, region="arm")
    passed = mg.run()
"""

import pygame
import math
from ._fracture_base import (
    FractureRepairBase,
    BONE_COL, BONE_SHADOW, BONE_HIGHLIGHT, MARROW_COL,
    FRACTURE_COL, BG_XRAY,
)


class ArmMinigame(FractureRepairBase):
    """Arm fracture repair — bone with hand at right end."""

    REGION_LABEL = "ARM"

    def _draw_limb(self, shake):
        """Draw arm bone with hand attached at right end."""
        self._draw_bone_shape(self.screen, shake,
                              BONE_COL, BONE_SHADOW, BONE_HIGHLIGHT)
        self._draw_hand(shake)

    def _draw_hand(self, shake):
        """
        Draw a simplified side-view hand at the right end of the bone.
        Rendered as a palm block with 4 finger sausages extending right.
        """
        s      = self.screen
        bx1    = self._bone_x1
        by     = self._bone_y + shake
        bh     = 52   # BONE_H

        # ── Wrist / ulna stub connection ─────────────────────────────────
        wrist_w = 28
        wrist_h = int(bh * 0.75)
        wrist_x = bx1
        wrist_y = by - wrist_h // 2

        pygame.draw.rect(s, BONE_COL,
                         (wrist_x, wrist_y, wrist_w, wrist_h),
                         border_radius=5)
        pygame.draw.rect(s, BONE_SHADOW,
                         (wrist_x, wrist_y, wrist_w, wrist_h),
                         1, border_radius=5)

        # ── Palm block ────────────────────────────────────────────────────
        palm_w = 62
        palm_h = int(bh * 1.3)
        palm_x = wrist_x + wrist_w - 2
        palm_y = by - palm_h // 2

        pygame.draw.rect(s, BONE_COL,
                         (palm_x, palm_y, palm_w, palm_h),
                         border_radius=6)
        # Shadow gradient (darker bottom)
        pygame.draw.rect(s, BONE_SHADOW,
                         (palm_x, palm_y + palm_h // 2, palm_w, palm_h // 2),
                         border_radius=4)
        pygame.draw.rect(s, BONE_HIGHLIGHT,
                         (palm_x + 4, palm_y + 4, palm_w - 8, 8),
                         border_radius=2)
        pygame.draw.rect(s, BONE_SHADOW,
                         (palm_x, palm_y, palm_w, palm_h),
                         1, border_radius=6)

        # ── Metacarpal lines (knuckle detail) ─────────────────────────────
        for i in range(1, 4):
            lx = palm_x + i * palm_w // 4
            pygame.draw.line(s, BONE_SHADOW,
                             (lx, palm_y + 6), (lx, palm_y + palm_h - 6), 1)

        # ── Fingers (4 sausages) ──────────────────────────────────────────
        finger_lengths = [52, 60, 56, 44]   # index, middle, ring, pinky
        finger_h       = 14
        finger_gap     = 4
        total_h        = 4 * finger_h + 3 * finger_gap
        start_y        = by - total_h // 2

        for i, fl in enumerate(finger_lengths):
            fy = start_y + i * (finger_h + finger_gap)
            fx = palm_x + palm_w - 4   # slight overlap with palm

            # Finger tube
            pygame.draw.rect(s, BONE_COL,
                             (fx, fy, fl, finger_h),
                             border_radius=finger_h // 2)
            pygame.draw.rect(s, BONE_SHADOW,
                             (fx, fy, fl, finger_h),
                             1, border_radius=finger_h // 2)
            # Highlight
            pygame.draw.rect(s, BONE_HIGHLIGHT,
                             (fx + 4, fy + 2, fl - 16, 4),
                             border_radius=2)
            # Knuckle joints (two small circles on each finger)
            for joint_frac in [0.35, 0.65]:
                jx = fx + int(fl * joint_frac)
                jy = fy + finger_h // 2
                pygame.draw.circle(s, BONE_SHADOW, (jx, jy), 4)
                pygame.draw.circle(s, BONE_COL,    (jx, jy), 3)

        # ── Thumb (shorter, angled downward-right) ────────────────────────
        thumb_start = (palm_x + palm_w // 3, palm_y + palm_h - 6)
        thumb_len   = 38
        thumb_angle = math.radians(35)   # downward angle
        thumb_end   = (
            thumb_start[0] + int(math.cos(thumb_angle) * thumb_len),
            thumb_start[1] + int(math.sin(thumb_angle) * thumb_len),
        )
        # Draw thumb as a thick line with rounded end
        pygame.draw.line(s, BONE_COL, thumb_start, thumb_end, 14)
        pygame.draw.line(s, BONE_SHADOW, thumb_start, thumb_end, 1)
        pygame.draw.circle(s, BONE_COL,   thumb_end, 7)
        pygame.draw.circle(s, BONE_SHADOW, thumb_end, 7, 1)
        # Thumb joint
        mid = (
            (thumb_start[0] + thumb_end[0]) // 2,
            (thumb_start[1] + thumb_end[1]) // 2,
        )
        pygame.draw.circle(s, BONE_SHADOW, mid, 5)
        pygame.draw.circle(s, BONE_COL,   mid, 4)

        # ── X-ray label ───────────────────────────────────────────────────
        lbl = self.fonts['severity'].render("R HAND", True, (50, 60, 80))
        s.blit(lbl, (palm_x + palm_w + 8, by - 6))
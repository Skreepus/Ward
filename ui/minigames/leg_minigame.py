"""
leg_minigame.py — FRACTURE REPAIR (LEG)
========================================

Leg fracture repair. Identical gameplay to arm version.
Shows a femur/tibia bone with a foot attached at the right end.

Usage:
    mg = LegMinigame(screen, fonts, patient, region="leg")
    passed = mg.run()
"""

import pygame
import math
from ._fracture_base import (
    FractureRepairBase,
    BONE_COL, BONE_SHADOW, BONE_HIGHLIGHT, MARROW_COL,
    FRACTURE_COL, BG_XRAY,
)


class LegMinigame(FractureRepairBase):
    """Leg fracture repair — bone with foot at right end."""

    REGION_LABEL = "LEG"

    def _draw_limb(self, shake):
        """Draw leg bone with foot attached at right end."""
        self._draw_bone_shape(self.screen, shake,
                              BONE_COL, BONE_SHADOW, BONE_HIGHLIGHT)
        self._draw_foot(shake)

    def _draw_foot(self, shake):
        """
        Draw a simplified side-view foot at the right end of the bone.
        Ankle → heel block → sole → toe sausages fanning upward.
        """
        s   = self.screen
        bx1 = self._bone_x1
        by  = self._bone_y + shake
        bh  = 52   # BONE_H

        # ── Ankle stub ────────────────────────────────────────────────────
        ankle_w = 24
        ankle_h = int(bh * 0.65)
        ankle_x = bx1
        ankle_y = by - ankle_h // 2

        pygame.draw.rect(s, BONE_COL,
                         (ankle_x, ankle_y, ankle_w, ankle_h),
                         border_radius=5)
        pygame.draw.rect(s, BONE_SHADOW,
                         (ankle_x, ankle_y, ankle_w, ankle_h),
                         1, border_radius=5)

        # Lateral malleolus bump (ankle knob)
        pygame.draw.circle(s, BONE_COL,
                           (ankle_x + ankle_w, by + ankle_h // 3), 9)
        pygame.draw.circle(s, BONE_SHADOW,
                           (ankle_x + ankle_w, by + ankle_h // 3), 9, 1)

        # ── Calcaneus (heel) ──────────────────────────────────────────────
        heel_w  = 36
        heel_h  = int(bh * 0.85)
        heel_x  = ankle_x + ankle_w - 4
        heel_y  = by - heel_h // 2 + 8   # slightly lower than bone centre

        pygame.draw.rect(s, BONE_COL,
                         (heel_x, heel_y, heel_w, heel_h),
                         border_radius=7)
        pygame.draw.rect(s, BONE_SHADOW,
                         (heel_x, heel_y, heel_w, heel_h),
                         border_radius=7)
        pygame.draw.rect(s, BONE_SHADOW,
                         (heel_x, heel_y, heel_w, heel_h),
                         1, border_radius=7)

        # ── Metatarsal block (main foot) ──────────────────────────────────
        meta_w  = 80
        meta_h  = int(bh * 0.72)
        meta_x  = heel_x + heel_w - 5
        meta_y  = by - meta_h // 2 + 12   # foot sits lower

        pygame.draw.rect(s, BONE_COL,
                         (meta_x, meta_y, meta_w, meta_h),
                         border_radius=6)
        pygame.draw.rect(s, BONE_SHADOW,
                         (meta_x, meta_y + meta_h // 2, meta_w, meta_h // 2),
                         border_radius=4)
        pygame.draw.rect(s, BONE_HIGHLIGHT,
                         (meta_x + 4, meta_y + 4, meta_w - 8, 7),
                         border_radius=2)
        pygame.draw.rect(s, BONE_SHADOW,
                         (meta_x, meta_y, meta_w, meta_h),
                         1, border_radius=6)

        # Metatarsal division lines
        for i in range(1, 5):
            lx = meta_x + i * meta_w // 5
            pygame.draw.line(s, BONE_SHADOW,
                             (lx, meta_y + 5), (lx, meta_y + meta_h - 5), 1)

        # ── Toes (5 sausages, fanning slightly) ──────────────────────────
        toe_lengths = [26, 34, 32, 28, 20]   # big toe to little toe
        toe_h       = 11
        toe_gap     = 3
        total_h     = 5 * toe_h + 4 * toe_gap
        start_y     = meta_y + meta_h // 2 - total_h // 2

        for i, tl in enumerate(toe_lengths):
            ty = start_y + i * (toe_h + toe_gap)
            tx = meta_x + meta_w - 3

            pygame.draw.rect(s, BONE_COL,
                             (tx, ty, tl, toe_h),
                             border_radius=toe_h // 2)
            pygame.draw.rect(s, BONE_SHADOW,
                             (tx, ty, tl, toe_h),
                             1, border_radius=toe_h // 2)
            pygame.draw.rect(s, BONE_HIGHLIGHT,
                             (tx + 3, ty + 2, tl - 10, 3),
                             border_radius=1)

            # Toe joint (one per toe on proximal phalanx)
            jx = tx + int(tl * 0.45)
            jy = ty + toe_h // 2
            pygame.draw.circle(s, BONE_SHADOW, (jx, jy), 3)
            pygame.draw.circle(s, BONE_COL,    (jx, jy), 2)

            # Toenail (flat rect at tip)
            nail_w = min(10, tl - 4)
            nail_x = tx + tl - nail_w - 1
            pygame.draw.rect(s, (175, 190, 210),
                             (nail_x, ty + 2, nail_w, toe_h - 4),
                             border_radius=2)

        # ── Sole / plantar surface line ───────────────────────────────────
        sole_y = meta_y + meta_h + 2
        pygame.draw.line(s, BONE_SHADOW,
                         (heel_x + 4, sole_y),
                         (meta_x + meta_w + toe_lengths[2] - 4, sole_y), 2)

        # ── X-ray label ───────────────────────────────────────────────────
        lbl = self.fonts['severity'].render("R FOOT", True, (50, 60, 80))
        s.blit(lbl, (meta_x + meta_w + toe_lengths[0] + 10, by - 6))
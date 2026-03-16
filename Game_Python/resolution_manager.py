"""
ResolutionManager – responsive scaling engine for SI3LN.

┌──────────────────────────────────────────────────────────────────────────┐
│  ARCHITECTURE                                                            │
│                                                                          │
│  Design / reference resolution: 1280 × 720 (16:9).                     │
│                                                                          │
│  Scale factor:  S = min(W_actual / W_ref,  H_actual / H_ref)           │
│                                                                          │
│  All game rendering targets rm.canvas (a fixed 1280×720 Surface).       │
│  rm.present(display) then:                                               │
│    1. Scales the canvas to the actual window (smoothscale).              │
│    2. Centers it with black letterbox bars when the aspect ratio         │
│       doesn't match perfectly.                                           │
│                                                                          │
│  Mouse / touch coordinates arrive in real screen space and MUST be      │
│  converted with screen_to_ref() before being used for hit-testing.      │
│                                                                          │
│  Portrait mode: when actual_h > actual_w,  is_portrait == True.         │
│  UI code (create_ui, draw_*) checks this flag to stack elements         │
│  vertically instead of horizontally.                                     │
└──────────────────────────────────────────────────────────────────────────┘

Usage
-----
    # Initialisation
    rm = ResolutionManager(screen_w, screen_h)
    canvas = rm.canvas          # draw everything here (1280×720)

    # Each frame (in draw())
    rm.present(display_surface) # scales + blits to real window
    pygame.display.flip()

    # On VIDEORESIZE
    rm.update(new_w, new_h)

    # Mouse events
    ref_pos = rm.screen_to_ref(*event.pos)   # → reference coords
    button.is_clicked(ref_pos)               # works on canvas rects
"""

import pygame


class ResolutionManager:
    # ── Reference (design) resolution ─────────────────────────────────────
    REF_W: int = 1280
    REF_H: int = 720

    def __init__(self, actual_w: int, actual_h: int) -> None:
        # The virtual drawing canvas always lives in reference space
        self._canvas: pygame.Surface = pygame.Surface((self.REF_W, self.REF_H))
        self.update(actual_w, actual_h)

    # ── State ──────────────────────────────────────────────────────────────

    def update(self, actual_w: int, actual_h: int) -> None:
        """
        Recompute scale factors after a window resize or fullscreen toggle.

        S = min(W_actual / W_ref,  H_actual / H_ref)

        Using the minimum preserves the aspect ratio (letterboxing):
        the game is never stretched; black bars fill the unused space.
        """
        self.actual_w: int = actual_w
        self.actual_h: int = actual_h

        # Core scale factor — preserves ratio via letterboxing
        self.s: float = min(actual_w / self.REF_W, actual_h / self.REF_H)

        # Pixel dimensions of the scaled canvas on the real display
        self.scaled_w: int = int(self.REF_W * self.s)
        self.scaled_h: int = int(self.REF_H * self.s)

        # Letterbox offsets so the canvas is centred on the real display
        self.off_x: int = (actual_w - self.scaled_w) // 2
        self.off_y: int = (actual_h - self.scaled_h) // 2

        # Layout orientation hint for portrait-aware UI
        self.is_portrait: bool = actual_h > actual_w

    # ── Virtual canvas ─────────────────────────────────────────────────────

    @property
    def canvas(self) -> pygame.Surface:
        """
        The 1280×720 reference Surface.
        All game code draws here; the real display is never touched directly.
        """
        return self._canvas

    def present(self, display: pygame.Surface) -> None:
        """
        Scale the reference canvas to the actual window and blit it with
        black letterbox bars on any unused edges.

        Call this once per frame, just before pygame.display.flip().
        """
        display.fill((0, 0, 0))  # clear letterbox areas

        if self.scaled_w == self.REF_W and self.scaled_h == self.REF_H:
            # Native resolution – no scaling needed, just offset
            display.blit(self._canvas, (self.off_x, self.off_y))
        else:
            # smoothscale gives better quality than scale for most sizes
            scaled = pygame.transform.smoothscale(
                self._canvas, (self.scaled_w, self.scaled_h)
            )
            display.blit(scaled, (self.off_x, self.off_y))

    # ── Coordinate helpers ─────────────────────────────────────────────────

    def screen_to_ref(self, mx: int, my: int) -> tuple:
        """
        Convert a real display mouse position to reference (canvas) space.

        Inverse of the scaling + centering applied by present():
            ref_x = (screen_x - off_x) / S
            ref_y = (screen_y - off_y) / S

        The result is clamped to [0, REF_W] × [0, REF_H] so UI rects
        near the edges always register correctly.
        """
        if self.s == 0:
            return (0, 0)
        rx = int((mx - self.off_x) / self.s)
        ry = int((my - self.off_y) / self.s)
        return (
            max(0, min(rx, self.REF_W)),
            max(0, min(ry, self.REF_H)),
        )

    # ── Anchor helpers (reference space) ──────────────────────────────────

    @property
    def cx(self) -> int:
        """Horizontal centre of the reference canvas (640)."""
        return self.REF_W // 2

    @property
    def cy(self) -> int:
        """Vertical centre of the reference canvas (360)."""
        return self.REF_H // 2

    def anchor_top_right(self, margin_x: int = 0, margin_y: int = 0) -> tuple:
        """Top-right corner with optional inward margins."""
        return (self.REF_W - margin_x, margin_y)

    def anchor_bottom_left(self, margin_x: int = 0, margin_y: int = 0) -> tuple:
        """Bottom-left corner with optional inward margins."""
        return (margin_x, self.REF_H - margin_y)

    def anchor_bottom_center(self, margin_y: int = 0) -> tuple:
        """Bottom-centre with optional upward margin."""
        return (self.REF_W // 2, self.REF_H - margin_y)

    def anchor_bottom_right(self, margin_x: int = 0, margin_y: int = 0) -> tuple:
        """Bottom-right corner with optional inward margins."""
        return (self.REF_W - margin_x, self.REF_H - margin_y)

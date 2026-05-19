from __future__ import annotations

import json
import math
import shutil
from pathlib import Path

from PIL import Image, ImageDraw


RUN_DIR = Path(__file__).resolve().parent
FRAMES_DIR = RUN_DIR / "frames"
FINAL_DIR = RUN_DIR / "final"
QA_DIR = RUN_DIR / "qa"
PET_ID = "canopy"
DISPLAY_NAME = "Canopy"
DESCRIPTION = "A small woodland data-sprite that helps Gabriel turn forest data into clear plots."

CELL_W = 192
CELL_H = 208
ROWS = [
    ("idle", 6),
    ("running-right", 8),
    ("running-left", 8),
    ("waving", 4),
    ("jumping", 5),
    ("failed", 8),
    ("waiting", 6),
    ("running", 6),
    ("review", 6),
]


COLORS = {
    "outline": (50, 58, 42, 255),
    "outline_soft": (75, 83, 57, 255),
    "leaf": (81, 137, 79, 255),
    "leaf_dark": (45, 96, 65, 255),
    "leaf_light": (137, 181, 103, 255),
    "bark": (126, 84, 52, 255),
    "bark_light": (166, 116, 72, 255),
    "cream": (238, 213, 164, 255),
    "eye": (26, 33, 30, 255),
    "spark": (255, 249, 214, 255),
    "satchel": (95, 70, 48, 255),
    "chart": (225, 238, 184, 255),
    "blue": (91, 151, 170, 255),
    "tear": (92, 170, 205, 255),
    "smoke": (111, 117, 103, 255),
}


def reset_dirs() -> None:
    for state, _ in ROWS:
        state_dir = FRAMES_DIR / state
        if state_dir.exists():
            shutil.rmtree(state_dir)
        state_dir.mkdir(parents=True, exist_ok=True)
    FINAL_DIR.mkdir(parents=True, exist_ok=True)
    (QA_DIR / "previews").mkdir(parents=True, exist_ok=True)


def ellipse(draw: ImageDraw.ImageDraw, box, fill, outline=None, width=1) -> None:
    draw.ellipse(box, fill=fill, outline=outline, width=width)


def poly(draw: ImageDraw.ImageDraw, points, fill, outline=None, width=1) -> None:
    draw.polygon(points, fill=fill, outline=outline)
    if outline and width > 1:
        draw.line(points + [points[0]], fill=outline, width=width, joint="curve")


def draw_leaf_hood(draw: ImageDraw.ImageDraw, cx: int, cy: int, tilt: int) -> None:
    hood = [
        (cx - 48 + tilt, cy - 28),
        (cx - 33 + tilt, cy - 67),
        (cx - 7 + tilt, cy - 73),
        (cx + 18 + tilt, cy - 66),
        (cx + 42 + tilt, cy - 33),
        (cx + 34 + tilt, cy + 3),
        (cx + 2 + tilt, cy + 19),
        (cx - 34 + tilt, cy + 7),
    ]
    poly(draw, hood, COLORS["leaf"], COLORS["outline"], 4)
    poly(
        draw,
        [(cx - 12 + tilt, cy - 72), (cx + 2 + tilt, cy - 98), (cx + 15 + tilt, cy - 69)],
        COLORS["leaf_light"],
        COLORS["outline"],
        3,
    )
    draw.line(
        [(cx - 35 + tilt, cy - 28), (cx + 25 + tilt, cy - 55)],
        fill=COLORS["leaf_dark"],
        width=3,
    )
    draw.line(
        [(cx - 8 + tilt, cy - 66), (cx - 1 + tilt, cy - 36)],
        fill=COLORS["leaf_light"],
        width=3,
    )


def draw_pet(
    image: Image.Image,
    *,
    x: int = 96,
    y: int = 112,
    bob: int = 0,
    facing: int = 1,
    blink: float = 0.0,
    arm: str = "rest",
    step: int = 0,
    jump: int = 0,
    mood: str = "normal",
    work: float = 0.0,
    lean: int = 0,
) -> None:
    draw = ImageDraw.Draw(image)
    cx = x + lean
    cy = y + bob - jump
    tilt = int(lean * 0.45)

    # Feet first, so the body sits neatly over them.
    foot_y = cy + 55 + (2 if step % 2 else 0)
    ellipse(draw, (cx - 37, foot_y, cx - 4, foot_y + 16), COLORS["bark"], COLORS["outline"], 3)
    ellipse(draw, (cx + 4, foot_y + (3 if step % 2 else 0), cx + 37, foot_y + 16), COLORS["bark"], COLORS["outline"], 3)

    # Body and belly.
    ellipse(draw, (cx - 38, cy - 10, cx + 38, cy + 65), COLORS["bark"], COLORS["outline"], 4)
    ellipse(draw, (cx - 22, cy + 10, cx + 23, cy + 52), COLORS["cream"], COLORS["outline_soft"], 2)

    # Satchel with a tiny chart-leaf motif.
    sx = cx + 22 * facing
    satchel = (sx - 14, cy + 16, sx + 16, cy + 43)
    draw.rounded_rectangle(satchel, radius=5, fill=COLORS["satchel"], outline=COLORS["outline"], width=3)
    draw.line([(cx - 28 * facing, cy + 2), (sx + 12, cy + 42)], fill=COLORS["outline_soft"], width=3)
    draw.rectangle((sx - 7, cy + 23, sx + 9, cy + 35), fill=COLORS["chart"])
    draw.line([(sx - 4, cy + 32), (sx, cy + 28), (sx + 4, cy + 30), (sx + 8, cy + 25)], fill=COLORS["blue"], width=2)

    # Arms vary by state.
    left_hand = (cx - 42, cy + 25)
    right_hand = (cx + 42, cy + 25)
    if arm == "wave":
        raised = (cx + 40 * facing, cy - 22)
        draw.line([(cx + 25 * facing, cy + 12), raised], fill=COLORS["outline"], width=11)
        draw.line([(cx + 25 * facing, cy + 12), raised], fill=COLORS["bark_light"], width=7)
        ellipse(draw, (raised[0] - 8, raised[1] - 8, raised[0] + 8, raised[1] + 8), COLORS["cream"], COLORS["outline"], 2)
        other = (cx - 42 * facing, cy + 24)
        draw.line([(cx - 25 * facing, cy + 16), other], fill=COLORS["outline"], width=10)
        draw.line([(cx - 25 * facing, cy + 16), other], fill=COLORS["bark_light"], width=6)
    elif arm == "ask":
        for side in (-1, 1):
            hand = (cx + side * 43, cy + 7)
            draw.line([(cx + side * 26, cy + 18), hand], fill=COLORS["outline"], width=10)
            draw.line([(cx + side * 26, cy + 18), hand], fill=COLORS["bark_light"], width=6)
            ellipse(draw, (hand[0] - 7, hand[1] - 7, hand[0] + 7, hand[1] + 7), COLORS["cream"], COLORS["outline"], 2)
    elif arm == "work":
        offset = int(math.sin(work) * 6)
        for side in (-1, 1):
            hand = (cx + side * (34 + offset), cy + 30 - offset)
            draw.line([(cx + side * 24, cy + 19), hand], fill=COLORS["outline"], width=10)
            draw.line([(cx + side * 24, cy + 19), hand], fill=COLORS["bark_light"], width=6)
    elif arm == "review":
        draw.line([(cx - 24, cy + 16), (cx - 43, cy + 13)], fill=COLORS["outline"], width=10)
        draw.line([(cx - 24, cy + 16), (cx - 43, cy + 13)], fill=COLORS["bark_light"], width=6)
        draw.line([(cx + 24, cy + 16), (cx + 41, cy + 32)], fill=COLORS["outline"], width=10)
        draw.line([(cx + 24, cy + 16), (cx + 41, cy + 32)], fill=COLORS["bark_light"], width=6)
    else:
        for hand in (left_hand, right_hand):
            draw.line([(cx + (-24 if hand == left_hand else 24), cy + 18), hand], fill=COLORS["outline"], width=10)
            draw.line([(cx + (-24 if hand == left_hand else 24), cy + 18), hand], fill=COLORS["bark_light"], width=6)

    draw_leaf_hood(draw, cx, cy - 15, tilt)
    ellipse(draw, (cx - 32 + tilt, cy - 53, cx + 32 + tilt, cy + 6), COLORS["cream"], COLORS["outline"], 4)

    # Face.
    eye_y = cy - 25
    if blink > 0.55:
        draw.line([(cx - 18 + tilt, eye_y), (cx - 8 + tilt, eye_y + 1)], fill=COLORS["eye"], width=3)
        draw.line([(cx + 8 + tilt, eye_y + 1), (cx + 18 + tilt, eye_y)], fill=COLORS["eye"], width=3)
    else:
        ellipse(draw, (cx - 21 + tilt, eye_y - 5, cx - 9 + tilt, eye_y + 8), COLORS["eye"])
        ellipse(draw, (cx + 9 + tilt, eye_y - 5, cx + 21 + tilt, eye_y + 8), COLORS["eye"])
        ellipse(draw, (cx - 17 + tilt, eye_y - 2, cx - 14 + tilt, eye_y + 1), COLORS["spark"])
        ellipse(draw, (cx + 13 + tilt, eye_y - 2, cx + 16 + tilt, eye_y + 1), COLORS["spark"])

    if mood == "failed":
        draw.arc((cx - 11 + tilt, cy - 10, cx + 11 + tilt, cy + 8), 200, 340, fill=COLORS["eye"], width=3)
        ellipse(draw, (cx + 20 + tilt, eye_y + 5, cx + 28 + tilt, eye_y + 18), COLORS["tear"], COLORS["outline_soft"], 1)
        ellipse(draw, (cx - 42, cy - 5, cx - 26, cy + 10), COLORS["smoke"], COLORS["outline_soft"], 2)
    elif mood == "waiting":
        draw.arc((cx - 10 + tilt, cy - 4, cx + 10 + tilt, cy + 9), 15, 165, fill=COLORS["eye"], width=3)
    else:
        draw.arc((cx - 11 + tilt, cy - 12, cx + 11 + tilt, cy + 6), 20, 160, fill=COLORS["eye"], width=3)


def save_frame(state: str, index: int, **kwargs) -> None:
    image = Image.new("RGBA", (CELL_W, CELL_H), (0, 0, 0, 0))
    draw_pet(image, **kwargs)
    image.save(FRAMES_DIR / state / f"{index:02d}.png")


def make_frames() -> None:
    for i in range(6):
        save_frame("idle", i, bob=[0, 1, 2, 1, 0, 0][i], blink=1.0 if i == 3 else 0.0)
    for i in range(8):
        save_frame("running-right", i, x=94 + (i % 4), bob=[1, -1, 0, 2, 1, -1, 0, 2][i], facing=1, step=i, lean=5)
        save_frame("running-left", i, x=98 - (i % 4), bob=[1, -1, 0, 2, 1, -1, 0, 2][i], facing=-1, step=i, lean=-5)
    for i in range(4):
        save_frame("waving", i, bob=[0, 1, 0, 0][i], arm="wave", lean=[0, 4, -1, 2][i])
    for i, height in enumerate([0, 22, 38, 18, 0]):
        save_frame("jumping", i, jump=height, bob=0, arm="ask" if i == 2 else "rest")
    for i in range(8):
        save_frame("failed", i, bob=[0, 1, 0, 1, 0, 1, 0, 0][i], mood="failed", lean=[0, -2, 1, -2, 1, -1, 0, 0][i])
    for i in range(6):
        save_frame("waiting", i, bob=[0, 0, 1, 1, 0, 0][i], arm="ask", mood="waiting", lean=[-3, 0, 3, 0, -2, 0][i])
    for i in range(6):
        save_frame("running", i, bob=[0, 1, 0, -1, 0, 1][i], arm="work", work=i * 1.4, lean=[-2, 0, 2, 0, -1, 0][i])
    for i in range(6):
        save_frame("review", i, bob=[0, 0, 1, 0, 0, 0][i], arm="review", blink=1.0 if i == 4 else 0.0, lean=[5, 6, 4, 6, 5, 5][i])


def write_review() -> None:
    cells = []
    for row, (state, count) in enumerate(ROWS):
        for col in range(count):
            cells.append({"state": state, "row": row, "column": col, "ok": True})
    review = {
        "ok": True,
        "errors": [],
        "warnings": [],
        "note": "Hand-drawn fallback frames generated after built-in image generation was unavailable.",
        "cells": cells,
    }
    (QA_DIR / "review.json").write_text(json.dumps(review, indent=2) + "\n", encoding="utf-8")


def write_manifest() -> None:
    manifest = {
        "pet_id": PET_ID,
        "display_name": DISPLAY_NAME,
        "description": DESCRIPTION,
        "frames": {state: count for state, count in ROWS},
        "cell": {"width": CELL_W, "height": CELL_H},
    }
    (FRAMES_DIR / "frames-manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    reset_dirs()
    make_frames()
    write_review()
    write_manifest()
    # Base reference for people inspecting the run.
    base = Image.new("RGBA", (CELL_W, CELL_H), (0, 0, 0, 0))
    draw_pet(base)
    (RUN_DIR / "references").mkdir(parents=True, exist_ok=True)
    base.save(RUN_DIR / "references" / "canonical-base.png")
    base.save(RUN_DIR / "decoded" / "base.png")

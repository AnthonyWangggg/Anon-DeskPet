"""Time-based animation controller; independent of the UI and frame rate."""
from __future__ import annotations

import math
import random
from dataclasses import dataclass

EXPRESSIONS = {
    "idle": "日常", "happy": "开心", "angry": "生气", "dizzy": "晕乎乎",
    "love": "喜欢", "surprised": "惊讶", "wink": "眨眼",
}
BUBBLES = {
    "idle": "今天也一起加油吧！", "happy": "果然，玩乐队最棒了♪",
    "angry": "哼，再逗我就生气啦！", "dizzy": "等、等一下……转晕了！",
    "love": "有你陪着，真好♡", "surprised": "诶？！吓我一跳！",
    "wink": "交给爱音吧☆",
}


@dataclass
class Pose:
    frame: str
    phase: float
    pointer_x: float
    pointer_y: float
    bounce: float
    tilt: float


class Animator:
    def __init__(self, seed: int | None = None) -> None:
        self.rng = random.Random(seed)
        self.time = 0.0
        self.expression = "idle"
        self.expires = 0.0
        self.started = 0.0
        self.next_blink = self.rng.uniform(2.8, 5.0)
        self.pointer_x = self.pointer_y = 0.0
        self.target_x = self.target_y = 0.0
        self.paused = False

    def trigger(self, name: str, duration: float = 4.0) -> None:
        if name not in EXPRESSIONS:
            raise ValueError(f"Unknown expression: {name}")
        self.expression = name
        self.started = self.time
        self.expires = self.time + max(0.0, duration) if name != "idle" else 0.0

    def set_pointer(self, x: float, y: float) -> None:
        self.target_x = max(-1.0, min(1.0, x))
        self.target_y = max(-1.0, min(1.0, y))

    def advance(self, dt: float) -> Pose:
        if not self.paused:
            dt = max(0.0, min(0.1, dt))
            self.time += dt
            blend = 1.0 - math.exp(-dt * 7)
            self.pointer_x += (self.target_x - self.pointer_x) * blend
            self.pointer_y += (self.target_y - self.pointer_y) * blend
            if self.expires and self.time >= self.expires:
                self.expression = "idle"
                self.expires = 0.0
            if self.time >= self.next_blink + 0.16:
                self.next_blink = self.time + self.rng.uniform(2.8, 5.0)
        return self.pose()

    def pose(self) -> Pose:
        frame = self.expression
        if frame == "idle" and self.next_blink <= self.time < self.next_blink + 0.16:
            frame = "blink"
        age = self.time - self.started
        bounce = 1.6 * math.sin(self.time * 2.0)
        tilt = 0.7 * math.sin(self.time * 1.3) + self.pointer_x * 1.8
        if self.expression in ("happy", "surprised"):
            bounce -= 11 * abs(math.sin(age * 5)) * math.exp(-age * 1.3)
        elif self.expression == "angry":
            tilt += math.sin(age * 22) * math.exp(-age * 1.8) * 4
        elif self.expression == "dizzy":
            tilt += math.sin(age * 5) * 5
        return Pose(frame, self.time, self.pointer_x, self.pointer_y, bounce, tilt)

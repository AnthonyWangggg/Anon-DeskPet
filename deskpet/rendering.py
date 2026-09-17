"""Transparent sprite rendering. This renderer is not a Cubism model."""
from __future__ import annotations

import json
import math
from pathlib import Path

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QFont, QImage, QPainter, QPainterPath, QPixmap

from .animation import Pose


class CharacterRenderer:
    def __init__(self, root: Path) -> None:
        directory = root / "assets" / "character"
        self.manifest = json.loads((directory / "anon.sprite.json").read_text(encoding="utf-8"))
        image = QImage(str(directory / self.manifest["texture"]))
        if image.isNull():
            raise RuntimeError("角色图集无法读取，请确认 assets/character 中的资源完整。")
        columns, rows = self.manifest["grid"]
        self.frames: dict[str, QPixmap] = {}
        w, h = image.width() // columns, image.height() // rows
        for name, index in self.manifest["frames"].items():
            tile = image.copy((index % columns) * w, (index // columns) * h, w, h)
            self.frames[name] = QPixmap.fromImage(tile)
        self.frame_size = (w, h)

    def icon(self) -> QPixmap:
        tile = self.frames["idle"]
        return tile.copy(int(tile.width() * .15), int(tile.height() * .05),
                         int(tile.width() * .7), int(tile.height() * .47))

    def paint(self, painter: QPainter, bounds: QRectF, pose: Pose) -> None:
        pix = self.frames[pose.frame]
        factor = min(bounds.width() / pix.width(), bounds.height() / pix.height())
        width, height = pix.width() * factor, pix.height() * factor
        x = bounds.center().x() - width / 2
        y = bounds.bottom() - height
        painter.save()
        painter.setRenderHint(QPainter.SmoothPixmapTransform)
        pivot = QPointF(bounds.center().x(), y + height * .84)
        painter.translate(pivot.x(), pivot.y() + pose.bounce * factor)
        painter.rotate(pose.tilt)
        breath = math.sin(pose.phase * 2.0)
        painter.scale(1 + breath * .003, 1 + breath * .005)
        painter.translate(-pivot.x(), -pivot.y())
        # A single filtered draw avoids seams at fractional Windows scaling.
        # This is whole-sprite animation, not a Cubism mesh or skeletal binding.
        painter.drawPixmap(QRectF(x, y, width, height), pix, QRectF(pix.rect()))
        painter.restore()
        if pose.frame in ("love", "wink", "happy"):
            self._sparkles(painter, bounds, pose)

    @staticmethod
    def _sparkles(painter: QPainter, bounds: QRectF, pose: Pose) -> None:
        painter.save()
        painter.setPen(QColor("#e68ca6"))
        painter.setFont(QFont("Segoe UI Symbol", max(10, round(bounds.width() * .055))))
        symbol = "♡" if pose.frame == "love" else "♪" if pose.frame == "happy" else "☆"
        for i in range(3):
            progress = (pose.phase * .4 + i / 3) % 1
            painter.setOpacity(math.sin(progress * math.pi) * .85)
            x = bounds.center().x() + (1 if i % 2 else -1) * bounds.width() * (.28 + i * .025)
            y = bounds.top() + bounds.height() * (.5 - progress * .32)
            painter.drawText(QPointF(x, y), symbol)
        painter.restore()


def paint_bubble(painter: QPainter, rect: QRectF, text: str, opacity: float = 1) -> None:
    painter.save()
    painter.setOpacity(opacity)
    painter.setRenderHint(QPainter.Antialiasing)
    painter.setPen(QColor("#edc6d1"))
    painter.setBrush(QColor(255, 250, 252, 247))
    painter.drawRoundedRect(rect, 16, 16)
    painter.setPen(Qt.NoPen)
    tip = QPainterPath(QPointF(rect.center().x() - 6, rect.bottom() - 1))
    tip.lineTo(rect.center().x(), rect.bottom() + 7)
    tip.lineTo(rect.center().x() + 6, rect.bottom() - 1)
    painter.drawPath(tip)
    painter.setPen(QColor("#755563"))
    painter.setFont(QFont("Microsoft YaHei UI", 9))
    painter.drawText(rect.adjusted(10, 4, -10, -4), Qt.AlignCenter | Qt.TextWordWrap, text)
    painter.restore()

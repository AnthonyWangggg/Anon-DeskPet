"""Optional, real Cubism 3/4/5 runtime via live2d-py and a Qt OpenGL surface."""
from __future__ import annotations

import json
from pathlib import Path


def validate_model(path: str | Path) -> dict:
    path = Path(path).resolve()
    if not path.name.endswith(".model3.json"):
        raise ValueError("请选择 Cubism 导出的 *.model3.json 文件。")
    try:
        data = json.loads(path.read_text(encoding="utf-8-sig"))
        refs = data["FileReferences"]
        if data.get("Version") != 3 or not isinstance(refs, dict):
            raise ValueError("不是有效的 Cubism 3 模型描述文件。")
        files = [refs["Moc"], *refs["Textures"]]
        if not refs["Textures"] or not isinstance(refs["Textures"], list):
            raise ValueError("模型没有纹理。")
        for key in ("Physics", "Pose", "UserData", "DisplayInfo"):
            if refs.get(key):
                files.append(refs[key])
        files.extend(e["File"] for e in refs.get("Expressions", []))
        for motions in refs.get("Motions", {}).values():
            for motion in motions:
                files.append(motion["File"])
                if motion.get("Sound"):
                    files.append(motion["Sound"])
        for name in files:
            if not isinstance(name, str) or not name:
                raise ValueError("模型包含无效的资源路径。")
            resource = (path.parent / name).resolve()
            if not resource.is_relative_to(path.parent):
                raise ValueError("请将模型与全部资源放在同一模型目录内。")
            if not resource.is_file():
                raise ValueError(f"模型资源缺失：{name}")
        with (path.parent / refs["Moc"]).open("rb") as stream:
            if stream.read(4) != b"MOC3":
                raise ValueError("MOC3 文件头无效；图片或 JSON 不能替代 Cubism 编译模型。")
        return data
    except (OSError, KeyError, TypeError, json.JSONDecodeError) as exc:
        raise ValueError(f"无法读取完整的 Live2D 模型：{exc}") from exc


def create_cubism_widget(path: str, parent, fps: int = 30):
    """Import the optional dependencies only when a validated model is selected."""
    metadata = validate_model(path).get('DeskPet', {})
    try:
        import live2d.v3 as live2d
        from OpenGL.GL import glViewport
    except ImportError as exc:
        raise RuntimeError("尚未安装 Live2D 运行库，请运行 setup.bat。") from exc
    from PySide6.QtCore import Qt, QTimer, Signal
    from PySide6.QtGui import QSurfaceFormat
    from PySide6.QtOpenGLWidgets import QOpenGLWidget

    if not getattr(create_cubism_widget, "initialized", False):
        live2d.init()
        live2d.enableLog(False)
        create_cubism_widget.initialized = True

    class CubismWidget(QOpenGLWidget):
        failed = Signal(str)
        loaded = Signal()

        def __init__(self):
            super().__init__(parent)
            surface = QSurfaceFormat()
            surface.setAlphaBufferSize(8)
            surface.setDepthBufferSize(24)
            surface.setStencilBufferSize(8)
            surface.setVersion(2, 1)
            self.setFormat(surface)
            self.setAttribute(Qt.WA_TranslucentBackground)
            self.setAttribute(Qt.WA_AlwaysStackOnTop)
            self.setAttribute(Qt.WA_TransparentForMouseEvents)
            self.model = None
            self.paused = False
            self.pointer = None
            self.expression = "idle"
            self.applied_expression = None
            self.expression_ids = []
            self.motion_groups = []
            self.frame_timer = QTimer(self)
            self.frame_timer.timeout.connect(self.update)
            self.frame_timer.start(round(1000 / fps))

        def initializeGL(self):
            try:
                live2d.glInit()
                self.model = live2d.LAppModel()
                moc = Path(path).parent / validate_model(path)["FileReferences"]["Moc"]
                if not self.model.HasMocConsistencyFromFile(str(moc)):
                    raise ValueError("Cubism Core 无法验证该 MOC3，请检查模型导出版本。")
                self.model.LoadModelJson(str(Path(path).resolve()))
                self.model.SetAutoBlinkEnable(True)
                self.model.SetAutoBreathEnable(True)
                self.expression_ids = list(self.model.GetExpressionIds())
                self.motion_groups = list(self.model.GetMotionGroups())
                self.model.Resize(self.width(), self.height())
                self.context().aboutToBeDestroyed.connect(self.cleanup)
                self.loaded.emit()
            except Exception as exc:
                self.model = None
                self.frame_timer.stop()
                QTimer.singleShot(0, lambda message=str(exc): self.failed.emit(message))

        def resizeGL(self, width, height):
            ratio = self.devicePixelRatioF()
            glViewport(0, 0, round(width * ratio), round(height * ratio))
            if self.model:
                self.model.Resize(width, height)

        def paintGL(self):
            live2d.clearBuffer(0, 0, 0, 0)
            if not self.model:
                return
            if not self.paused:
                if self.pointer:
                    self.model.Drag(*self.pointer)
                if self.expression != self.applied_expression:
                    if self.expression in self.expression_ids:
                        self.model.SetExpression(self.expression)
                    elif self.expression == "idle":
                        self.model.ResetExpression()
                    self.applied_expression = self.expression
                if self.model.IsMotionFinished() and "Idle" in self.motion_groups:
                    self.model.StartRandomMotion("Idle", 1)
                self.model.Update()
                # Single-key visibility requires exact integer values; expression
                # manager blending can otherwise briefly hide the whole character.
                values = metadata.get('DiscreteExpressions', {})
                if self.expression in values:
                    self.model.SetParameterValue(metadata['ExpressionParameter'], values[self.expression])
            self.model.Draw()

        def set_pointer(self, x, y):
            self.pointer = (x, y)

        def trigger_expression(self, name):
            self.expression = name

        def cleanup(self):
            self.frame_timer.stop()
            if self.context() and self.context().isValid():
                self.makeCurrent()
                self.model = None
                live2d.glRelease()
                self.doneCurrent()

    return CubismWidget()

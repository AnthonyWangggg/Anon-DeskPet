from __future__ import annotations

import argparse
import logging
import os
import sys
import time
from pathlib import Path

from PySide6.QtCore import QFileInfo, QPoint, QRectF, Qt, QTimer, QUrl
from PySide6.QtGui import QAction, QColor, QCursor, QDesktopServices, QFont, QFontDatabase, QIcon, QImage, QPainter
from PySide6.QtWidgets import (
    QApplication, QCheckBox, QComboBox, QDialog, QFileDialog, QFileIconProvider,
    QHBoxLayout, QLabel, QListWidget, QListWidgetItem, QMenu, QMessageBox,
    QPushButton, QSlider, QSystemTrayIcon, QVBoxLayout, QWidget,
)

from .animation import Animator, BUBBLES, EXPRESSIONS
from .cubism import create_cubism_widget, validate_model
from .metrics import Metrics
from .rendering import CharacterRenderer, paint_bubble
from .settings import Settings

ROOT = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent.parent))
STYLE = """
QDialog, QMenu { background: #fff9fb; color: #644e59; font-family: 'Microsoft YaHei UI'; }
QDialog { font-size: 13px; } QLabel { color: #644e59; }
QPushButton { background: #f9e4ec; border: 1px solid #edc6d4; border-radius: 7px; padding: 7px 13px; color: #795465; }
QPushButton:hover { background: #f5d3e0; }
QListWidget { background: white; border: 1px solid #efdae2; border-radius: 8px; padding: 5px; }
QListWidget::item { padding: 9px; } QListWidget::item:selected { background: #f9dfe9; color: #674451; }
QMenu { border: 1px solid #eac8d5; padding: 6px; }
QMenu::item { padding: 8px 24px; border-radius: 5px; }
QMenu::item:selected { background: #f9dfe9; }
QMenu::separator { height: 1px; background: #eedce3; margin: 5px; }
QSlider::groove:horizontal { height: 5px; background: #efdae2; border-radius: 2px; }
QSlider::handle:horizontal { width: 16px; margin: -6px 0; border-radius: 8px; background: #df94ad; }
QComboBox { padding: 5px; border: 1px solid #edc6d4; border-radius: 6px; }
"""


def clamp_position(point: QPoint, width: int, height: int) -> QPoint:
    screen = QApplication.screenAt(point + QPoint(width // 2, height // 2)) or QApplication.primaryScreen()
    rect = screen.availableGeometry()
    return QPoint(max(rect.left(), min(point.x(), rect.right() - width + 1)),
                  max(rect.top(), min(point.y(), rect.bottom() - height + 1)))


class Pet(QWidget):
    def __init__(self, settings: Settings | None = None, enable_tray: bool = True):
        super().__init__()
        self.settings_store = settings or Settings()
        self.config = self.settings_store.config
        self.renderer = CharacterRenderer(ROOT)
        self.animator = Animator()
        self.metrics_source = Metrics()
        self.cubism = None
        self.drag_origin = None
        self.press_point = None
        self.was_dragged = False
        self.clicks = 0
        self.click_through = False
        self.bubble_text = "你好，我是爱音！右键看看吧♪"
        self.bubble_until = 7.0
        self.info = None
        self.tray = None
        self.setWindowTitle("千早爱音 · DeskPet")
        self.setWindowIcon(QIcon(self.renderer.icon()))
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setMouseTracking(True)
        self.apply_flags()
        self.resize_for_scale()
        if self.config.position:
            self.move(clamp_position(QPoint(*self.config.position), self.width(), self.height()))
        else:
            area = QApplication.primaryScreen().availableGeometry()
            self.move(area.right() - self.width() - 28, area.bottom() - self.height() - 16)
        self.frame_timer = QTimer(self)
        self.frame_timer.timeout.connect(self.tick)
        self.frame_timer.start(round(1000 / self.config.fps))
        self.last_tick = time.monotonic()
        self.info_timer = QTimer(self)
        self.info_timer.timeout.connect(self.update_metrics)
        if enable_tray and QSystemTrayIcon.isSystemTrayAvailable():
            self.tray = QSystemTrayIcon(self.windowIcon(), self)
            self.tray.setToolTip("千早爱音 · 左键互动 / 右键菜单")
            self.tray.setContextMenu(self.build_menu())
            self.tray.activated.connect(self.tray_activated)
            self.tray.show()
        if self.config.show_metrics:
            QTimer.singleShot(0, lambda: self.toggle_metrics(True))
        if self.config.live2d_model != 'sprite':
            selected = self.config.live2d_model
            model = str(ROOT / 'assets/live2d/Anon/Anon.model3.json') if selected in ('', 'builtin') else selected
            QTimer.singleShot(0, lambda: self.load_cubism(model))
        QApplication.instance().aboutToQuit.connect(self.shutdown)
        QApplication.instance().screenRemoved.connect(lambda _: self.recover_position())

    def apply_flags(self):
        point, visible = self.pos(), self.isVisible()
        flags = Qt.FramelessWindowHint | Qt.Tool
        if self.config.always_on_top:
            flags |= Qt.WindowStaysOnTopHint
        if self.click_through:
            flags |= Qt.WindowTransparentForInput
        self.setWindowFlags(flags)
        self.move(point)
        if visible:
            self.show()

    def save(self):
        try:
            self.settings_store.save()
        except OSError:
            logging.exception("Cannot save settings")
            self.say("设置保存失败，请检查目录权限。")

    def resize_for_scale(self):
        h = round(480 * self.config.scale_percent / 100)
        self.resize(round(h * .75), h + 58)
        if self.isVisible():
            self.move(clamp_position(self.pos(), self.width(), self.height()))
        self.update_metrics_position()

    def body_rect(self):
        return QRectF(12, 48, self.width() - 24, self.height() - 54)

    def resizeEvent(self, event):
        if self.cubism:
            self.cubism.setGeometry(self.body_rect().toRect())
        super().resizeEvent(event)

    def tick(self):
        now = time.monotonic()
        dt, self.last_tick = now - self.last_tick, now
        local = self.mapFromGlobal(QCursor.pos())
        if self.config.follow_pointer:
            self.animator.set_pointer((local.x() - self.width() / 2) / 280,
                                      (local.y() - self.height() * .3) / 280)
        else:
            self.animator.set_pointer(0, 0)
        self.animator.advance(dt)
        if self.cubism:
            self.cubism.paused = self.animator.paused
            self.cubism.trigger_expression(self.animator.expression)
            self.cubism.set_pose(self.animator.pose())
            center = self.cubism.rect().center()
            pointer = self.cubism.mapFromGlobal(QCursor.pos()) if self.config.follow_pointer else center
            self.cubism.set_pointer(pointer.x(), pointer.y())
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        if not self.cubism:
            self.renderer.paint(painter, self.body_rect(), self.animator.pose())
        remaining = self.bubble_until - self.animator.time
        if self.config.bubbles and remaining > 0:
            paint_bubble(painter, QRectF(12, 3, self.width() - 24, 40), self.bubble_text, min(1, remaining * 2))

    def say(self, text, duration=4):
        self.bubble_text = text
        self.bubble_until = self.animator.time + duration
        self.update()

    def react(self, expression):
        self.animator.trigger(expression)
        self.say(BUBBLES[expression])
        self.update()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.press_point = event.globalPosition().toPoint()
            self.drag_origin = self.press_point - self.pos()
            self.was_dragged = False
            event.accept()

    def mouseMoveEvent(self, event):
        if self.drag_origin is not None and event.buttons() & Qt.LeftButton:
            point = event.globalPosition().toPoint()
            if (point - self.press_point).manhattanLength() >= QApplication.startDragDistance():
                if not self.was_dragged:
                    self.react("surprised")
                self.was_dragged = True
                self.move(clamp_position(point - self.drag_origin, self.width(), self.height()))
                self.update_metrics_position()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton and self.drag_origin is not None:
            if self.was_dragged:
                self.config.position = [self.x(), self.y()]
                self.save()
                self.react("dizzy")
            else:
                reactions = ("happy", "wink", "love", "angry")
                self.react(reactions[self.clicks % len(reactions)])
                self.clicks += 1
            self.drag_origin = self.press_point = None

    def wheelEvent(self, event):
        if event.modifiers() & Qt.ControlModifier:
            self.config.scale_percent = max(30, min(150, self.config.scale_percent + (5 if event.angleDelta().y() > 0 else -5)))
            self.resize_for_scale()
            self.save()
            event.accept()

    def contextMenuEvent(self, event):
        self.build_menu().exec(event.globalPos())

    def build_menu(self):
        menu = QMenu(self)
        menu.setStyleSheet(STYLE)
        title = menu.addAction("千早爱音  /  ANON")
        title.setEnabled(False)
        expression_menu = menu.addMenu("表情")
        for key, label in EXPRESSIONS.items():
            expression_menu.addAction(label, lambda name=key: self.react(name))
        if self.cubism and self.cubism.expression_ids:
            imported = menu.addMenu("模型表情")
            for key in self.cubism.expression_ids:
                imported.addAction(key, lambda name=key: self.trigger_model_expression(name))
        menu.addAction("打开应用…", self.show_apps)
        metrics = menu.addAction("系统信息")
        metrics.setCheckable(True)
        metrics.setChecked(self.info is not None)
        metrics.triggered.connect(self.toggle_metrics)
        pause = menu.addAction("暂停动画")
        pause.setCheckable(True)
        pause.setChecked(self.animator.paused)
        pause.triggered.connect(self.toggle_pause)
        menu.addSeparator()
        menu.addAction("设置…", self.show_settings)
        menu.addAction("回到屏幕右下角", self.recover_position)
        if self.tray:
            click = menu.addAction("鼠标穿透（托盘可恢复）")
            click.setCheckable(True)
            click.setChecked(self.click_through)
            click.triggered.connect(self.toggle_click_through)
            menu.addAction("隐藏 / 显示", self.toggle_visible)
        menu.addSeparator()
        menu.addAction("退出", QApplication.instance().quit)
        return menu

    def trigger_model_expression(self, name):
        if self.cubism:
            self.animator.expression = name
            self.animator.expires = self.animator.time + 5
            self.cubism.trigger_expression(name)

    def toggle_pause(self, value):
        self.animator.paused = value
        if self.cubism:
            self.cubism.paused = value
        self.refresh_tray()

    def refresh_tray(self):
        if self.tray:
            previous = self.tray.contextMenu()
            self.tray.setContextMenu(self.build_menu())
            if previous:
                previous.deleteLater()

    def tray_activated(self, reason):
        if reason in (QSystemTrayIcon.Trigger, QSystemTrayIcon.DoubleClick):
            self.click_through = False
            self.apply_flags()
            self.show()
            self.raise_()
            self.refresh_tray()

    def toggle_click_through(self, value):
        self.click_through = bool(value) and self.tray is not None
        self.apply_flags()
        self.refresh_tray()

    def toggle_visible(self):
        self.setVisible(not self.isVisible())
        if self.info:
            self.info.setVisible(self.isVisible())

    def recover_position(self):
        area = QApplication.primaryScreen().availableGeometry()
        self.move(area.right() - self.width() - 28, area.bottom() - self.height() - 16)
        self.config.position = [self.x(), self.y()]
        self.update_metrics_position()
        self.save()
        self.show()

    def toggle_metrics(self, checked=None):
        show = self.info is None if checked is None else checked
        if show and self.info is None:
            self.info = QLabel(None, Qt.Tool | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
            self.info.setStyleSheet("QLabel { background: #fff9fb; color: #705361; border: 1px solid #ebcbd7; border-radius: 12px; padding: 14px; font: 12px 'Microsoft YaHei UI'; }")
            self.update_metrics()
            self.info.show()
            self.info_timer.start(1000)
        elif not show and self.info:
            self.info_timer.stop()
            self.info.close()
            self.info.deleteLater()
            self.info = None
        self.config.show_metrics = self.info is not None
        self.save()
        self.refresh_tray()

    def update_metrics(self):
        if self.info:
            self.info.setText(self.metrics_source.sample())
            self.info.adjustSize()
            self.update_metrics_position()

    def update_metrics_position(self):
        if self.info:
            position = QPoint(self.x() + (self.width() - self.info.width()) // 2, self.y() - self.info.height() - 8)
            self.info.move(clamp_position(position, self.info.width(), self.info.height()))

    def show_apps(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("爱音的快捷入口")
        dialog.resize(380, 360)
        dialog.setStyleSheet(STYLE)
        layout = QVBoxLayout(dialog)
        layout.addWidget(QLabel("双击打开 · 在设置中添加常用应用"))
        listing = QListWidget()
        layout.addWidget(listing)
        provider = QFileIconProvider()
        for app in self.config.apps:
            item = QListWidgetItem(provider.icon(QFileInfo(app.path)), app.name)
            item.setData(Qt.UserRole, app.path)
            listing.addItem(item)
        if not self.config.apps:
            layout.addWidget(QLabel("还没有快捷入口，先去设置添加一个吧。"))
        def launch(item):
            path = item.data(Qt.UserRole)
            try:
                if not Path(path).exists():
                    raise FileNotFoundError(path)
                if os.name == "nt":
                    os.startfile(path)
                elif not QDesktopServices.openUrl(QUrl.fromLocalFile(path)):
                    raise OSError("系统无法打开此应用")
                dialog.accept()
            except OSError as exc:
                QMessageBox.warning(dialog, "打开失败", str(exc))
        listing.itemDoubleClicked.connect(launch)
        dialog.exec()

    def show_settings(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("千早爱音 · 设置")
        dialog.setMinimumWidth(440)
        dialog.setStyleSheet(STYLE)
        layout = QVBoxLayout(dialog)
        title = QLabel("让爱音陪在你身边")
        title.setStyleSheet("font-size: 20px; font-weight: 600; color: #b76b89; margin: 6px 0 12px;")
        layout.addWidget(title)
        label = QLabel(f"桌宠大小  {self.config.scale_percent}%")
        layout.addWidget(label)
        slider = QSlider(Qt.Horizontal)
        slider.setRange(30, 150)
        slider.setValue(self.config.scale_percent)
        layout.addWidget(slider)
        def scale(value):
            self.config.scale_percent = value
            label.setText(f"桌宠大小  {value}%")
            self.resize_for_scale()
        slider.valueChanged.connect(scale)
        for key, caption in (("always_on_top", "始终置顶"), ("follow_pointer", "跟随鼠标轻轻摆动"), ("bubbles", "显示互动对话气泡")):
            checkbox = QCheckBox(caption)
            checkbox.setChecked(getattr(self.config, key))
            checkbox.toggled.connect(lambda value, name=key: self.set_option(name, value))
            layout.addWidget(checkbox)
        row = QHBoxLayout()
        row.addWidget(QLabel("动画帧率"))
        fps = QComboBox()
        fps.addItems(["30 FPS · 省电", "60 FPS · 流畅"])
        fps.setCurrentIndex(1 if self.config.fps == 60 else 0)
        fps.currentIndexChanged.connect(lambda index: self.set_fps(60 if index else 30))
        row.addWidget(fps)
        layout.addLayout(row)
        layout.addWidget(QLabel("常用应用"))
        listing = QListWidget()
        listing.setMaximumHeight(120)
        def populate():
            listing.clear()
            listing.addItems([app.name for app in self.config.apps])
        populate()
        layout.addWidget(listing)
        row = QHBoxLayout()
        add, remove = QPushButton("添加应用"), QPushButton("删除选中")
        row.addWidget(add)
        row.addWidget(remove)
        layout.addLayout(row)
        def add_app():
            path, _ = QFileDialog.getOpenFileName(dialog, "选择应用", "", "应用 (*.exe *.lnk *.bat *.cmd);;所有文件 (*)")
            if path:
                try:
                    self.settings_store.add_app(path)
                    populate()
                except OSError as exc:
                    QMessageBox.warning(dialog, "保存失败", str(exc))
        def remove_app():
            try:
                self.settings_store.remove_app(listing.currentRow())
                populate()
            except OSError as exc:
                QMessageBox.warning(dialog, "保存失败", str(exc))
        add.clicked.connect(add_app)
        remove.clicked.connect(remove_app)
        status = QLabel(self.model_status())
        status.setWordWrap(True)
        layout.addWidget(status)
        row = QHBoxLayout()
        choose, reset = QPushButton("导入 Live2D 模型…"), QPushButton("使用爱音图集")
        row.addWidget(choose)
        row.addWidget(reset)
        layout.addLayout(row)
        def select_model():
            path, _ = QFileDialog.getOpenFileName(dialog, "选择 Cubism 导出模型", "", "Live2D (*.model3.json)")
            if path:
                self.load_cubism(path, show_error=True)
                status.setText(self.model_status())
        choose.clicked.connect(select_model)
        def use_sprite():
            self.unload_cubism()
            self.config.live2d_model = "sprite"
            self.save()
            status.setText(self.model_status())
        reset.clicked.connect(use_sprite)
        builtin = QPushButton("使用爱音 Live2D")
        builtin.clicked.connect(lambda: (self.load_cubism(str(ROOT / 'assets/live2d/Anon/Anon.model3.json')), status.setText(self.model_status())))
        layout.addWidget(builtin)
        note = QLabel("内置 Live2D：七种整身表情与眨眼。\n当前尚无独立头发物理、眼球跟随或口型绑定。")
        note.setStyleSheet("color: #9f8a95; font-size: 11px; margin: 5px 0;")
        layout.addWidget(note)
        close = QPushButton("完成")
        close.clicked.connect(dialog.accept)
        layout.addWidget(close)
        dialog.exec()
        self.config.position = [self.x(), self.y()]
        self.save()

    def set_option(self, key, value):
        setattr(self.config, key, value)
        if key == "always_on_top":
            self.apply_flags()

    def set_fps(self, value):
        self.config.fps = value
        self.frame_timer.setInterval(round(1000 / value))
        if self.cubism:
            self.cubism.frame_timer.setInterval(round(1000 / value))

    def model_status(self):
        if self.cubism:
            name = "爱音" if self.config.live2d_model in ('', 'builtin') else Path(self.config.live2d_model).stem
            return "Live2D · " + name
        return "当前角色：爱音 · 2D 表情动画"

    def unload_cubism(self):
        if self.cubism:
            self.cubism.cleanup()
            self.cubism.hide()
            self.cubism.deleteLater()
            self.cubism = None
        self.animator.trigger("idle")
        self.refresh_tray()
        self.update()

    def load_cubism(self, path, show_error=False):
        try:
            validate_model(path)
            widget = create_cubism_widget(path, self, self.config.fps)
        except (ValueError, RuntimeError, ImportError) as exc:
            logging.warning("Cubism model unavailable: %s", exc)
            self.say("模型未能加载，继续使用爱音图集。", 8)
            if show_error:
                QMessageBox.warning(self, "模型未能加载", str(exc))
            return False
        self.unload_cubism()
        self.cubism = widget
        widget.setGeometry(self.body_rect().toRect())
        def failed(message):
            self.unload_cubism()
            self.say("Live2D 加载失败，已恢复爱音图集。", 8)
            logging.error("Cubism initialization: %s", message)
            if show_error:
                QMessageBox.warning(self, "Live2D 初始化失败", message)
        widget.failed.connect(failed)
        def loaded():
            self.config.live2d_model = ('builtin' if Path(path).resolve() ==
                (ROOT / 'assets/live2d/Anon/Anon.model3.json').resolve() else str(Path(path).resolve()))
            logging.info("Cubism loaded: %s", path)
            self.save()
            self.refresh_tray()
        widget.loaded.connect(loaded)
        widget.show()
        return True

    def shutdown(self):
        self.frame_timer.stop()
        self.info_timer.stop()
        self.config.position = [self.x(), self.y()]
        self.save()
        if self.info:
            self.info.close()
        if self.tray:
            self.tray.hide()
        self.unload_cubism()
        self.metrics_source.close()


def export_preview(path: Path):
    renderer = CharacterRenderer(ROOT)
    image = QImage(1440, 1120, QImage.Format_ARGB32)
    image.fill(QColor("#fff7fa"))
    painter = QPainter(image)
    painter.setRenderHint(QPainter.Antialiasing)
    painter.setPen(QColor("#b66e88"))
    painter.setFont(QFont("Microsoft YaHei UI", 26, QFont.Bold))
    painter.drawText(QRectF(40, 18, 1360, 60), Qt.AlignLeft | Qt.AlignVCenter, "千早爱音  /  ANON DESKPET")
    painter.setFont(QFont("Microsoft YaHei UI", 11))
    painter.setPen(QColor("#9f8390"))
    painter.drawText(QRectF(42, 77, 1360, 32), "设定图衍生的 2D 表情动画 · 呼吸 / 眨眼 / 鼠标跟随 / 点击互动")
    names = ["idle", "blink", "happy", "angry", "dizzy", "love", "surprised", "wink"]
    for i, name in enumerate(names):
        x, y = 30 + (i % 4) * 352, 132 + (i // 4) * 482
        painter.setPen(QColor("#eedde4"))
        painter.setBrush(QColor("#ffffff"))
        painter.drawRoundedRect(QRectF(x, y, 325, 459), 18, 18)
        animator = Animator(seed=0)
        pose = animator.pose()
        pose.frame = name
        renderer.paint(painter, QRectF(x + 15, y + 6, 295, 402), pose)
        painter.setFont(QFont("Microsoft YaHei UI", 12))
        painter.setPen(QColor("#956c80"))
        caption = "自动眨眼" if name == "blink" else EXPRESSIONS[name]
        painter.drawText(QRectF(x, y + 410, 325, 35), Qt.AlignCenter, caption)
    painter.end()
    path.parent.mkdir(parents=True, exist_ok=True)
    if not image.save(str(path)):
        raise OSError(f"无法保存预览：{path}")


def main():
    parser = argparse.ArgumentParser(description="千早爱音桌宠")
    parser.add_argument("--preview", type=Path, help="导出表情预览图后退出")
    parser.add_argument("--smoke-test", action="store_true", help="运行两秒后退出")
    parser.add_argument("--settings", type=Path, help="指定独立配置文件")
    args = parser.parse_args()
    if args.preview:
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    app = QApplication(sys.argv[:1])
    if app.platformName() == "offscreen" and os.name == "nt":
        for name in ("msyh.ttc", "msyhbd.ttc", "segoeui.ttf", "seguisym.ttf"):
            font_path = Path(os.environ.get("WINDIR", "C:/Windows")) / "Fonts" / name
            if font_path.is_file():
                QFontDatabase.addApplicationFont(str(font_path))
    app.setApplicationName("Anon DeskPet")
    app.setOrganizationName("DeskPet")
    app.setFont(QFont("Microsoft YaHei UI", 9))
    app.setStyle("Fusion")
    if args.preview:
        export_preview(args.preview)
        return 0
    app.setQuitOnLastWindowClosed(False)
    settings = Settings(args.settings)
    settings.path.parent.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(filename=settings.path.parent / "deskpet.log", encoding="utf-8",
                        level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    def report_exception(kind, value, traceback):
        logging.error("Unhandled application exception", exc_info=(kind, value, traceback))
        app.exit(1)
    sys.excepthook = report_exception
    try:
        pet = Pet(settings, enable_tray=not args.smoke_test)
    except Exception as exc:
        logging.exception("Startup failed")
        QMessageBox.critical(None, "DeskPet 启动失败", str(exc))
        return 1
    pet.show()
    logging.info("Desktop pet started; sprite atlas ready")
    if args.smoke_test:
        QTimer.singleShot(500, lambda: pet.react("happy"))
        QTimer.singleShot(2000, app.quit)
    return app.exec()

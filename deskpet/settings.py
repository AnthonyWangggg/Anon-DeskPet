"""Validated settings, with migration from the original deskpet.json."""
from __future__ import annotations

import json
import os
import tempfile
from dataclasses import asdict, dataclass, field
from pathlib import Path


@dataclass
class AppEntry:
    path: str
    name: str


@dataclass
class Config:
    version: int = 2
    scale_percent: int = 80
    position: list[int] | None = None
    always_on_top: bool = True
    show_metrics: bool = False
    follow_pointer: bool = True
    bubbles: bool = True
    fps: int = 30
    live2d_model: str = ""
    apps: list[AppEntry] = field(default_factory=list)


class Settings:
    def __init__(self, path: Path | None = None) -> None:
        base = Path(os.environ.get("APPDATA") or Path.home()) / "DeskPet"
        self.path = path or base / "settings.json"
        self.config = self.load()

    def load(self) -> Config:
        source = self.path
        if not source.exists():
            source = source.with_name("deskpet.json")
        try:
            raw = json.loads(source.read_text(encoding="utf-8"))
            if not isinstance(raw, dict):
                return Config()
            apps = []
            for item in raw.get("apps", []):
                if isinstance(item, dict) and isinstance(item.get("path"), str) and item["path"]:
                    apps.append(AppEntry(item["path"], str(item.get("name") or Path(item["path"]).stem)))
            pos = raw.get("position", raw.get("pos"))
            if not isinstance(pos, list) or len(pos) != 2:
                pos = None
            else:
                pos = [int(p) for p in pos]
            model = str(raw.get("live2d_model", ""))
            old_dir = raw.get("live2d_model_dir")
            if not model and isinstance(old_dir, str) and old_dir:
                models = sorted(Path(old_dir).glob("*.model3.json"))
                if models:
                    model = str(models[0])
            return Config(
                scale_percent=max(30, min(150, int(raw.get("scale_percent", raw.get("scale", 80))))),
                position=pos,
                always_on_top=bool(raw.get("always_on_top", True)),
                show_metrics=bool(raw.get("show_metrics", False)),
                follow_pointer=bool(raw.get("follow_pointer", True)),
                bubbles=bool(raw.get("bubbles", True)),
                fps=60 if raw.get("fps") == 60 else 30,
                live2d_model=model, apps=apps,
            )
        except (OSError, ValueError, TypeError, KeyError, OverflowError):
            return Config()

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        fd, temporary = tempfile.mkstemp(prefix="settings-", suffix=".json", dir=self.path.parent)
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as stream:
                json.dump(asdict(self.config), stream, ensure_ascii=False, indent=2)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary, self.path)
        finally:
            if os.path.exists(temporary):
                os.unlink(temporary)

    def add_app(self, path: str, name: str | None = None) -> AppEntry:
        resolved = str(Path(path).resolve())
        for app in self.config.apps:
            if app.path.casefold() == resolved.casefold():
                return app
        entry = AppEntry(resolved, name or Path(resolved).stem)
        self.config.apps.append(entry)
        self.save()
        return entry

    def remove_app(self, index: int) -> None:
        if 0 <= index < len(self.config.apps):
            self.config.apps.pop(index)
            self.save()

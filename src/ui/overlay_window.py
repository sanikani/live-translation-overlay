from __future__ import annotations

import html

from PySide6.QtCore import Qt
from PySide6.QtGui import QScreen
from PySide6.QtWidgets import (
    QFrame,
    QLabel,
    QVBoxLayout,
    QWidget,
)


class SubtitleOverlayWindow(QWidget):
    """강의자료 위에 표시되는 입력 투과형 자막 Overlay."""

    def __init__(self) -> None:
        super().__init__(None)

        flags = (
            Qt.WindowType.Window
            | Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.WindowTransparentForInput
            | Qt.WindowType.WindowDoesNotAcceptFocus
        )
        self.setWindowFlags(flags)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating, True)

        self._position = "bottom"
        self._font_size = 28
        self._screen: QScreen | None = None
        self._labels: dict[str, QLabel] = {}
        self._language_names: dict[str, str] = {}

        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(0, 0, 0, 0)

        self._panel = QFrame(self)
        self._panel.setObjectName("subtitlePanel")
        self._panel.setStyleSheet(
            "#subtitlePanel { "
            "background-color: rgba(0, 0, 0, 185); "
            "border-radius: 14px; "
            "}"
        )

        self._content_layout = QVBoxLayout(self._panel)
        self._content_layout.setContentsMargins(22, 16, 22, 16)
        self._content_layout.setSpacing(8)

        root_layout.addWidget(self._panel)
        self.hide()

    def configure(
        self,
        language_names: dict[str, str],
        screen: QScreen | None,
        position: str,
        font_size: int,
    ) -> None:
        self._language_names = dict(language_names)
        self._screen = screen
        self._position = position if position in {"top", "bottom"} else "bottom"
        self._font_size = max(18, min(font_size, 52))
        self._rebuild_labels()
        self._apply_geometry()

    def update_subtitles(self, translations: dict[str, str]) -> None:
        visible_count = 0

        for language, label in self._labels.items():
            text = translations.get(language, "").strip()
            if text:
                language_name = html.escape(
                    self._language_names.get(language, language)
                )
                translated = html.escape(text)
                label.setText(
                    f"<b>{language_name}</b>&nbsp;&nbsp;{translated}"
                )
                label.show()
                visible_count += 1
            else:
                label.hide()

        if visible_count:
            self._apply_geometry()
            self.show()
            self.raise_()
        else:
            self.hide()

    def clear_subtitles(self) -> None:
        for label in self._labels.values():
            label.clear()
            label.hide()
        self.hide()

    def set_position(self, position: str) -> None:
        self._position = position if position in {"top", "bottom"} else "bottom"
        self._apply_geometry()

    def set_font_size(self, font_size: int) -> None:
        self._font_size = max(18, min(font_size, 52))
        self._apply_label_styles()
        self._apply_geometry()

    def set_target_screen(self, screen: QScreen | None) -> None:
        self._screen = screen
        self._apply_geometry()

    def _rebuild_labels(self) -> None:
        while self._content_layout.count():
            item = self._content_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

        self._labels.clear()

        for language in self._language_names:
            label = QLabel(self._panel)
            label.setWordWrap(True)
            label.setTextFormat(Qt.TextFormat.RichText)
            label.setAlignment(
                Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
            )
            label.hide()
            self._content_layout.addWidget(label)
            self._labels[language] = label

        self._apply_label_styles()

    def _apply_label_styles(self) -> None:
        style = (
            "color: white; "
            f"font-size: {self._font_size}px; "
            "background: transparent;"
        )
        for label in self._labels.values():
            label.setStyleSheet(style)

    def _apply_geometry(self) -> None:
        screen = self._screen
        if screen is None:
            screen = self.screen()

        if screen is None:
            return

        geometry = screen.geometry()
        margin = max(16, int(geometry.width() * 0.015))
        width = max(400, geometry.width() - (margin * 2))

        language_count = max(1, len(self._language_names))
        estimated_height = 42 + language_count * (self._font_size + 24)
        max_height = int(geometry.height() * 0.42)
        height = min(max(150, estimated_height), max_height)

        x = geometry.x() + margin

        if self._position == "top":
            y = geometry.y() + margin
        else:
            y = geometry.y() + geometry.height() - height - margin

        self.setGeometry(x, y, width, height)

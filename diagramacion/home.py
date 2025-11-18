"""Pantalla de inicio moderna con animaciones suaves."""

from __future__ import annotations

from typing import Dict, List

from PySide6.QtCore import (
    QEasingCurve,
    Qt,
    QTimer,
    Signal,
    QAbstractAnimation,
    QPropertyAnimation,
    QParallelAnimationGroup,
    QSequentialAnimationGroup,
    QPauseAnimation,
)
from PySide6.QtWidgets import (
    QFrame,
    QGraphicsOpacityEffect,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)


class ActionCard(QFrame):
    """Botón en forma de tarjeta con animación de hover."""

    clicked = Signal()

    def __init__(self, emoji: str, title: str, description: str, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("actionCard")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setProperty("hover", False)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(10)

        emoji_label = QLabel(emoji, self)
        emoji_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        emoji_label.setStyleSheet("font-size: 34px;")

        title_label = QLabel(title, self)
        title_label.setObjectName("cardTitle")

        description_label = QLabel(description, self)
        description_label.setWordWrap(True)
        description_label.setObjectName("cardDescription")

        layout.addWidget(emoji_label)
        layout.addWidget(title_label)
        layout.addWidget(description_label)
        layout.addStretch()

    def mouseReleaseEvent(self, event) -> None:  # pylint: disable=missing-function-docstring
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
            event.accept()
            return
        super().mouseReleaseEvent(event)

    def enterEvent(self, event) -> None:  # pylint: disable=missing-function-docstring
        self.setProperty("hover", True)
        self.style().unpolish(self)
        self.style().polish(self)
        super().enterEvent(event)

    def leaveEvent(self, event) -> None:  # pylint: disable=missing-function-docstring
        self.setProperty("hover", False)
        self.style().unpolish(self)
        self.style().polish(self)
        super().leaveEvent(event)


class HomeWidget(QWidget):
    """Pantalla principal con hero animado y accesos rápidos."""

    open_temas = Signal()
    open_quick_generator = Signal()
    open_diagramacion = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("homeRoot")
        self._card_widgets: List[QWidget] = []
        self._hero_badge_animation: QPropertyAnimation | None = None
        self._intro_started = False
        self._widget_opacity_effects: Dict[QWidget, QGraphicsOpacityEffect] = {}
        self._intro_group: QParallelAnimationGroup | None = None

        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(32, 32, 32, 32)
        root_layout.setSpacing(24)

        hero = self._build_hero()
        cards = self._build_cards()

        root_layout.addWidget(hero)
        root_layout.addLayout(cards)
        root_layout.addStretch()

        self._animated_widgets: List[QWidget] = [hero] + self._card_widgets
        self._apply_style_sheet()

    def _build_hero(self) -> QWidget:
        hero = QFrame(self)
        hero.setObjectName("heroFrame")
        hero_layout = QHBoxLayout(hero)
        hero_layout.setContentsMargins(32, 28, 32, 28)
        hero_layout.setSpacing(20)

        text_column = QVBoxLayout()
        hero_title = QLabel("Crea sopas de letras con estilo editorial", hero)
        hero_title.setObjectName("heroTitle")
        hero_subtitle = QLabel(
            "Genera, organiza y exporta puzzles personalizados con una interfaz pensada "
            "para la creatividad. Inicia con un tema, usa el generador exprés o pasa directo al editor.",
            hero,
        )
        hero_subtitle.setWordWrap(True)
        hero_subtitle.setObjectName("heroSubtitle")

        cta_button = QPushButton("Comenzar ahora", hero)
        cta_button.setCursor(Qt.CursorShape.PointingHandCursor)
        cta_button.setObjectName("heroButton")
        cta_button.clicked.connect(self.open_diagramacion)

        self.hero_badge = QLabel("✨ Modo creativo activo", hero)
        self.hero_badge.setObjectName("heroBadge")
        self.hero_badge.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)

        text_column.addWidget(self.hero_badge)
        text_column.addWidget(hero_title)
        text_column.addWidget(hero_subtitle)
        text_column.addSpacing(12)
        text_column.addWidget(cta_button)
        text_column.addStretch()

        stats_column = QVBoxLayout()
        stats_column.setSpacing(12)

        highlight = QFrame(hero)
        highlight.setObjectName("heroHighlight")
        highlight_layout = QVBoxLayout(highlight)
        highlight_layout.setContentsMargins(18, 18, 18, 18)
        highlight_label = QLabel("Lista para:", highlight)
        highlight_label.setObjectName("highlightLabel")
        highlight_value = QLabel("Diagramar rápido\nGestionar temas\nExportar impecable", highlight)
        highlight_value.setObjectName("highlightValue")
        highlight_value.setWordWrap(True)
        highlight_layout.addWidget(highlight_label)
        highlight_layout.addWidget(highlight_value)

        stats_column.addWidget(highlight)
        stats_column.addStretch()

        hero_layout.addLayout(text_column, stretch=2)
        hero_layout.addLayout(stats_column, stretch=1)
        return hero

    def _build_cards(self):
        row = QHBoxLayout()
        row.setSpacing(16)

        card_temas = ActionCard(
            "📚",
            "Explorar temas",
            "Gestiona categorías, guarda listas y reutiliza tus colecciones favoritas.",
            self,
        )
        card_temas.clicked.connect(self.open_temas)

        card_quick = ActionCard(
            "⚡",
            "Generador exprés",
            "Pega palabras y obtén una sopa en segundos con los valores recomendados.",
            self,
        )
        card_quick.clicked.connect(self.open_quick_generator)

        card_editor = ActionCard(
            "🎨",
            "Ir al editor",
            "Diagramación al detalle, ajustes de layout y exportación a PDF o PNG.",
            self,
        )
        card_editor.clicked.connect(self.open_diagramacion)

        for card in (card_temas, card_quick, card_editor):
            row.addWidget(card, stretch=1)

        self._card_widgets = [card_temas, card_quick, card_editor]
        return row

    def _apply_style_sheet(self) -> None:
        self.setStyleSheet(
            """
            QWidget#homeRoot {
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:1,
                    stop:0 #101b3a,
                    stop:1 #1b2b52
                );
            }
            QFrame#heroFrame {
                border-radius: 20px;
                background: #ffffff;
            }
            QLabel#heroTitle {
                font-size: 28px;
                font-weight: 700;
                color: #0f172a;
            }
            QLabel#heroSubtitle {
                font-size: 15px;
                color: #475569;
            }
            QPushButton#heroButton {
                background-color: #4338ca;
                color: white;
                padding: 10px 26px;
                border-radius: 10px;
                font-size: 15px;
                font-weight: 600;
                border: none;
            }
            QPushButton#heroButton:hover {
                background-color: #3730a3;
            }
            QLabel#heroBadge {
                background-color: #f3e8ff;
                color: #6d28d9;
                border-radius: 999px;
                padding: 4px 14px;
                font-weight: 600;
            }
            QFrame#heroHighlight {
                background-color: #0f172a;
                border-radius: 14px;
            }
            QLabel#highlightLabel {
                color: #e2e8f0;
                font-size: 13px;
                letter-spacing: 1px;
                text-transform: uppercase;
            }
            QLabel#highlightValue {
                color: #f8fafc;
                font-size: 16px;
                font-weight: 600;
                line-height: 1.4;
            }
            QFrame#actionCard {
                background-color: rgba(255, 255, 255, 0.08);
                border-radius: 18px;
                border: 1px solid rgba(255, 255, 255, 0.12);
                color: #e2e8f0;
            }
            QFrame#actionCard[hover="true"] {
                background-color: rgba(15, 23, 42, 0.74);
                border: 1px solid rgba(255, 255, 255, 0.35);
            }
            QLabel#cardTitle {
                font-size: 18px;
                font-weight: 600;
            }
            QLabel#cardDescription {
                font-size: 14px;
                color: #cbd5f5;
            }
            """
        )

    def _start_badge_animation(self) -> None:
        if self._hero_badge_animation:
            if self._hero_badge_animation.state() == QAbstractAnimation.Running:
                return
            self._hero_badge_animation.start()
            return
        effect = QGraphicsOpacityEffect(self.hero_badge)
        self.hero_badge.setGraphicsEffect(effect)
        animation = QPropertyAnimation(effect, b"opacity", self)
        animation.setDuration(2000)
        animation.setStartValue(0.4)
        animation.setEndValue(1.0)
        animation.setEasingCurve(QEasingCurve.InOutSine)
        animation.setLoopCount(-1)
        animation.start()
        self._hero_badge_animation = animation

    def _stop_badge_animation(self) -> None:
        if self._hero_badge_animation:
            self._hero_badge_animation.stop()

    def showEvent(self, event) -> None:  # pylint: disable=missing-function-docstring
        super().showEvent(event)
        self._start_badge_animation()
        if not self._intro_started:
            self._intro_started = True
            QTimer.singleShot(60, self.play_intro)

    def hideEvent(self, event) -> None:  # pylint: disable=missing-function-docstring
        super().hideEvent(event)
        self._stop_badge_animation()
        self._clear_intro_group()

    def _ensure_opacity_effect(self, widget: QWidget) -> QGraphicsOpacityEffect:
        effect = self._widget_opacity_effects.get(widget)
        if effect is None:
            effect = QGraphicsOpacityEffect(widget)
            widget.setGraphicsEffect(effect)
            self._widget_opacity_effects[widget] = effect
        return effect

    def _clear_intro_group(self) -> None:
        if self._intro_group:
            self._intro_group.stop()
            self._intro_group.deleteLater()
            self._intro_group = None

    def _handle_intro_finished(self) -> None:
        self._intro_group = None

    def play_intro(self) -> None:
        """Animación de fade-in secuencial para hero y tarjetas."""
        if not self.isVisible():
            QTimer.singleShot(80, self.play_intro)
            return

        self._clear_intro_group()
        group = QParallelAnimationGroup(self)

        for index, widget in enumerate(self._animated_widgets):
            effect = self._ensure_opacity_effect(widget)
            effect.setOpacity(0.0)

            seq = QSequentialAnimationGroup(self)
            if index:
                seq.addAnimation(QPauseAnimation(index * 120, self))

            animation = QPropertyAnimation(effect, b"opacity", self)
            animation.setDuration(600)
            animation.setStartValue(0.0)
            animation.setEndValue(1.0)
            animation.setEasingCurve(QEasingCurve.OutCubic)
            seq.addAnimation(animation)
            group.addAnimation(seq)

        group.finished.connect(self._handle_intro_finished)
        group.start(QAbstractAnimation.DeleteWhenStopped)
        self._intro_group = group

    def restart_intro(self) -> None:
        """Permite relanzar las animaciones cuando se vuelve al inicio."""
        self._clear_intro_group()
        self._intro_started = False
        if not self.isVisible():
            QTimer.singleShot(120, self.restart_intro)
            return
        self._intro_started = True
        self.play_intro()


__all__ = ["HomeWidget"]

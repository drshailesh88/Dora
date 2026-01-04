"""Reusable UI components for Dora Desktop."""

import flet as ft
from .theme import Colors, Spacing, Typography, styled_card, severity_chip


class QueryInput(ft.UserControl):
    """Query input with voice button."""

    def __init__(
        self,
        on_submit: callable,
        on_voice: callable | None = None,
        placeholder: str = "Ask a medical question...",
    ):
        super().__init__()
        self.on_submit_callback = on_submit
        self.on_voice_callback = on_voice
        self.placeholder = placeholder
        self.text_field: ft.TextField | None = None

    def build(self):
        self.text_field = ft.TextField(
            hint_text=self.placeholder,
            expand=True,
            multiline=True,
            min_lines=1,
            max_lines=4,
            border_radius=12,
            border_color=Colors.BG_TERTIARY,
            focused_border_color=Colors.PRIMARY,
            on_submit=self._handle_submit,
            text_size=Typography.SIZE_MD,
            content_padding=ft.padding.all(Spacing.MD),
        )

        voice_button = ft.IconButton(
            icon=ft.icons.MIC,
            icon_color=Colors.PRIMARY,
            icon_size=24,
            tooltip="Voice input",
            on_click=self._handle_voice,
        ) if self.on_voice_callback else None

        submit_button = ft.IconButton(
            icon=ft.icons.SEND_ROUNDED,
            icon_color=Colors.TEXT_INVERSE,
            bgcolor=Colors.PRIMARY,
            icon_size=20,
            tooltip="Send",
            on_click=self._handle_submit,
        )

        controls = [self.text_field]
        if voice_button:
            controls.append(voice_button)
        controls.append(submit_button)

        return ft.Container(
            content=ft.Row(
                controls=controls,
                spacing=Spacing.SM,
                vertical_alignment=ft.CrossAxisAlignment.END,
            ),
            padding=Spacing.MD,
            bgcolor=Colors.BG_PRIMARY,
            border_radius=16,
            shadow=ft.BoxShadow(
                spread_radius=0,
                blur_radius=12,
                color=ft.colors.with_opacity(0.1, Colors.TEXT_PRIMARY),
                offset=ft.Offset(0, -4),
            ),
        )

    def _handle_submit(self, e):
        if self.text_field and self.text_field.value:
            self.on_submit_callback(self.text_field.value)
            self.text_field.value = ""
            self.text_field.update()

    def _handle_voice(self, e):
        if self.on_voice_callback:
            self.on_voice_callback()

    def set_text(self, text: str):
        """Set the input text."""
        if self.text_field:
            self.text_field.value = text
            self.text_field.update()


class AnswerCard(ft.UserControl):
    """Display a medical answer with citations."""

    def __init__(
        self,
        question: str,
        answer: str,
        confidence: str,
        citations: list[dict],
        warnings: list[str] | None = None,
    ):
        super().__init__()
        self.question = question
        self.answer = answer
        self.confidence = confidence
        self.citations = citations
        self.warnings = warnings or []

    def build(self):
        # Confidence indicator
        confidence_colors = {
            "high": Colors.SUCCESS,
            "medium": Colors.WARNING,
            "low": Colors.ERROR,
        }
        conf_color = confidence_colors.get(self.confidence.lower(), Colors.TEXT_SECONDARY)

        confidence_badge = ft.Container(
            content=ft.Row(
                controls=[
                    ft.Icon(ft.icons.VERIFIED, size=14, color=conf_color),
                    ft.Text(
                        f"{self.confidence.upper()} CONFIDENCE",
                        size=Typography.SIZE_XS,
                        weight=Typography.WEIGHT_SEMIBOLD,
                        color=conf_color,
                    ),
                ],
                spacing=4,
            ),
            padding=ft.padding.symmetric(horizontal=8, vertical=4),
            border_radius=4,
            bgcolor=ft.colors.with_opacity(0.1, conf_color),
        )

        # Warnings section
        warnings_section = None
        if self.warnings:
            warning_items = [
                ft.Row(
                    controls=[
                        ft.Icon(ft.icons.WARNING_AMBER, size=16, color=Colors.WARNING),
                        ft.Text(
                            w,
                            size=Typography.SIZE_SM,
                            color=Colors.TEXT_PRIMARY,
                            expand=True,
                        ),
                    ],
                    spacing=8,
                )
                for w in self.warnings
            ]
            warnings_section = ft.Container(
                content=ft.Column(controls=warning_items, spacing=8),
                bgcolor=ft.colors.with_opacity(0.1, Colors.WARNING),
                border_radius=8,
                padding=Spacing.MD,
                margin=ft.margin.only(bottom=Spacing.MD),
            )

        # Citations section
        citations_section = None
        if self.citations:
            citation_items = []
            for i, cite in enumerate(self.citations[:5], 1):
                citation_items.append(
                    ft.Container(
                        content=ft.Row(
                            controls=[
                                ft.Container(
                                    content=ft.Text(
                                        str(i),
                                        size=Typography.SIZE_XS,
                                        weight=Typography.WEIGHT_BOLD,
                                        color=Colors.PRIMARY,
                                    ),
                                    width=20,
                                    height=20,
                                    border_radius=10,
                                    bgcolor=ft.colors.with_opacity(0.1, Colors.PRIMARY),
                                    alignment=ft.alignment.center,
                                ),
                                ft.Column(
                                    controls=[
                                        ft.Text(
                                            cite.get("title", "Unknown Source"),
                                            size=Typography.SIZE_SM,
                                            weight=Typography.WEIGHT_MEDIUM,
                                            color=Colors.TEXT_PRIMARY,
                                        ),
                                        ft.Text(
                                            cite.get("source", ""),
                                            size=Typography.SIZE_XS,
                                            color=Colors.TEXT_SECONDARY,
                                        ),
                                    ],
                                    spacing=2,
                                    expand=True,
                                ),
                            ],
                            spacing=12,
                        ),
                        padding=ft.padding.symmetric(vertical=8),
                    )
                )

            citations_section = ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Text(
                            "SOURCES",
                            size=Typography.SIZE_XS,
                            weight=Typography.WEIGHT_SEMIBOLD,
                            color=Colors.TEXT_SECONDARY,
                        ),
                        ft.Column(controls=citation_items, spacing=0),
                    ],
                    spacing=8,
                ),
                border=ft.border.only(top=ft.BorderSide(1, Colors.BG_TERTIARY)),
                padding=ft.padding.only(top=Spacing.MD),
                margin=ft.margin.only(top=Spacing.MD),
            )

        # Main answer content
        content = ft.Column(
            controls=[
                # Question
                ft.Row(
                    controls=[
                        ft.Icon(ft.icons.HELP_OUTLINE, size=18, color=Colors.TEXT_SECONDARY),
                        ft.Text(
                            self.question,
                            size=Typography.SIZE_SM,
                            color=Colors.TEXT_SECONDARY,
                            italic=True,
                            expand=True,
                        ),
                    ],
                    spacing=8,
                ),
                ft.Divider(height=1, color=Colors.BG_TERTIARY),

                # Confidence badge
                ft.Row(
                    controls=[confidence_badge],
                    alignment=ft.MainAxisAlignment.END,
                ),

                # Warnings if any
                warnings_section if warnings_section else ft.Container(),

                # Answer
                ft.Text(
                    self.answer,
                    size=Typography.SIZE_MD,
                    color=Colors.TEXT_PRIMARY,
                    selectable=True,
                ),

                # Citations
                citations_section if citations_section else ft.Container(),
            ],
            spacing=Spacing.SM,
        )

        return styled_card(content)


class PatientContextBanner(ft.UserControl):
    """Banner showing current patient context."""

    def __init__(
        self,
        patient_name: str,
        patient_id: int,
        on_clear: callable,
    ):
        super().__init__()
        self.patient_name = patient_name
        self.patient_id = patient_id
        self.on_clear = on_clear

    def build(self):
        return ft.Container(
            content=ft.Row(
                controls=[
                    ft.Icon(ft.icons.PERSON, size=18, color=Colors.PRIMARY),
                    ft.Text(
                        f"Patient Context: {self.patient_name}",
                        size=Typography.SIZE_SM,
                        weight=Typography.WEIGHT_MEDIUM,
                        color=Colors.PRIMARY,
                    ),
                    ft.Text(
                        f"(ID: {self.patient_id})",
                        size=Typography.SIZE_XS,
                        color=Colors.TEXT_SECONDARY,
                    ),
                    ft.Container(expand=True),
                    ft.IconButton(
                        icon=ft.icons.CLOSE,
                        icon_size=16,
                        icon_color=Colors.TEXT_SECONDARY,
                        tooltip="Clear patient context",
                        on_click=lambda _: self.on_clear(),
                    ),
                ],
                spacing=8,
            ),
            bgcolor=ft.colors.with_opacity(0.1, Colors.PRIMARY),
            border_radius=8,
            padding=ft.padding.symmetric(horizontal=Spacing.MD, vertical=Spacing.SM),
        )


class DrugInteractionCard(ft.UserControl):
    """Display drug interaction warning."""

    def __init__(
        self,
        drug1: str,
        drug2: str,
        severity: str,
        description: str,
        management: str,
    ):
        super().__init__()
        self.drug1 = drug1
        self.drug2 = drug2
        self.severity = severity
        self.description = description
        self.management = management

    def build(self):
        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Row(
                        controls=[
                            severity_chip(self.severity),
                            ft.Text(
                                f"{self.drug1} + {self.drug2}",
                                size=Typography.SIZE_MD,
                                weight=Typography.WEIGHT_SEMIBOLD,
                                color=Colors.TEXT_PRIMARY,
                            ),
                        ],
                        spacing=Spacing.SM,
                    ),
                    ft.Text(
                        self.description,
                        size=Typography.SIZE_SM,
                        color=Colors.TEXT_PRIMARY,
                    ),
                    ft.Container(
                        content=ft.Row(
                            controls=[
                                ft.Icon(ft.icons.MEDICAL_SERVICES, size=14, color=Colors.INFO),
                                ft.Text(
                                    f"Management: {self.management}",
                                    size=Typography.SIZE_SM,
                                    color=Colors.INFO,
                                    italic=True,
                                ),
                            ],
                            spacing=8,
                        ),
                        bgcolor=ft.colors.with_opacity(0.1, Colors.INFO),
                        border_radius=4,
                        padding=Spacing.SM,
                    ),
                ],
                spacing=Spacing.SM,
            ),
            border=ft.border.all(1, Colors.BG_TERTIARY),
            border_radius=8,
            padding=Spacing.MD,
        )


class StatusIndicator(ft.UserControl):
    """Status indicator with label."""

    def __init__(self, label: str, status: str, tooltip: str = ""):
        super().__init__()
        self.label = label
        self.status = status  # "online", "offline", "warning"
        self.tooltip = tooltip

    def build(self):
        status_colors = {
            "online": Colors.SUCCESS,
            "offline": Colors.ERROR,
            "warning": Colors.WARNING,
        }
        color = status_colors.get(self.status, Colors.TEXT_SECONDARY)

        return ft.Tooltip(
            message=self.tooltip,
            content=ft.Row(
                controls=[
                    ft.Container(
                        width=8,
                        height=8,
                        border_radius=4,
                        bgcolor=color,
                    ),
                    ft.Text(
                        self.label,
                        size=Typography.SIZE_XS,
                        color=Colors.TEXT_SECONDARY,
                    ),
                ],
                spacing=6,
            ),
        )


class SidebarItem(ft.UserControl):
    """Sidebar navigation item."""

    def __init__(
        self,
        icon: str,
        label: str,
        selected: bool = False,
        on_click: callable = None,
        badge: int | None = None,
    ):
        super().__init__()
        self.icon = icon
        self.label = label
        self.selected = selected
        self.on_click_callback = on_click
        self.badge = badge

    def build(self):
        bg_color = Colors.PRIMARY if self.selected else ft.colors.TRANSPARENT
        text_color = Colors.TEXT_INVERSE if self.selected else Colors.TEXT_SECONDARY
        icon_color = Colors.TEXT_INVERSE if self.selected else Colors.TEXT_SECONDARY

        badge_control = None
        if self.badge and self.badge > 0:
            badge_control = ft.Container(
                content=ft.Text(
                    str(self.badge) if self.badge < 100 else "99+",
                    size=10,
                    weight=Typography.WEIGHT_BOLD,
                    color=Colors.TEXT_INVERSE,
                ),
                bgcolor=Colors.ERROR,
                border_radius=10,
                padding=ft.padding.symmetric(horizontal=6, vertical=2),
            )

        return ft.Container(
            content=ft.Row(
                controls=[
                    ft.Icon(self.icon, size=20, color=icon_color),
                    ft.Text(
                        self.label,
                        size=Typography.SIZE_SM,
                        weight=Typography.WEIGHT_MEDIUM if self.selected else Typography.WEIGHT_REGULAR,
                        color=text_color,
                        expand=True,
                    ),
                    badge_control if badge_control else ft.Container(),
                ],
                spacing=12,
            ),
            bgcolor=bg_color,
            border_radius=8,
            padding=ft.padding.symmetric(horizontal=12, vertical=10),
            on_click=lambda _: self.on_click_callback() if self.on_click_callback else None,
            ink=True,
        )

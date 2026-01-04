"""Dora Desktop Theme - Apple-inspired medical UI."""

import flet as ft

# Color Palette - Medical Professional Theme
class Colors:
    """Dora color scheme."""

    # Primary
    PRIMARY = "#0066CC"  # Medical blue
    PRIMARY_LIGHT = "#4D94FF"
    PRIMARY_DARK = "#004C99"

    # Backgrounds
    BG_PRIMARY = "#FFFFFF"
    BG_SECONDARY = "#F5F7FA"
    BG_TERTIARY = "#E8ECF0"
    BG_DARK = "#1C1C1E"

    # Text
    TEXT_PRIMARY = "#1C1C1E"
    TEXT_SECONDARY = "#6B7280"
    TEXT_TERTIARY = "#9CA3AF"
    TEXT_INVERSE = "#FFFFFF"

    # Status
    SUCCESS = "#10B981"
    WARNING = "#F59E0B"
    ERROR = "#EF4444"
    INFO = "#3B82F6"

    # Severity (Drug Interactions)
    CONTRAINDICATED = "#DC2626"
    SEVERE = "#EA580C"
    MODERATE = "#D97706"
    MILD = "#65A30D"

    # Accents
    ACCENT_PURPLE = "#8B5CF6"
    ACCENT_TEAL = "#14B8A6"


class Spacing:
    """Consistent spacing values."""

    XS = 4
    SM = 8
    MD = 16
    LG = 24
    XL = 32
    XXL = 48


class Typography:
    """Text styles."""

    # Sizes
    SIZE_XS = 11
    SIZE_SM = 13
    SIZE_MD = 15
    SIZE_LG = 17
    SIZE_XL = 20
    SIZE_XXL = 28
    SIZE_DISPLAY = 34

    # Weights
    WEIGHT_REGULAR = ft.FontWeight.W_400
    WEIGHT_MEDIUM = ft.FontWeight.W_500
    WEIGHT_SEMIBOLD = ft.FontWeight.W_600
    WEIGHT_BOLD = ft.FontWeight.W_700


def get_theme(dark_mode: bool = False) -> ft.Theme:
    """Get Flet theme configuration."""

    if dark_mode:
        color_scheme = ft.ColorScheme(
            primary=Colors.PRIMARY_LIGHT,
            on_primary=Colors.TEXT_INVERSE,
            background=Colors.BG_DARK,
            surface="#2C2C2E",
            on_surface=Colors.TEXT_INVERSE,
        )
    else:
        color_scheme = ft.ColorScheme(
            primary=Colors.PRIMARY,
            on_primary=Colors.TEXT_INVERSE,
            background=Colors.BG_PRIMARY,
            surface=Colors.BG_SECONDARY,
            on_surface=Colors.TEXT_PRIMARY,
        )

    return ft.Theme(
        color_scheme=color_scheme,
        font_family="SF Pro Display",
        visual_density=ft.VisualDensity.COMFORTABLE,
    )


# Reusable styled components
def styled_card(content: ft.Control, **kwargs) -> ft.Container:
    """Create a styled card container."""
    return ft.Container(
        content=content,
        bgcolor=Colors.BG_PRIMARY,
        border_radius=12,
        padding=Spacing.MD,
        shadow=ft.BoxShadow(
            spread_radius=0,
            blur_radius=8,
            color=ft.colors.with_opacity(0.08, Colors.TEXT_PRIMARY),
            offset=ft.Offset(0, 2),
        ),
        **kwargs,
    )


def styled_button(
    text: str,
    on_click=None,
    primary: bool = True,
    icon: str | None = None,
    disabled: bool = False,
) -> ft.ElevatedButton:
    """Create a styled button."""
    return ft.ElevatedButton(
        text=text,
        icon=icon,
        on_click=on_click,
        disabled=disabled,
        style=ft.ButtonStyle(
            color=Colors.TEXT_INVERSE if primary else Colors.PRIMARY,
            bgcolor=Colors.PRIMARY if primary else Colors.BG_SECONDARY,
            padding=ft.padding.symmetric(horizontal=Spacing.LG, vertical=Spacing.MD),
            shape=ft.RoundedRectangleBorder(radius=8),
        ),
    )


def styled_text_field(
    label: str,
    hint: str = "",
    multiline: bool = False,
    password: bool = False,
    on_change=None,
    on_submit=None,
) -> ft.TextField:
    """Create a styled text field."""
    return ft.TextField(
        label=label,
        hint_text=hint,
        multiline=multiline,
        password=password,
        on_change=on_change,
        on_submit=on_submit,
        border_radius=8,
        border_color=Colors.BG_TERTIARY,
        focused_border_color=Colors.PRIMARY,
        cursor_color=Colors.PRIMARY,
        text_size=Typography.SIZE_MD,
    )


def severity_chip(severity: str) -> ft.Container:
    """Create a severity indicator chip."""
    colors = {
        "contraindicated": (Colors.CONTRAINDICATED, "CONTRAINDICATED"),
        "severe": (Colors.SEVERE, "SEVERE"),
        "moderate": (Colors.MODERATE, "MODERATE"),
        "mild": (Colors.MILD, "MILD"),
    }

    color, label = colors.get(severity.lower(), (Colors.TEXT_SECONDARY, severity.upper()))

    return ft.Container(
        content=ft.Text(
            label,
            size=Typography.SIZE_XS,
            weight=Typography.WEIGHT_SEMIBOLD,
            color=Colors.TEXT_INVERSE,
        ),
        bgcolor=color,
        border_radius=4,
        padding=ft.padding.symmetric(horizontal=8, vertical=4),
    )

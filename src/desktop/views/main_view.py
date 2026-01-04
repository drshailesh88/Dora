"""Main View - App shell with navigation."""

import flet as ft

from ..theme import Colors, Spacing, Typography, get_theme
from ..components import SidebarItem, StatusIndicator
from ..services import DoraAPIClient, StateManager
from .query_view import QueryView
from .drugs_view import DrugsView
from .history_view import HistoryView
from .settings_view import SettingsView
from .calculators_view import CalculatorsView
from .protocols_view import ProtocolsView


class MainView(ft.UserControl):
    """Main application shell with sidebar navigation."""

    def __init__(self, api_client: DoraAPIClient, state_manager: StateManager):
        super().__init__()
        self.api = api_client
        self.state = state_manager
        self.current_view = "query"
        self.content_area: ft.Container | None = None

        # Create views
        self.views = {
            "query": QueryView(api_client, state_manager),
            "drugs": DrugsView(api_client, state_manager),
            "calculators": CalculatorsView(api_client, state_manager),
            "protocols": ProtocolsView(api_client, state_manager),
            "history": HistoryView(state_manager, on_rerun=self._rerun_query),
            "settings": SettingsView(api_client, state_manager),
        }

    def build(self):
        # Subscribe to state changes
        self.state.subscribe(self._on_state_change)

        # Sidebar
        sidebar = self._build_sidebar()

        # Content area
        self.content_area = ft.Container(
            content=self.views["query"],
            expand=True,
            bgcolor=Colors.BG_SECONDARY,
        )

        return ft.Row(
            controls=[
                sidebar,
                ft.VerticalDivider(width=1, color=Colors.BG_TERTIARY),
                self.content_area,
            ],
            spacing=0,
            expand=True,
        )

    def _build_sidebar(self) -> ft.Container:
        """Build the sidebar navigation."""
        # Logo
        logo = ft.Container(
            content=ft.Row(
                controls=[
                    ft.Container(
                        content=ft.Icon(
                            ft.icons.LOCAL_HOSPITAL,
                            color=Colors.TEXT_INVERSE,
                            size=20,
                        ),
                        width=36,
                        height=36,
                        border_radius=8,
                        bgcolor=Colors.PRIMARY,
                        alignment=ft.alignment.center,
                    ),
                    ft.Text(
                        "Dora",
                        size=Typography.SIZE_XL,
                        weight=Typography.WEIGHT_BOLD,
                        color=Colors.TEXT_PRIMARY,
                    ),
                ],
                spacing=Spacing.SM,
            ),
            padding=Spacing.MD,
        )

        # Navigation items
        nav_items = ft.Column(
            controls=[
                SidebarItem(
                    icon=ft.icons.CHAT_BUBBLE_OUTLINE,
                    label="Query",
                    selected=self.current_view == "query",
                    on_click=lambda: self._navigate("query"),
                ),
                SidebarItem(
                    icon=ft.icons.MEDICATION,
                    label="Drug Interactions",
                    selected=self.current_view == "drugs",
                    on_click=lambda: self._navigate("drugs"),
                ),
                SidebarItem(
                    icon=ft.icons.CALCULATE,
                    label="Calculators",
                    selected=self.current_view == "calculators",
                    on_click=lambda: self._navigate("calculators"),
                ),
                SidebarItem(
                    icon=ft.icons.CHECKLIST,
                    label="Protocols",
                    selected=self.current_view == "protocols",
                    on_click=lambda: self._navigate("protocols"),
                ),
                SidebarItem(
                    icon=ft.icons.HISTORY,
                    label="History",
                    selected=self.current_view == "history",
                    on_click=lambda: self._navigate("history"),
                    badge=len(self.state.state.query_history),
                ),
            ],
            spacing=Spacing.XS,
        )

        # Status indicators
        status_section = ft.Container(
            content=ft.Column(
                controls=[
                    StatusIndicator(
                        label="API",
                        status="online" if self.state.state.api_connected else "offline",
                        tooltip="Backend connection status",
                    ),
                    StatusIndicator(
                        label="LLM",
                        status="online",
                        tooltip="Language model status",
                    ),
                    StatusIndicator(
                        label="Voice",
                        status="online" if self.state.state.voice_enabled else "offline",
                        tooltip="Voice assistant status",
                    ),
                ],
                spacing=Spacing.XS,
            ),
            padding=ft.padding.symmetric(horizontal=Spacing.MD),
        )

        # License badge
        tier = self.state.state.license_tier.upper()
        tier_colors = {
            "FREE": Colors.TEXT_SECONDARY,
            "ESSENTIAL": Colors.INFO,
            "PROFESSIONAL": Colors.PRIMARY,
            "CLINIC": Colors.ACCENT_PURPLE,
            "ENTERPRISE": Colors.SUCCESS,
        }
        tier_color = tier_colors.get(tier, Colors.TEXT_SECONDARY)

        license_badge = ft.Container(
            content=ft.Row(
                controls=[
                    ft.Icon(ft.icons.VERIFIED, size=14, color=tier_color),
                    ft.Text(
                        tier,
                        size=Typography.SIZE_XS,
                        weight=Typography.WEIGHT_SEMIBOLD,
                        color=tier_color,
                    ),
                ],
                spacing=4,
                alignment=ft.MainAxisAlignment.CENTER,
            ),
            bgcolor=ft.colors.with_opacity(0.1, tier_color),
            border_radius=4,
            padding=ft.padding.symmetric(horizontal=12, vertical=6),
        )

        # Settings button
        settings_item = SidebarItem(
            icon=ft.icons.SETTINGS,
            label="Settings",
            selected=self.current_view == "settings",
            on_click=lambda: self._navigate("settings"),
        )

        return ft.Container(
            content=ft.Column(
                controls=[
                    logo,
                    ft.Divider(height=1, color=Colors.BG_TERTIARY),
                    ft.Container(
                        content=nav_items,
                        padding=Spacing.SM,
                    ),
                    ft.Container(expand=True),
                    status_section,
                    ft.Container(height=Spacing.MD),
                    ft.Container(
                        content=license_badge,
                        alignment=ft.alignment.center,
                    ),
                    ft.Container(height=Spacing.SM),
                    ft.Container(
                        content=settings_item,
                        padding=Spacing.SM,
                    ),
                ],
            ),
            width=220,
            bgcolor=Colors.BG_PRIMARY,
        )

    def _navigate(self, view_name: str):
        """Navigate to a different view."""
        if view_name not in self.views:
            return

        self.current_view = view_name
        self.content_area.content = self.views[view_name]
        self.content_area.update()

        # Rebuild sidebar to update selection
        self.update()

    def _rerun_query(self, question: str):
        """Re-run a query from history."""
        self._navigate("query")
        # Set the question in the query input
        query_view = self.views["query"]
        # TODO: Set question in query input

    def _on_state_change(self, state):
        """Handle state changes."""
        self.update()

    def will_unmount(self):
        """Cleanup on unmount."""
        self.state.unsubscribe(self._on_state_change)

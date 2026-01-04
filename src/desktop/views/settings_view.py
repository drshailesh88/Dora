"""Settings View - App configuration."""

import flet as ft

from ..theme import Colors, Spacing, Typography, styled_card, styled_button
from ..services import DoraAPIClient, StateManager


class SettingsView(ft.UserControl):
    """Application settings interface."""

    def __init__(self, api_client: DoraAPIClient, state_manager: StateManager):
        super().__init__()
        self.api = api_client
        self.state = state_manager

    def build(self):
        # License section
        license_section = self._build_license_section()

        # API section
        api_section = self._build_api_section()

        # Appearance section
        appearance_section = self._build_appearance_section()

        # Voice section
        voice_section = self._build_voice_section()

        # About section
        about_section = self._build_about_section()

        return ft.Column(
            controls=[
                # Header
                ft.Container(
                    content=ft.Text(
                        "Settings",
                        size=Typography.SIZE_XL,
                        weight=Typography.WEIGHT_BOLD,
                        color=Colors.TEXT_PRIMARY,
                    ),
                    padding=Spacing.MD,
                ),

                # Settings sections
                ft.ListView(
                    controls=[
                        license_section,
                        api_section,
                        appearance_section,
                        voice_section,
                        about_section,
                    ],
                    expand=True,
                    spacing=Spacing.MD,
                    padding=Spacing.MD,
                ),
            ],
            expand=True,
        )

    def _build_license_section(self) -> ft.Control:
        """Build license settings section."""
        license_status = self.state.state.license_tier.upper()
        is_licensed = self.state.state.is_licensed

        status_color = Colors.SUCCESS if is_licensed else Colors.WARNING

        license_key_field = ft.TextField(
            label="License Key",
            hint_text="Enter your license key",
            password=True,
            can_reveal_password=True,
            border_radius=8,
            expand=True,
        )

        return styled_card(
            ft.Column(
                controls=[
                    ft.Row(
                        controls=[
                            ft.Icon(ft.icons.VERIFIED_USER, color=Colors.PRIMARY, size=24),
                            ft.Text(
                                "License",
                                size=Typography.SIZE_LG,
                                weight=Typography.WEIGHT_SEMIBOLD,
                                color=Colors.TEXT_PRIMARY,
                            ),
                        ],
                        spacing=Spacing.SM,
                    ),
                    ft.Divider(height=1, color=Colors.BG_TERTIARY),

                    # Current status
                    ft.Row(
                        controls=[
                            ft.Text(
                                "Status:",
                                size=Typography.SIZE_SM,
                                color=Colors.TEXT_SECONDARY,
                            ),
                            ft.Container(
                                content=ft.Text(
                                    license_status,
                                    size=Typography.SIZE_XS,
                                    weight=Typography.WEIGHT_SEMIBOLD,
                                    color=Colors.TEXT_INVERSE,
                                ),
                                bgcolor=status_color,
                                border_radius=4,
                                padding=ft.padding.symmetric(horizontal=8, vertical=4),
                            ),
                        ],
                        spacing=Spacing.SM,
                    ),

                    # License key input
                    ft.Row(
                        controls=[
                            license_key_field,
                            styled_button(
                                text="Activate",
                                on_click=lambda _: self._activate_license(license_key_field.value),
                            ),
                        ],
                        spacing=Spacing.SM,
                    ),

                    # Pricing link
                    ft.TextButton(
                        text="View pricing and features →",
                        style=ft.ButtonStyle(color=Colors.PRIMARY),
                        on_click=lambda _: self.page.launch_url("https://docassist.in/pricing"),
                    ),
                ],
                spacing=Spacing.MD,
            ),
        )

    def _build_api_section(self) -> ft.Control:
        """Build API settings section."""
        api_status = "online" if self.state.state.api_connected else "offline"
        status_color = Colors.SUCCESS if self.state.state.api_connected else Colors.ERROR

        api_url_field = ft.TextField(
            label="API URL",
            value=self.state.state.api_url,
            border_radius=8,
            expand=True,
        )

        return styled_card(
            ft.Column(
                controls=[
                    ft.Row(
                        controls=[
                            ft.Icon(ft.icons.API, color=Colors.PRIMARY, size=24),
                            ft.Text(
                                "API Connection",
                                size=Typography.SIZE_LG,
                                weight=Typography.WEIGHT_SEMIBOLD,
                                color=Colors.TEXT_PRIMARY,
                            ),
                        ],
                        spacing=Spacing.SM,
                    ),
                    ft.Divider(height=1, color=Colors.BG_TERTIARY),

                    # Status
                    ft.Row(
                        controls=[
                            ft.Container(
                                width=10,
                                height=10,
                                border_radius=5,
                                bgcolor=status_color,
                            ),
                            ft.Text(
                                f"API {api_status}",
                                size=Typography.SIZE_SM,
                                color=Colors.TEXT_SECONDARY,
                            ),
                        ],
                        spacing=Spacing.SM,
                    ),

                    # API URL
                    ft.Row(
                        controls=[
                            api_url_field,
                            ft.IconButton(
                                icon=ft.icons.REFRESH,
                                tooltip="Test connection",
                                on_click=lambda _: self._test_connection(api_url_field.value),
                            ),
                        ],
                        spacing=Spacing.SM,
                    ),

                    # Offline mode toggle
                    ft.Row(
                        controls=[
                            ft.Text(
                                "Offline Mode",
                                size=Typography.SIZE_SM,
                                color=Colors.TEXT_PRIMARY,
                            ),
                            ft.Switch(
                                value=self.state.state.offline_mode,
                                active_color=Colors.PRIMARY,
                                on_change=lambda e: self._toggle_offline(e.control.value),
                            ),
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    ),
                ],
                spacing=Spacing.MD,
            ),
        )

    def _build_appearance_section(self) -> ft.Control:
        """Build appearance settings section."""
        return styled_card(
            ft.Column(
                controls=[
                    ft.Row(
                        controls=[
                            ft.Icon(ft.icons.PALETTE, color=Colors.PRIMARY, size=24),
                            ft.Text(
                                "Appearance",
                                size=Typography.SIZE_LG,
                                weight=Typography.WEIGHT_SEMIBOLD,
                                color=Colors.TEXT_PRIMARY,
                            ),
                        ],
                        spacing=Spacing.SM,
                    ),
                    ft.Divider(height=1, color=Colors.BG_TERTIARY),

                    # Dark mode toggle
                    ft.Row(
                        controls=[
                            ft.Row(
                                controls=[
                                    ft.Icon(
                                        ft.icons.DARK_MODE,
                                        size=20,
                                        color=Colors.TEXT_SECONDARY,
                                    ),
                                    ft.Text(
                                        "Dark Mode",
                                        size=Typography.SIZE_SM,
                                        color=Colors.TEXT_PRIMARY,
                                    ),
                                ],
                                spacing=Spacing.SM,
                            ),
                            ft.Switch(
                                value=self.state.state.dark_mode,
                                active_color=Colors.PRIMARY,
                                on_change=lambda e: self._toggle_dark_mode(e.control.value),
                            ),
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    ),
                ],
                spacing=Spacing.MD,
            ),
        )

    def _build_voice_section(self) -> ft.Control:
        """Build voice settings section."""
        return styled_card(
            ft.Column(
                controls=[
                    ft.Row(
                        controls=[
                            ft.Icon(ft.icons.MIC, color=Colors.PRIMARY, size=24),
                            ft.Text(
                                "Voice Assistant",
                                size=Typography.SIZE_LG,
                                weight=Typography.WEIGHT_SEMIBOLD,
                                color=Colors.TEXT_PRIMARY,
                            ),
                        ],
                        spacing=Spacing.SM,
                    ),
                    ft.Divider(height=1, color=Colors.BG_TERTIARY),

                    # Voice enabled toggle
                    ft.Row(
                        controls=[
                            ft.Text(
                                "Enable Voice",
                                size=Typography.SIZE_SM,
                                color=Colors.TEXT_PRIMARY,
                            ),
                            ft.Switch(
                                value=self.state.state.voice_enabled,
                                active_color=Colors.PRIMARY,
                                on_change=lambda e: self._toggle_voice(e.control.value),
                            ),
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    ),

                    # Wake word
                    ft.Row(
                        controls=[
                            ft.Text(
                                "Wake Word:",
                                size=Typography.SIZE_SM,
                                color=Colors.TEXT_SECONDARY,
                            ),
                            ft.Text(
                                '"Hey DocAssist"',
                                size=Typography.SIZE_SM,
                                color=Colors.PRIMARY,
                                weight=Typography.WEIGHT_MEDIUM,
                            ),
                        ],
                        spacing=Spacing.SM,
                    ),
                ],
                spacing=Spacing.MD,
            ),
        )

    def _build_about_section(self) -> ft.Control:
        """Build about section."""
        return styled_card(
            ft.Column(
                controls=[
                    ft.Row(
                        controls=[
                            ft.Icon(ft.icons.INFO_OUTLINE, color=Colors.PRIMARY, size=24),
                            ft.Text(
                                "About",
                                size=Typography.SIZE_LG,
                                weight=Typography.WEIGHT_SEMIBOLD,
                                color=Colors.TEXT_PRIMARY,
                            ),
                        ],
                        spacing=Spacing.SM,
                    ),
                    ft.Divider(height=1, color=Colors.BG_TERTIARY),

                    ft.Text(
                        "Dora - Medical Knowledge Platform",
                        size=Typography.SIZE_MD,
                        weight=Typography.WEIGHT_MEDIUM,
                        color=Colors.TEXT_PRIMARY,
                    ),
                    ft.Text(
                        "Version 0.1.0",
                        size=Typography.SIZE_SM,
                        color=Colors.TEXT_SECONDARY,
                    ),
                    ft.Text(
                        "© 2026 DocAssist. All rights reserved.",
                        size=Typography.SIZE_XS,
                        color=Colors.TEXT_TERTIARY,
                    ),

                    ft.Row(
                        controls=[
                            ft.TextButton(
                                text="Documentation",
                                style=ft.ButtonStyle(color=Colors.PRIMARY),
                            ),
                            ft.TextButton(
                                text="Privacy Policy",
                                style=ft.ButtonStyle(color=Colors.PRIMARY),
                            ),
                            ft.TextButton(
                                text="Terms of Service",
                                style=ft.ButtonStyle(color=Colors.PRIMARY),
                            ),
                        ],
                        spacing=Spacing.XS,
                    ),
                ],
                spacing=Spacing.SM,
            ),
        )

    async def _activate_license(self, license_key: str):
        """Activate license key."""
        if not license_key:
            return

        result = await self.api.activate_license(license_key)

        if result.get("success"):
            # Refresh license status
            status = await self.api.get_license_status()
            self.state.update(
                is_licensed=True,
                license_tier=status.get("tier", "essential"),
            )

            # Show success
            self.page.snack_bar = ft.SnackBar(
                content=ft.Text("License activated successfully!"),
                bgcolor=Colors.SUCCESS,
            )
            self.page.snack_bar.open = True
            self.page.update()
        else:
            # Show error
            self.page.snack_bar = ft.SnackBar(
                content=ft.Text(result.get("error", "Failed to activate license")),
                bgcolor=Colors.ERROR,
            )
            self.page.snack_bar.open = True
            self.page.update()

    async def _test_connection(self, api_url: str):
        """Test API connection."""
        self.api.base_url = api_url
        result = await self.api.health_check()

        if result.get("status") == "healthy":
            self.state.update(api_connected=True, api_url=api_url)

            self.page.snack_bar = ft.SnackBar(
                content=ft.Text("API connection successful!"),
                bgcolor=Colors.SUCCESS,
            )
        else:
            self.state.update(api_connected=False)

            self.page.snack_bar = ft.SnackBar(
                content=ft.Text(f"Connection failed: {result.get('error', 'Unknown error')}"),
                bgcolor=Colors.ERROR,
            )

        self.page.snack_bar.open = True
        self.page.update()

    def _toggle_offline(self, value: bool):
        """Toggle offline mode."""
        self.state.update(offline_mode=value)

    def _toggle_dark_mode(self, value: bool):
        """Toggle dark mode."""
        self.state.update(dark_mode=value)
        # Would need to update app theme here

    def _toggle_voice(self, value: bool):
        """Toggle voice assistant."""
        self.state.update(voice_enabled=value)

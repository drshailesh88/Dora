"""Dora Desktop Application - Main entry point."""

import asyncio
import flet as ft

from .theme import Colors, Spacing, Typography, get_theme
from .services import DoraAPIClient, StateManager
from .views import MainView


class DoraApp:
    """
    Dora Desktop Application.

    A premium medical knowledge platform for doctors.
    """

    def __init__(self):
        self.api_client = DoraAPIClient()
        self.state_manager = StateManager()
        self.page: ft.Page | None = None

    async def initialize(self):
        """Initialize app - check API and license."""
        # Check API connection
        health = await self.api_client.health_check()
        self.state_manager.update(
            api_connected=health.get("status") == "healthy"
        )

        # Check license status
        license_status = await self.api_client.get_license_status()
        if license_status.get("status") != "error":
            self.state_manager.update(
                is_licensed=license_status.get("status") in ["active", "grace_period"],
                license_tier=license_status.get("tier", "free") or "free",
            )

    def main(self, page: ft.Page):
        """Main entry point for Flet app."""
        self.page = page

        # Configure page
        page.title = "Dora - Medical Knowledge Platform"
        page.theme = get_theme(dark_mode=False)
        page.theme_mode = ft.ThemeMode.LIGHT
        page.padding = 0
        page.spacing = 0

        # Window settings
        page.window.width = 1200
        page.window.height = 800
        page.window.min_width = 900
        page.window.min_height = 600
        page.window.title_bar_hidden = False

        # Show loading screen
        loading = ft.Container(
            content=ft.Column(
                controls=[
                    ft.ProgressRing(
                        width=48,
                        height=48,
                        stroke_width=3,
                        color=Colors.PRIMARY,
                    ),
                    ft.Container(height=Spacing.MD),
                    ft.Text(
                        "Loading Dora...",
                        size=Typography.SIZE_MD,
                        color=Colors.TEXT_SECONDARY,
                    ),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            alignment=ft.alignment.center,
            expand=True,
        )
        page.add(loading)

        # Initialize in background
        async def init_and_show():
            await self.initialize()

            # Remove loading, show main view
            page.controls.clear()
            main_view = MainView(self.api_client, self.state_manager)
            page.add(main_view)
            page.update()

        # Run initialization
        page.run_task(init_and_show)

    async def cleanup(self):
        """Cleanup resources."""
        await self.api_client.close()


def run_app():
    """Run the Dora desktop application."""
    app = DoraApp()

    ft.app(
        target=app.main,
        assets_dir="assets",
    )


# Alternative: Run as web app
def run_web_app(port: int = 8080):
    """Run as web application."""
    app = DoraApp()

    ft.app(
        target=app.main,
        view=ft.AppView.WEB_BROWSER,
        port=port,
    )


if __name__ == "__main__":
    run_app()

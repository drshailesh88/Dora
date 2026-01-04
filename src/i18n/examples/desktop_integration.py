"""
Example: Flet desktop app integration with i18n.

This shows how to use the translation system in Flet applications
to create multilingual desktop UIs.
"""

import flet as ft
from src.i18n import Translator, get_translator


class MultilingualApp:
    """Example Flet app with multilingual support."""

    def __init__(self):
        self.translator = get_translator("en")  # Default to English
        self.current_locale = "en"

    def main(self, page: ft.Page):
        """Main app entry point."""
        page.title = self.translator.translate("app.name")
        page.theme_mode = ft.ThemeMode.LIGHT

        # Language selector dropdown
        def on_language_change(e):
            self.current_locale = e.control.value
            self.translator.set_locale(self.current_locale)
            self.update_ui(page)

        language_dropdown = ft.Dropdown(
            width=150,
            value=self.current_locale,
            options=[
                ft.dropdown.Option("en", "English"),
                ft.dropdown.Option("hi", "हिंदी (Hindi)"),
                ft.dropdown.Option("mr", "मराठी (Marathi)"),
                ft.dropdown.Option("ta", "தமிழ் (Tamil)"),
                ft.dropdown.Option("te", "తెలుగు (Telugu)"),
                ft.dropdown.Option("bn", "বাংলা (Bengali)"),
            ],
            on_change=on_language_change,
        )

        # Create UI elements
        self.welcome_text = ft.Text(
            self.translator.translate("messages.welcome", params={"name": "Doctor"}),
            size=24,
            weight=ft.FontWeight.BOLD,
        )

        self.search_field = ft.TextField(
            hint_text=self.translator.translate("search.search_placeholder"),
            width=400,
            autofocus=True,
        )

        self.submit_button = ft.ElevatedButton(
            text=self.translator.translate("buttons.submit"),
            on_click=self.on_submit,
        )

        self.result_text = ft.Text("", size=16)

        # Navigation rail
        self.nav_rail = ft.NavigationRail(
            selected_index=0,
            label_type=ft.NavigationRailLabelType.ALL,
            min_width=100,
            min_extended_width=200,
            destinations=[
                ft.NavigationRailDestination(
                    icon=ft.icons.HOME_OUTLINED,
                    selected_icon=ft.icons.HOME,
                    label=self.translator.translate("nav.home"),
                ),
                ft.NavigationRailDestination(
                    icon=ft.icons.SEARCH_OUTLINED,
                    selected_icon=ft.icons.SEARCH,
                    label=self.translator.translate("nav.search"),
                ),
                ft.NavigationRailDestination(
                    icon=ft.icons.LIBRARY_BOOKS_OUTLINED,
                    selected_icon=ft.icons.LIBRARY_BOOKS,
                    label=self.translator.translate("nav.library"),
                ),
                ft.NavigationRailDestination(
                    icon=ft.icons.FAVORITE_OUTLINED,
                    selected_icon=ft.icons.FAVORITE,
                    label=self.translator.translate("nav.favorites"),
                ),
                ft.NavigationRailDestination(
                    icon=ft.icons.SETTINGS_OUTLINED,
                    selected_icon=ft.icons.SETTINGS,
                    label=self.translator.translate("nav.settings"),
                ),
            ],
        )

        # Medical terms examples
        medical_terms_list = ft.Column([
            ft.Text(
                self.translator.translate("medical.terms.diabetes"),
                size=14
            ),
            ft.Text(
                self.translator.translate("medical.terms.hypertension"),
                size=14
            ),
            ft.Text(
                self.translator.translate("medical.terms.fever"),
                size=14
            ),
        ])

        # Layout
        page.add(
            ft.Row([
                ft.Container(
                    content=ft.Column([
                        ft.Text(
                            self.translator.translate("settings.language"),
                            size=12
                        ),
                        language_dropdown,
                    ]),
                    padding=10,
                ),
            ], alignment=ft.MainAxisAlignment.END),
            ft.Row([
                self.nav_rail,
                ft.VerticalDivider(width=1),
                ft.Column([
                    self.welcome_text,
                    ft.Divider(),
                    ft.Row([
                        self.search_field,
                        self.submit_button,
                    ]),
                    self.result_text,
                    ft.Divider(),
                    ft.Text(
                        self.translator.translate("common.examples") + ":",
                        size=16,
                        weight=ft.FontWeight.BOLD,
                    ),
                    medical_terms_list,
                ], expand=True, scroll=ft.ScrollMode.AUTO),
            ], expand=True),
        )

    def on_submit(self, e):
        """Handle search submission."""
        query = self.search_field.value

        if not query:
            self.result_text.value = self.translator.translate("errors.no_results")
            self.result_text.update()
            return

        # Simulate processing
        self.result_text.value = f"{self.translator.translate('messages.processing')}"
        self.result_text.update()

        # Simulate result (in production, call RAG pipeline)
        import time
        time.sleep(1)

        self.result_text.value = f"""
{self.translator.translate('responses.answer_template')}

{self.translator.translate('responses.draft_warning')}

{self.translator.translate('responses.sources')}: UpToDate, PubMed
"""
        self.result_text.update()

    def update_ui(self, page: ft.Page):
        """Update all UI elements with new translations."""
        # Update page title
        page.title = self.translator.translate("app.name")

        # Update welcome text
        self.welcome_text.value = self.translator.translate(
            "messages.welcome",
            params={"name": "Doctor"}
        )

        # Update search field
        self.search_field.hint_text = self.translator.translate(
            "search.search_placeholder"
        )

        # Update button
        self.submit_button.text = self.translator.translate("buttons.submit")

        # Update navigation rail
        self.nav_rail.destinations = [
            ft.NavigationRailDestination(
                icon=ft.icons.HOME_OUTLINED,
                selected_icon=ft.icons.HOME,
                label=self.translator.translate("nav.home"),
            ),
            ft.NavigationRailDestination(
                icon=ft.icons.SEARCH_OUTLINED,
                selected_icon=ft.icons.SEARCH,
                label=self.translator.translate("nav.search"),
            ),
            ft.NavigationRailDestination(
                icon=ft.icons.LIBRARY_BOOKS_OUTLINED,
                selected_icon=ft.icons.LIBRARY_BOOKS,
                label=self.translator.translate("nav.library"),
            ),
            ft.NavigationRailDestination(
                icon=ft.icons.FAVORITE_OUTLINED,
                selected_icon=ft.icons.FAVORITE,
                label=self.translator.translate("nav.favorites"),
            ),
            ft.NavigationRailDestination(
                icon=ft.icons.SETTINGS_OUTLINED,
                selected_icon=ft.icons.SETTINGS,
                label=self.translator.translate("nav.settings"),
            ),
        ]

        # Update page
        page.update()


# Usage example
if __name__ == "__main__":
    app = MultilingualApp()
    ft.app(target=app.main)

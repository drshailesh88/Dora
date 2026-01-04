"""History View - Query history."""

import flet as ft
from datetime import datetime

from ..theme import Colors, Spacing, Typography, styled_card
from ..services import StateManager, QueryHistoryItem


class HistoryView(ft.UserControl):
    """View for query history."""

    def __init__(self, state_manager: StateManager, on_rerun: callable | None = None):
        super().__init__()
        self.state = state_manager
        self.on_rerun = on_rerun
        self.history_list: ft.ListView | None = None

    def build(self):
        self.state.subscribe(self._on_state_change)

        self.history_list = ft.ListView(
            expand=True,
            spacing=Spacing.SM,
            padding=Spacing.MD,
        )

        # Populate with existing history
        self._refresh_history()

        # Empty state
        empty_state = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Icon(
                        ft.icons.HISTORY,
                        size=48,
                        color=Colors.TEXT_TERTIARY,
                    ),
                    ft.Text(
                        "No queries yet",
                        size=Typography.SIZE_MD,
                        color=Colors.TEXT_SECONDARY,
                    ),
                    ft.Text(
                        "Your query history will appear here",
                        size=Typography.SIZE_SM,
                        color=Colors.TEXT_TERTIARY,
                    ),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=Spacing.SM,
            ),
            alignment=ft.alignment.center,
            expand=True,
            visible=len(self.state.state.query_history) == 0,
        )

        return ft.Column(
            controls=[
                # Header
                ft.Container(
                    content=ft.Row(
                        controls=[
                            ft.Column(
                                controls=[
                                    ft.Text(
                                        "Query History",
                                        size=Typography.SIZE_XL,
                                        weight=Typography.WEIGHT_BOLD,
                                        color=Colors.TEXT_PRIMARY,
                                    ),
                                    ft.Text(
                                        f"{len(self.state.state.query_history)} queries",
                                        size=Typography.SIZE_SM,
                                        color=Colors.TEXT_SECONDARY,
                                    ),
                                ],
                                spacing=4,
                            ),
                            ft.Container(expand=True),
                            ft.IconButton(
                                icon=ft.icons.DELETE_SWEEP,
                                icon_color=Colors.TEXT_SECONDARY,
                                tooltip="Clear history",
                                on_click=self._clear_history,
                            ),
                        ],
                    ),
                    padding=Spacing.MD,
                ),

                # History list
                self.history_list,

                # Empty state
                empty_state,
            ],
            spacing=0,
            expand=True,
        )

    def _refresh_history(self):
        """Refresh the history list."""
        if not self.history_list:
            return

        self.history_list.controls.clear()

        for item in self.state.state.query_history:
            self.history_list.controls.append(self._create_history_item(item))

    def _create_history_item(self, item: QueryHistoryItem) -> ft.Control:
        """Create a history item card."""
        # Format timestamp
        time_str = item.timestamp.strftime("%I:%M %p")
        date_str = item.timestamp.strftime("%b %d")

        # Confidence badge color
        conf_colors = {
            "high": Colors.SUCCESS,
            "medium": Colors.WARNING,
            "low": Colors.ERROR,
        }
        conf_color = conf_colors.get(item.confidence.lower(), Colors.TEXT_SECONDARY)

        return ft.Container(
            content=ft.Column(
                controls=[
                    # Header row
                    ft.Row(
                        controls=[
                            ft.Text(
                                time_str,
                                size=Typography.SIZE_XS,
                                color=Colors.TEXT_TERTIARY,
                            ),
                            ft.Text(
                                date_str,
                                size=Typography.SIZE_XS,
                                color=Colors.TEXT_TERTIARY,
                            ),
                            ft.Container(expand=True),
                            ft.Container(
                                content=ft.Text(
                                    item.confidence.upper(),
                                    size=10,
                                    weight=Typography.WEIGHT_SEMIBOLD,
                                    color=conf_color,
                                ),
                                bgcolor=ft.colors.with_opacity(0.1, conf_color),
                                border_radius=4,
                                padding=ft.padding.symmetric(horizontal=6, vertical=2),
                            ),
                        ],
                        spacing=Spacing.SM,
                    ),

                    # Question
                    ft.Text(
                        item.question,
                        size=Typography.SIZE_SM,
                        weight=Typography.WEIGHT_MEDIUM,
                        color=Colors.TEXT_PRIMARY,
                        max_lines=2,
                        overflow=ft.TextOverflow.ELLIPSIS,
                    ),

                    # Answer preview
                    ft.Text(
                        item.answer[:150] + "..." if len(item.answer) > 150 else item.answer,
                        size=Typography.SIZE_SM,
                        color=Colors.TEXT_SECONDARY,
                        max_lines=2,
                        overflow=ft.TextOverflow.ELLIPSIS,
                    ),

                    # Actions
                    ft.Row(
                        controls=[
                            ft.TextButton(
                                text="View Full",
                                style=ft.ButtonStyle(color=Colors.PRIMARY),
                                on_click=lambda _, i=item: self._view_full(i),
                            ),
                            ft.TextButton(
                                text="Ask Again",
                                style=ft.ButtonStyle(color=Colors.TEXT_SECONDARY),
                                on_click=lambda _, i=item: self._rerun_query(i),
                            ),
                        ],
                        spacing=Spacing.SM,
                    ),
                ],
                spacing=Spacing.XS,
            ),
            bgcolor=Colors.BG_PRIMARY,
            border_radius=8,
            padding=Spacing.MD,
            border=ft.border.all(1, Colors.BG_TERTIARY),
        )

    def _view_full(self, item: QueryHistoryItem):
        """View full answer in dialog."""
        # Create dialog content
        dialog = ft.AlertDialog(
            title=ft.Text("Query Details", weight=Typography.WEIGHT_BOLD),
            content=ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Text(
                            "QUESTION",
                            size=Typography.SIZE_XS,
                            weight=Typography.WEIGHT_SEMIBOLD,
                            color=Colors.TEXT_SECONDARY,
                        ),
                        ft.Text(
                            item.question,
                            size=Typography.SIZE_MD,
                            color=Colors.TEXT_PRIMARY,
                            selectable=True,
                        ),
                        ft.Divider(height=20),
                        ft.Text(
                            "ANSWER",
                            size=Typography.SIZE_XS,
                            weight=Typography.WEIGHT_SEMIBOLD,
                            color=Colors.TEXT_SECONDARY,
                        ),
                        ft.Text(
                            item.answer,
                            size=Typography.SIZE_MD,
                            color=Colors.TEXT_PRIMARY,
                            selectable=True,
                        ),
                        ft.Divider(height=20),
                        ft.Text(
                            f"Confidence: {item.confidence}",
                            size=Typography.SIZE_SM,
                            color=Colors.TEXT_SECONDARY,
                        ),
                        ft.Text(
                            f"Citations: {len(item.citations)}",
                            size=Typography.SIZE_SM,
                            color=Colors.TEXT_SECONDARY,
                        ),
                    ],
                    scroll=ft.ScrollMode.AUTO,
                    spacing=Spacing.XS,
                ),
                width=500,
                height=400,
            ),
            actions=[
                ft.TextButton("Close", on_click=lambda _: self._close_dialog()),
            ],
        )

        self.page.dialog = dialog
        dialog.open = True
        self.page.update()

    def _close_dialog(self):
        """Close dialog."""
        if self.page.dialog:
            self.page.dialog.open = False
            self.page.update()

    def _rerun_query(self, item: QueryHistoryItem):
        """Re-run a query."""
        if self.on_rerun:
            self.on_rerun(item.question)

    def _clear_history(self, e):
        """Clear all history."""
        self.state.state.query_history.clear()
        self.state.notify()
        self._refresh_history()
        self.history_list.update()

    def _on_state_change(self, state):
        """Handle state changes."""
        self._refresh_history()
        if self.history_list:
            self.history_list.update()

    def will_unmount(self):
        """Cleanup on unmount."""
        self.state.unsubscribe(self._on_state_change)

"""Drugs View - Drug interaction checker."""

import flet as ft

from ..theme import Colors, Spacing, Typography, styled_card, styled_button
from ..components import DrugInteractionCard
from ..services import DoraAPIClient, StateManager


class DrugsView(ft.UserControl):
    """Drug interaction checking interface."""

    def __init__(self, api_client: DoraAPIClient, state_manager: StateManager):
        super().__init__()
        self.api = api_client
        self.state = state_manager
        self.drug_inputs: list[ft.TextField] = []
        self.results_container: ft.Column | None = None
        self.loading: ft.ProgressRing | None = None

    def build(self):
        self.loading = ft.ProgressRing(
            visible=False,
            width=24,
            height=24,
            stroke_width=2,
            color=Colors.PRIMARY,
        )

        # Drug input fields
        self.drug_inputs = [
            self._create_drug_input(1),
            self._create_drug_input(2),
        ]

        drug_inputs_column = ft.Column(
            controls=self.drug_inputs,
            spacing=Spacing.SM,
        )

        # Add drug button
        add_drug_btn = ft.TextButton(
            text="+ Add another drug",
            on_click=self._add_drug_field,
            style=ft.ButtonStyle(color=Colors.PRIMARY),
        )

        # Check button
        check_btn = styled_button(
            text="Check Interactions",
            icon=ft.icons.VERIFIED_USER,
            on_click=self._check_interactions,
        )

        # Results container
        self.results_container = ft.Column(
            controls=[],
            spacing=Spacing.MD,
        )

        # Quick reference section
        quick_ref = styled_card(
            ft.Column(
                controls=[
                    ft.Text(
                        "SEVERITY GUIDE",
                        size=Typography.SIZE_XS,
                        weight=Typography.WEIGHT_SEMIBOLD,
                        color=Colors.TEXT_SECONDARY,
                    ),
                    ft.Row(
                        controls=[
                            self._severity_legend("Contraindicated", Colors.CONTRAINDICATED),
                            self._severity_legend("Severe", Colors.SEVERE),
                            self._severity_legend("Moderate", Colors.MODERATE),
                            self._severity_legend("Mild", Colors.MILD),
                        ],
                        spacing=Spacing.MD,
                        wrap=True,
                    ),
                ],
                spacing=Spacing.SM,
            ),
        )

        return ft.Column(
            controls=[
                # Header
                ft.Container(
                    content=ft.Column(
                        controls=[
                            ft.Text(
                                "Drug Interaction Checker",
                                size=Typography.SIZE_XL,
                                weight=Typography.WEIGHT_BOLD,
                                color=Colors.TEXT_PRIMARY,
                            ),
                            ft.Text(
                                "Check for potential interactions between medications",
                                size=Typography.SIZE_SM,
                                color=Colors.TEXT_SECONDARY,
                            ),
                        ],
                        spacing=4,
                    ),
                    padding=Spacing.MD,
                ),

                # Drug inputs card
                styled_card(
                    ft.Column(
                        controls=[
                            ft.Text(
                                "ENTER MEDICATIONS",
                                size=Typography.SIZE_XS,
                                weight=Typography.WEIGHT_SEMIBOLD,
                                color=Colors.TEXT_SECONDARY,
                            ),
                            drug_inputs_column,
                            add_drug_btn,
                            ft.Container(height=Spacing.SM),
                            ft.Row(
                                controls=[check_btn, self.loading],
                                spacing=Spacing.MD,
                            ),
                        ],
                        spacing=Spacing.SM,
                    ),
                ),

                # Severity guide
                quick_ref,

                # Results
                ft.Container(
                    content=ft.Column(
                        controls=[
                            ft.Text(
                                "RESULTS",
                                size=Typography.SIZE_XS,
                                weight=Typography.WEIGHT_SEMIBOLD,
                                color=Colors.TEXT_SECONDARY,
                            ),
                            self.results_container,
                        ],
                        spacing=Spacing.SM,
                    ),
                    padding=Spacing.MD,
                    visible=False,
                ),
            ],
            spacing=Spacing.MD,
            expand=True,
            scroll=ft.ScrollMode.AUTO,
        )

    def _create_drug_input(self, number: int) -> ft.Row:
        """Create a drug input row."""
        text_field = ft.TextField(
            label=f"Drug {number}",
            hint_text="Enter drug name (e.g., Warfarin, Aspirin)",
            expand=True,
            border_radius=8,
            border_color=Colors.BG_TERTIARY,
            focused_border_color=Colors.PRIMARY,
        )

        remove_btn = ft.IconButton(
            icon=ft.icons.REMOVE_CIRCLE_OUTLINE,
            icon_color=Colors.ERROR,
            tooltip="Remove",
            on_click=lambda e, row=None: self._remove_drug_field(e, row),
            visible=number > 2,
        )

        row = ft.Row(
            controls=[text_field, remove_btn],
            spacing=Spacing.SM,
        )

        # Store reference to remove button
        remove_btn.data = row

        return row

    def _add_drug_field(self, e):
        """Add a new drug input field."""
        new_input = self._create_drug_input(len(self.drug_inputs) + 1)
        new_input.controls[1].visible = True  # Show remove button
        self.drug_inputs.append(new_input)

        # Find the column and add
        for control in self.controls[0].controls:
            if isinstance(control, ft.Container):
                content = control.content
                if isinstance(content, ft.Column):
                    for c in content.controls:
                        if isinstance(c, ft.Column) and len(c.controls) > 0:
                            if isinstance(c.controls[0], ft.Row):
                                c.controls.append(new_input)
                                c.update()
                                return

    def _remove_drug_field(self, e, row):
        """Remove a drug input field."""
        row_to_remove = e.control.data
        if row_to_remove in self.drug_inputs:
            self.drug_inputs.remove(row_to_remove)

            # Update parent
            for control in self.controls[0].controls:
                if isinstance(control, ft.Container):
                    content = control.content
                    if isinstance(content, ft.Column):
                        for c in content.controls:
                            if isinstance(c, ft.Column):
                                if row_to_remove in c.controls:
                                    c.controls.remove(row_to_remove)
                                    c.update()
                                    return

    async def _check_interactions(self, e):
        """Check drug interactions."""
        # Collect drug names
        drugs = []
        for row in self.drug_inputs:
            if isinstance(row, ft.Row):
                text_field = row.controls[0]
                if text_field.value:
                    drugs.append(text_field.value.strip())

        if len(drugs) < 2:
            # Show error
            self.results_container.controls.clear()
            self.results_container.controls.append(
                ft.Container(
                    content=ft.Text(
                        "Please enter at least 2 drugs to check interactions.",
                        color=Colors.WARNING,
                        size=Typography.SIZE_SM,
                    ),
                    bgcolor=ft.colors.with_opacity(0.1, Colors.WARNING),
                    border_radius=8,
                    padding=Spacing.MD,
                )
            )
            self.results_container.parent.visible = True
            self.results_container.update()
            return

        # Show loading
        self.loading.visible = True
        self.loading.update()

        # Call API
        result = await self.api.check_drug_interactions(drugs=drugs)

        # Hide loading
        self.loading.visible = False
        self.loading.update()

        # Clear previous results
        self.results_container.controls.clear()

        if result.get("success"):
            interactions = result.get("interactions", [])

            if not interactions:
                # No interactions found
                self.results_container.controls.append(
                    ft.Container(
                        content=ft.Row(
                            controls=[
                                ft.Icon(ft.icons.CHECK_CIRCLE, color=Colors.SUCCESS, size=24),
                                ft.Text(
                                    f"No known interactions found between {', '.join(drugs)}",
                                    color=Colors.SUCCESS,
                                    size=Typography.SIZE_MD,
                                    weight=Typography.WEIGHT_MEDIUM,
                                ),
                            ],
                            spacing=Spacing.SM,
                        ),
                        bgcolor=ft.colors.with_opacity(0.1, Colors.SUCCESS),
                        border_radius=8,
                        padding=Spacing.MD,
                    )
                )
            else:
                # Show interactions
                for inter in interactions:
                    self.results_container.controls.append(
                        DrugInteractionCard(
                            drug1=inter.get("drug1", ""),
                            drug2=inter.get("drug2", ""),
                            severity=inter.get("severity", "unknown"),
                            description=inter.get("description", ""),
                            management=inter.get("management", ""),
                        )
                    )
        else:
            # Show error
            error_msg = result.get("error", "Failed to check interactions")
            self.results_container.controls.append(
                ft.Container(
                    content=ft.Row(
                        controls=[
                            ft.Icon(ft.icons.ERROR_OUTLINE, color=Colors.ERROR, size=20),
                            ft.Text(error_msg, color=Colors.ERROR, size=Typography.SIZE_SM),
                        ],
                        spacing=Spacing.SM,
                    ),
                    bgcolor=ft.colors.with_opacity(0.1, Colors.ERROR),
                    border_radius=8,
                    padding=Spacing.MD,
                )
            )

        # Show results section
        self.results_container.parent.visible = True
        self.results_container.update()

    def _severity_legend(self, label: str, color: str) -> ft.Row:
        """Create a severity legend item."""
        return ft.Row(
            controls=[
                ft.Container(
                    width=12,
                    height=12,
                    border_radius=2,
                    bgcolor=color,
                ),
                ft.Text(
                    label,
                    size=Typography.SIZE_XS,
                    color=Colors.TEXT_SECONDARY,
                ),
            ],
            spacing=4,
        )

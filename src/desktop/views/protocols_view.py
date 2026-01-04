"""Protocols View - Team protocols and checklists."""

import flet as ft

from ..theme import Colors, Spacing, Typography, styled_card, styled_button
from ..services import DoraAPIClient, StateManager


class ProtocolsView(ft.UserControl):
    """Team protocols and checklists interface."""

    def __init__(self, api_client: DoraAPIClient, state_manager: StateManager):
        super().__init__()
        self.api = api_client
        self.state = state_manager
        self.protocols: list[dict] = []
        self.selected_protocol: dict | None = None
        self.checklist_items: dict[str, bool] = {}

    def build(self):
        # Protocol list
        self.protocol_list = ft.Container(
            content=self._build_protocol_list(),
            expand=True,
        )

        # Protocol detail (hidden initially)
        self.protocol_detail = ft.Container(
            visible=False,
            expand=True,
        )

        # Search bar
        search_bar = ft.TextField(
            hint_text="Search protocols...",
            prefix_icon=ft.icons.SEARCH,
            border_radius=20,
            border_color=Colors.BG_TERTIARY,
            focused_border_color=Colors.PRIMARY,
            expand=True,
            on_change=self._on_search,
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
                                        "Protocols & Checklists",
                                        size=Typography.SIZE_XL,
                                        weight=Typography.WEIGHT_BOLD,
                                        color=Colors.TEXT_PRIMARY,
                                    ),
                                    ft.Text(
                                        "Standardized clinical workflows for your team",
                                        size=Typography.SIZE_SM,
                                        color=Colors.TEXT_SECONDARY,
                                    ),
                                ],
                                spacing=4,
                                expand=True,
                            ),
                            styled_button(
                                text="Create Protocol",
                                icon=ft.icons.ADD,
                                on_click=self._create_protocol,
                            ),
                        ],
                    ),
                    padding=Spacing.MD,
                ),

                # Search bar
                ft.Container(
                    content=search_bar,
                    padding=ft.padding.symmetric(horizontal=Spacing.MD),
                ),

                # Content
                ft.Stack(
                    controls=[
                        self.protocol_list,
                        self.protocol_detail,
                    ],
                    expand=True,
                ),
            ],
            expand=True,
        )

    def _build_protocol_list(self) -> ft.Control:
        """Build the protocol list."""
        # Mock protocols for demo
        self.protocols = [
            {
                "id": "sepsis-bundle",
                "title": "Sepsis 3-Hour Bundle",
                "description": "Initial resuscitation and management of sepsis",
                "category": "Critical Care",
                "status": "published",
                "usage_count": 156,
                "items": [
                    {"id": "1", "text": "Measure lactate level", "required": True, "section": "Initial Assessment"},
                    {"id": "2", "text": "Obtain blood cultures prior to antibiotics", "required": True, "section": "Initial Assessment"},
                    {"id": "3", "text": "Administer broad-spectrum antibiotics", "required": True, "section": "Treatment"},
                    {"id": "4", "text": "Administer 30 mL/kg crystalloid for hypotension or lactate ≥4 mmol/L", "required": True, "section": "Treatment"},
                    {"id": "5", "text": "Apply vasopressors if hypotensive during/after fluid resuscitation", "required": False, "section": "Hemodynamic Support"},
                    {"id": "6", "text": "Reassess volume status and tissue perfusion", "required": True, "section": "Reassessment"},
                    {"id": "7", "text": "Remeasure lactate if initial elevated", "required": True, "section": "Reassessment"},
                ],
            },
            {
                "id": "chest-pain",
                "title": "Chest Pain Evaluation",
                "description": "Systematic evaluation of acute chest pain",
                "category": "Cardiology",
                "status": "published",
                "usage_count": 243,
                "items": [
                    {"id": "1", "text": "Obtain 12-lead ECG within 10 minutes", "required": True, "section": "Immediate"},
                    {"id": "2", "text": "Measure troponin levels", "required": True, "section": "Immediate"},
                    {"id": "3", "text": "Assess HEART score", "required": True, "section": "Risk Stratification"},
                    {"id": "4", "text": "Administer aspirin 325mg if no contraindication", "required": True, "section": "Treatment"},
                    {"id": "5", "text": "Consider sublingual nitroglycerin", "required": False, "section": "Treatment"},
                    {"id": "6", "text": "Cardiology consult if STEMI or high-risk NSTEMI", "required": True, "section": "Consultation"},
                ],
            },
            {
                "id": "stroke-code",
                "title": "Stroke Code Protocol",
                "description": "Acute stroke assessment and tPA eligibility",
                "category": "Neurology",
                "status": "published",
                "usage_count": 89,
                "items": [
                    {"id": "1", "text": "Confirm last known well time", "required": True, "section": "Assessment"},
                    {"id": "2", "text": "NIHSS assessment", "required": True, "section": "Assessment"},
                    {"id": "3", "text": "Stat CT head without contrast", "required": True, "section": "Imaging"},
                    {"id": "4", "text": "Check glucose level", "required": True, "section": "Labs"},
                    {"id": "5", "text": "Review tPA contraindications", "required": True, "section": "Eligibility"},
                    {"id": "6", "text": "Obtain informed consent", "required": True, "section": "Consent"},
                    {"id": "7", "text": "Administer tPA if eligible", "required": False, "section": "Treatment"},
                    {"id": "8", "text": "Consider thrombectomy if LVO", "required": False, "section": "Treatment"},
                ],
            },
            {
                "id": "intubation",
                "title": "Rapid Sequence Intubation",
                "description": "Emergency airway management checklist",
                "category": "Critical Care",
                "status": "draft",
                "usage_count": 45,
                "items": [
                    {"id": "1", "text": "Prepare equipment and suction", "required": True, "section": "Preparation"},
                    {"id": "2", "text": "Position patient optimally", "required": True, "section": "Preparation"},
                    {"id": "3", "text": "Preoxygenate for 3-5 minutes", "required": True, "section": "Preoxygenation"},
                    {"id": "4", "text": "Administer induction agent", "required": True, "section": "Medications"},
                    {"id": "5", "text": "Administer neuromuscular blocker", "required": True, "section": "Medications"},
                    {"id": "6", "text": "Perform laryngoscopy and intubation", "required": True, "section": "Procedure"},
                    {"id": "7", "text": "Confirm placement with ETCO2 and bilateral breath sounds", "required": True, "section": "Confirmation"},
                    {"id": "8", "text": "Secure tube and order chest X-ray", "required": True, "section": "Post-intubation"},
                ],
            },
        ]

        return ft.ListView(
            controls=[
                self._build_protocol_card(p)
                for p in self.protocols
            ],
            expand=True,
            spacing=Spacing.SM,
            padding=Spacing.MD,
        )

    def _build_protocol_card(self, protocol: dict) -> ft.Container:
        """Build a protocol card."""
        status_colors = {
            "published": Colors.SUCCESS,
            "draft": Colors.WARNING,
            "review": Colors.INFO,
        }
        status_color = status_colors.get(protocol["status"], Colors.TEXT_SECONDARY)

        return styled_card(
            ft.Column(
                controls=[
                    ft.Row(
                        controls=[
                            ft.Column(
                                controls=[
                                    ft.Text(
                                        protocol["title"],
                                        size=Typography.SIZE_MD,
                                        weight=Typography.WEIGHT_SEMIBOLD,
                                        color=Colors.TEXT_PRIMARY,
                                    ),
                                    ft.Text(
                                        protocol["description"],
                                        size=Typography.SIZE_SM,
                                        color=Colors.TEXT_SECONDARY,
                                    ),
                                ],
                                spacing=2,
                                expand=True,
                            ),
                            ft.Container(
                                content=ft.Text(
                                    protocol["status"].upper(),
                                    size=Typography.SIZE_XS,
                                    weight=Typography.WEIGHT_SEMIBOLD,
                                    color=Colors.TEXT_INVERSE,
                                ),
                                bgcolor=status_color,
                                border_radius=4,
                                padding=ft.padding.symmetric(horizontal=8, vertical=4),
                            ),
                        ],
                    ),
                    ft.Divider(height=1, color=Colors.BG_TERTIARY),
                    ft.Row(
                        controls=[
                            ft.Container(
                                content=ft.Text(
                                    protocol["category"],
                                    size=Typography.SIZE_XS,
                                    color=Colors.PRIMARY,
                                ),
                                bgcolor=ft.colors.with_opacity(0.1, Colors.PRIMARY),
                                border_radius=4,
                                padding=ft.padding.symmetric(horizontal=8, vertical=4),
                            ),
                            ft.Text(
                                f"{len(protocol['items'])} items",
                                size=Typography.SIZE_XS,
                                color=Colors.TEXT_SECONDARY,
                            ),
                            ft.Container(expand=True),
                            ft.Icon(ft.icons.ANALYTICS, size=14, color=Colors.TEXT_SECONDARY),
                            ft.Text(
                                f"{protocol['usage_count']} uses",
                                size=Typography.SIZE_XS,
                                color=Colors.TEXT_SECONDARY,
                            ),
                            ft.IconButton(
                                icon=ft.icons.PLAY_ARROW,
                                icon_color=Colors.PRIMARY,
                                tooltip="Start Checklist",
                                on_click=lambda _, p=protocol: self._open_protocol(p),
                            ),
                        ],
                        spacing=Spacing.SM,
                    ),
                ],
                spacing=Spacing.SM,
            ),
        )

    def _open_protocol(self, protocol: dict):
        """Open protocol checklist view."""
        self.selected_protocol = protocol
        self.checklist_items = {item["id"]: False for item in protocol["items"]}

        # Group items by section
        sections: dict[str, list[dict]] = {}
        for item in protocol["items"]:
            section = item.get("section", "General")
            if section not in sections:
                sections[section] = []
            sections[section].append(item)

        # Build checklist
        checklist_controls = []
        for section_name, items in sections.items():
            checklist_controls.append(
                ft.Text(
                    section_name.upper(),
                    size=Typography.SIZE_XS,
                    weight=Typography.WEIGHT_SEMIBOLD,
                    color=Colors.PRIMARY,
                )
            )
            for item in items:
                checklist_controls.append(
                    self._build_checklist_item(item)
                )
            checklist_controls.append(ft.Container(height=Spacing.SM))

        # Progress indicator
        self.progress_text = ft.Text(
            "0%",
            size=Typography.SIZE_XXL,
            weight=Typography.WEIGHT_BOLD,
            color=Colors.PRIMARY,
        )

        self.progress_bar = ft.ProgressBar(
            value=0,
            color=Colors.PRIMARY,
            bgcolor=Colors.BG_TERTIARY,
        )

        # Build detail view
        self.protocol_detail.content = ft.Column(
            controls=[
                # Back button and title
                ft.Container(
                    content=ft.Row(
                        controls=[
                            ft.IconButton(
                                icon=ft.icons.ARROW_BACK,
                                on_click=self._close_protocol,
                            ),
                            ft.Column(
                                controls=[
                                    ft.Text(
                                        protocol["title"],
                                        size=Typography.SIZE_LG,
                                        weight=Typography.WEIGHT_BOLD,
                                        color=Colors.TEXT_PRIMARY,
                                    ),
                                    ft.Text(
                                        protocol["description"],
                                        size=Typography.SIZE_SM,
                                        color=Colors.TEXT_SECONDARY,
                                    ),
                                ],
                                spacing=2,
                                expand=True,
                            ),
                        ],
                        spacing=Spacing.SM,
                    ),
                    padding=Spacing.MD,
                ),

                # Progress section
                ft.Container(
                    content=ft.Row(
                        controls=[
                            ft.Column(
                                controls=[
                                    ft.Text(
                                        "Completion",
                                        size=Typography.SIZE_XS,
                                        color=Colors.TEXT_SECONDARY,
                                    ),
                                    self.progress_text,
                                ],
                                spacing=2,
                            ),
                            ft.Container(
                                content=self.progress_bar,
                                expand=True,
                                padding=ft.padding.only(left=Spacing.MD),
                            ),
                        ],
                    ),
                    bgcolor=Colors.BG_SECONDARY,
                    border_radius=12,
                    padding=Spacing.MD,
                    margin=ft.margin.symmetric(horizontal=Spacing.MD),
                ),

                # Checklist
                ft.ListView(
                    controls=checklist_controls,
                    expand=True,
                    padding=Spacing.MD,
                ),

                # Complete button
                ft.Container(
                    content=styled_button(
                        text="Mark Complete",
                        icon=ft.icons.CHECK_CIRCLE,
                        on_click=self._complete_protocol,
                        disabled=True,
                    ),
                    padding=Spacing.MD,
                ),
            ],
            expand=True,
        )

        # Show detail, hide list
        self.protocol_list.visible = False
        self.protocol_detail.visible = True
        self.protocol_list.update()
        self.protocol_detail.update()

    def _build_checklist_item(self, item: dict) -> ft.Container:
        """Build a checklist item."""
        is_required = item.get("required", False)

        checkbox = ft.Checkbox(
            label=item["text"],
            value=False,
            active_color=Colors.PRIMARY,
            on_change=lambda e, i=item["id"]: self._toggle_item(i, e.control.value),
        )

        return ft.Container(
            content=ft.Row(
                controls=[
                    checkbox,
                    ft.Container(expand=True),
                    ft.Icon(
                        ft.icons.STAR,
                        size=14,
                        color=Colors.ERROR if is_required else Colors.TRANSPARENT,
                        tooltip="Required",
                    ) if is_required else ft.Container(),
                ],
            ),
            bgcolor=Colors.BG_PRIMARY,
            border_radius=8,
            padding=Spacing.SM,
            border=ft.border.all(1, Colors.BG_TERTIARY),
        )

    def _toggle_item(self, item_id: str, value: bool):
        """Toggle checklist item."""
        self.checklist_items[item_id] = value
        self._update_progress()

    def _update_progress(self):
        """Update progress indicator."""
        if not self.selected_protocol:
            return

        total = len(self.checklist_items)
        completed = sum(1 for v in self.checklist_items.values() if v)
        percentage = (completed / total) * 100 if total > 0 else 0

        self.progress_text.value = f"{int(percentage)}%"
        self.progress_bar.value = percentage / 100
        self.progress_text.update()
        self.progress_bar.update()

        # Enable complete button if all required items are checked
        required_items = [
            item["id"] for item in self.selected_protocol["items"]
            if item.get("required", False)
        ]
        all_required_complete = all(
            self.checklist_items.get(item_id, False)
            for item_id in required_items
        )

        # Update button state
        complete_btn = self.protocol_detail.content.controls[-1].content
        complete_btn.disabled = not all_required_complete
        complete_btn.update()

    def _close_protocol(self, e):
        """Close protocol detail view."""
        self.selected_protocol = None
        self.protocol_list.visible = True
        self.protocol_detail.visible = False
        self.protocol_list.update()
        self.protocol_detail.update()

    def _complete_protocol(self, e):
        """Mark protocol as complete."""
        # Record usage via API
        # For now, show success message
        self.page.snack_bar = ft.SnackBar(
            content=ft.Text("Protocol completed successfully!"),
            bgcolor=Colors.SUCCESS,
        )
        self.page.snack_bar.open = True
        self.page.update()

        self._close_protocol(None)

    def _create_protocol(self, e):
        """Create new protocol."""
        # Would open protocol editor
        self.page.snack_bar = ft.SnackBar(
            content=ft.Text("Protocol editor coming soon!"),
            bgcolor=Colors.INFO,
        )
        self.page.snack_bar.open = True
        self.page.update()

    def _on_search(self, e):
        """Handle search."""
        query = e.control.value.lower()
        filtered = [
            p for p in self.protocols
            if query in p["title"].lower() or query in p["description"].lower()
        ]

        self.protocol_list.content.controls = [
            self._build_protocol_card(p) for p in filtered
        ]
        self.protocol_list.update()

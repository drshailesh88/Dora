"""Query View - Main question/answer interface."""

import flet as ft

from ..theme import Colors, Spacing, Typography, styled_card
from ..components import QueryInput, AnswerCard, PatientContextBanner
from ..services import DoraAPIClient, StateManager, QueryHistoryItem


class QueryView(ft.UserControl):
    """Main query interface for medical questions."""

    def __init__(self, api_client: DoraAPIClient, state_manager: StateManager):
        super().__init__()
        self.api = api_client
        self.state = state_manager
        self.answers_list: ft.ListView | None = None
        self.loading_indicator: ft.ProgressRing | None = None
        self.patient_banner: ft.Container | None = None

    def build(self):
        # Subscribe to state changes
        self.state.subscribe(self._on_state_change)

        # Loading indicator
        self.loading_indicator = ft.ProgressRing(
            visible=False,
            width=24,
            height=24,
            stroke_width=2,
            color=Colors.PRIMARY,
        )

        # Answers list
        self.answers_list = ft.ListView(
            expand=True,
            spacing=Spacing.MD,
            padding=Spacing.MD,
            auto_scroll=True,
        )

        # Patient context banner (initially hidden)
        self.patient_banner = ft.Container(visible=False)

        # Welcome message
        welcome = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Icon(
                        ft.icons.LOCAL_HOSPITAL,
                        size=48,
                        color=Colors.PRIMARY,
                    ),
                    ft.Text(
                        "Welcome to Dora",
                        size=Typography.SIZE_XXL,
                        weight=Typography.WEIGHT_BOLD,
                        color=Colors.TEXT_PRIMARY,
                    ),
                    ft.Text(
                        "Ask any medical question and get evidence-based answers with citations.",
                        size=Typography.SIZE_MD,
                        color=Colors.TEXT_SECONDARY,
                        text_align=ft.TextAlign.CENTER,
                    ),
                    ft.Container(height=Spacing.LG),
                    ft.Text(
                        "Example questions:",
                        size=Typography.SIZE_SM,
                        weight=Typography.WEIGHT_MEDIUM,
                        color=Colors.TEXT_SECONDARY,
                    ),
                    self._example_questions(),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=Spacing.SM,
            ),
            alignment=ft.alignment.center,
            expand=True,
        )

        self.answers_list.controls.append(welcome)

        # Query input at bottom
        query_input = QueryInput(
            on_submit=self._handle_query,
            on_voice=self._handle_voice,
            placeholder="Ask a medical question...",
        )

        return ft.Column(
            controls=[
                # Patient banner
                self.patient_banner,
                # Loading indicator row
                ft.Row(
                    controls=[
                        ft.Container(expand=True),
                        self.loading_indicator,
                        ft.Container(expand=True),
                    ],
                    visible=False,
                ),
                # Main content
                self.answers_list,
                # Input area
                query_input,
            ],
            spacing=0,
            expand=True,
        )

    def _example_questions(self) -> ft.Control:
        """Create example question chips."""
        examples = [
            "What is the first-line treatment for type 2 diabetes?",
            "How to manage hypertensive crisis?",
            "Differential diagnosis for chest pain",
            "Drug interactions with warfarin",
        ]

        chips = [
            ft.Container(
                content=ft.Text(
                    q,
                    size=Typography.SIZE_SM,
                    color=Colors.PRIMARY,
                ),
                bgcolor=ft.colors.with_opacity(0.1, Colors.PRIMARY),
                border_radius=20,
                padding=ft.padding.symmetric(horizontal=16, vertical=8),
                on_click=lambda _, q=q: self._handle_query(q),
                ink=True,
            )
            for q in examples
        ]

        return ft.Wrap(
            controls=chips,
            spacing=Spacing.SM,
            run_spacing=Spacing.SM,
            alignment=ft.MainAxisAlignment.CENTER,
        )

    async def _handle_query(self, question: str):
        """Handle a query submission."""
        if not question.strip():
            return

        # Show loading
        self.loading_indicator.visible = True
        self.loading_indicator.update()

        # Clear welcome message if present
        if len(self.answers_list.controls) == 1:
            self.answers_list.controls.clear()
            self.answers_list.update()

        # Call API
        result = await self.api.query(
            question=question,
            patient_id=self.state.state.current_patient_id,
        )

        # Hide loading
        self.loading_indicator.visible = False
        self.loading_indicator.update()

        if result.get("success") and result.get("answer"):
            answer_data = result["answer"]

            # Create answer card
            answer_card = AnswerCard(
                question=question,
                answer=answer_data.get("answer", "No answer available."),
                confidence=answer_data.get("confidence", "unknown"),
                citations=answer_data.get("citations", []),
                warnings=answer_data.get("warnings", []),
            )

            self.answers_list.controls.append(answer_card)
            self.answers_list.update()

            # Add to history
            self.state.add_query_to_history(
                QueryHistoryItem(
                    question=question,
                    answer=answer_data.get("answer", ""),
                    confidence=answer_data.get("confidence", "unknown"),
                    citations=answer_data.get("citations", []),
                    patient_id=self.state.state.current_patient_id,
                )
            )
        else:
            # Show error
            error_text = result.get("error", "Failed to get answer. Please try again.")
            error_container = ft.Container(
                content=ft.Row(
                    controls=[
                        ft.Icon(ft.icons.ERROR_OUTLINE, color=Colors.ERROR, size=20),
                        ft.Text(error_text, color=Colors.ERROR, size=Typography.SIZE_SM),
                    ],
                    spacing=Spacing.SM,
                ),
                bgcolor=ft.colors.with_opacity(0.1, Colors.ERROR),
                border_radius=8,
                padding=Spacing.MD,
            )
            self.answers_list.controls.append(error_container)
            self.answers_list.update()

    def _handle_voice(self):
        """Handle voice input."""
        # TODO: Integrate with voice agent
        pass

    def _on_state_change(self, state):
        """Handle state changes."""
        if state.current_patient_id:
            self.patient_banner.content = PatientContextBanner(
                patient_name=state.current_patient_name,
                patient_id=state.current_patient_id,
                on_clear=lambda: self.state.clear_patient(),
            )
            self.patient_banner.visible = True
        else:
            self.patient_banner.visible = False

        if self.patient_banner:
            self.patient_banner.update()

    def did_mount(self):
        """Called when view is mounted."""
        pass

    def will_unmount(self):
        """Called when view will unmount."""
        self.state.unsubscribe(self._on_state_change)

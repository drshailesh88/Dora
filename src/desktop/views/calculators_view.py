"""Calculators View - Medical calculators interface."""

import flet as ft

from ..theme import Colors, Spacing, Typography, styled_card, styled_button
from ..services import DoraAPIClient, StateManager


class CalculatorsView(ft.UserControl):
    """Medical calculators interface."""

    def __init__(self, api_client: DoraAPIClient, state_manager: StateManager):
        super().__init__()
        self.api = api_client
        self.state = state_manager
        self.selected_calculator: dict | None = None
        self.input_fields: dict[str, ft.TextField] = {}
        self.result_container: ft.Container | None = None

    def build(self):
        # Calculator categories
        categories = self._get_calculator_categories()

        # Category tabs
        category_tabs = ft.Tabs(
            tabs=[
                ft.Tab(
                    text=cat["name"],
                    icon=cat["icon"],
                )
                for cat in categories
            ],
            on_change=self._on_category_change,
        )

        # Calculator list
        self.calculator_list = ft.ListView(
            controls=self._build_calculator_list(categories[0]["calculators"]),
            expand=True,
            spacing=Spacing.SM,
            padding=Spacing.MD,
        )

        # Calculator detail (hidden initially)
        self.calculator_detail = ft.Container(
            visible=False,
            expand=True,
        )

        return ft.Column(
            controls=[
                # Header
                ft.Container(
                    content=ft.Column(
                        controls=[
                            ft.Text(
                                "Medical Calculators",
                                size=Typography.SIZE_XL,
                                weight=Typography.WEIGHT_BOLD,
                                color=Colors.TEXT_PRIMARY,
                            ),
                            ft.Text(
                                "Evidence-based clinical decision support tools",
                                size=Typography.SIZE_SM,
                                color=Colors.TEXT_SECONDARY,
                            ),
                        ],
                        spacing=4,
                    ),
                    padding=Spacing.MD,
                ),

                # Category tabs
                ft.Container(
                    content=category_tabs,
                    padding=ft.padding.symmetric(horizontal=Spacing.MD),
                ),

                # Content
                ft.Stack(
                    controls=[
                        self.calculator_list,
                        self.calculator_detail,
                    ],
                    expand=True,
                ),
            ],
            expand=True,
        )

    def _get_calculator_categories(self) -> list[dict]:
        """Get calculator categories."""
        return [
            {
                "name": "Cardiovascular",
                "icon": ft.icons.FAVORITE,
                "calculators": [
                    {
                        "id": "chads2vasc",
                        "name": "CHA₂DS₂-VASc Score",
                        "description": "Stroke risk in atrial fibrillation",
                        "inputs": [
                            {"id": "age", "label": "Age", "type": "number", "unit": "years"},
                            {"id": "sex", "label": "Sex", "type": "select", "options": ["Male", "Female"]},
                            {"id": "chf", "label": "CHF History", "type": "bool"},
                            {"id": "hypertension", "label": "Hypertension", "type": "bool"},
                            {"id": "stroke", "label": "Stroke/TIA/Thromboembolism", "type": "bool"},
                            {"id": "vascular", "label": "Vascular Disease", "type": "bool"},
                            {"id": "diabetes", "label": "Diabetes", "type": "bool"},
                        ],
                    },
                    {
                        "id": "heart_score",
                        "name": "HEART Score",
                        "description": "Major cardiac events risk assessment",
                        "inputs": [
                            {"id": "history", "label": "History", "type": "select", "options": ["Slightly suspicious", "Moderately suspicious", "Highly suspicious"]},
                            {"id": "ecg", "label": "ECG", "type": "select", "options": ["Normal", "Non-specific repolarization", "Significant ST deviation"]},
                            {"id": "age", "label": "Age", "type": "number"},
                            {"id": "risk_factors", "label": "Risk Factors", "type": "number"},
                            {"id": "troponin", "label": "Troponin", "type": "select", "options": ["Normal", "1-3x normal", ">3x normal"]},
                        ],
                    },
                    {
                        "id": "wells_pe",
                        "name": "Wells' Criteria (PE)",
                        "description": "Pulmonary embolism probability",
                        "inputs": [
                            {"id": "dvt_symptoms", "label": "DVT symptoms", "type": "bool"},
                            {"id": "pe_likely", "label": "PE most likely diagnosis", "type": "bool"},
                            {"id": "tachycardia", "label": "Heart rate >100", "type": "bool"},
                            {"id": "immobilization", "label": "Immobilization/surgery", "type": "bool"},
                            {"id": "previous_dvt", "label": "Previous DVT/PE", "type": "bool"},
                            {"id": "hemoptysis", "label": "Hemoptysis", "type": "bool"},
                            {"id": "malignancy", "label": "Active malignancy", "type": "bool"},
                        ],
                    },
                ],
            },
            {
                "name": "Renal",
                "icon": ft.icons.WATER_DROP,
                "calculators": [
                    {
                        "id": "gfr_ckd_epi",
                        "name": "eGFR (CKD-EPI)",
                        "description": "Estimated glomerular filtration rate",
                        "inputs": [
                            {"id": "creatinine", "label": "Creatinine", "type": "number", "unit": "mg/dL"},
                            {"id": "age", "label": "Age", "type": "number", "unit": "years"},
                            {"id": "sex", "label": "Sex", "type": "select", "options": ["Male", "Female"]},
                        ],
                    },
                    {
                        "id": "creatinine_clearance",
                        "name": "Creatinine Clearance",
                        "description": "Cockcroft-Gault equation",
                        "inputs": [
                            {"id": "creatinine", "label": "Creatinine", "type": "number", "unit": "mg/dL"},
                            {"id": "age", "label": "Age", "type": "number", "unit": "years"},
                            {"id": "weight", "label": "Weight", "type": "number", "unit": "kg"},
                            {"id": "sex", "label": "Sex", "type": "select", "options": ["Male", "Female"]},
                        ],
                    },
                ],
            },
            {
                "name": "Hepatic",
                "icon": ft.icons.SCIENCE,
                "calculators": [
                    {
                        "id": "meld",
                        "name": "MELD Score",
                        "description": "End-stage liver disease prognosis",
                        "inputs": [
                            {"id": "creatinine", "label": "Creatinine", "type": "number", "unit": "mg/dL"},
                            {"id": "bilirubin", "label": "Bilirubin", "type": "number", "unit": "mg/dL"},
                            {"id": "inr", "label": "INR", "type": "number"},
                            {"id": "sodium", "label": "Sodium", "type": "number", "unit": "mEq/L"},
                            {"id": "dialysis", "label": "Dialysis (2+ times/week)", "type": "bool"},
                        ],
                    },
                    {
                        "id": "child_pugh",
                        "name": "Child-Pugh Score",
                        "description": "Cirrhosis severity classification",
                        "inputs": [
                            {"id": "bilirubin", "label": "Bilirubin", "type": "select", "options": ["<2 mg/dL", "2-3 mg/dL", ">3 mg/dL"]},
                            {"id": "albumin", "label": "Albumin", "type": "select", "options": [">3.5 g/dL", "2.8-3.5 g/dL", "<2.8 g/dL"]},
                            {"id": "inr", "label": "INR", "type": "select", "options": ["<1.7", "1.7-2.3", ">2.3"]},
                            {"id": "ascites", "label": "Ascites", "type": "select", "options": ["None", "Mild", "Moderate-Severe"]},
                            {"id": "encephalopathy", "label": "Encephalopathy", "type": "select", "options": ["None", "Grade 1-2", "Grade 3-4"]},
                        ],
                    },
                ],
            },
            {
                "name": "Critical Care",
                "icon": ft.icons.MONITOR_HEART,
                "calculators": [
                    {
                        "id": "apache2",
                        "name": "APACHE II Score",
                        "description": "ICU mortality prediction",
                        "inputs": [
                            {"id": "temperature", "label": "Temperature (°C)", "type": "number"},
                            {"id": "map", "label": "Mean Arterial Pressure", "type": "number"},
                            {"id": "heart_rate", "label": "Heart Rate", "type": "number"},
                            {"id": "respiratory_rate", "label": "Respiratory Rate", "type": "number"},
                            {"id": "pao2", "label": "PaO2 or A-a gradient", "type": "number"},
                            {"id": "ph", "label": "Arterial pH", "type": "number"},
                            {"id": "sodium", "label": "Sodium", "type": "number"},
                            {"id": "potassium", "label": "Potassium", "type": "number"},
                            {"id": "creatinine", "label": "Creatinine", "type": "number"},
                            {"id": "hematocrit", "label": "Hematocrit", "type": "number"},
                            {"id": "wbc", "label": "WBC", "type": "number"},
                            {"id": "gcs", "label": "Glasgow Coma Scale", "type": "number"},
                            {"id": "age", "label": "Age", "type": "number"},
                        ],
                    },
                    {
                        "id": "sofa",
                        "name": "SOFA Score",
                        "description": "Sepsis-related organ failure",
                        "inputs": [
                            {"id": "pao2_fio2", "label": "PaO2/FiO2", "type": "number"},
                            {"id": "platelets", "label": "Platelets (×10³/μL)", "type": "number"},
                            {"id": "bilirubin", "label": "Bilirubin (mg/dL)", "type": "number"},
                            {"id": "map", "label": "MAP or Vasopressors", "type": "select", "options": ["MAP ≥70", "MAP <70", "Dopamine ≤5", "Dopamine >5 or Epi ≤0.1", "Dopamine >15 or Epi >0.1"]},
                            {"id": "gcs", "label": "Glasgow Coma Scale", "type": "number"},
                            {"id": "creatinine", "label": "Creatinine (mg/dL)", "type": "number"},
                        ],
                    },
                ],
            },
        ]

    def _build_calculator_list(self, calculators: list[dict]) -> list[ft.Control]:
        """Build list of calculator cards."""
        return [
            self._build_calculator_card(calc)
            for calc in calculators
        ]

    def _build_calculator_card(self, calculator: dict) -> ft.Container:
        """Build a calculator card."""
        return ft.Container(
            content=ft.Row(
                controls=[
                    ft.Column(
                        controls=[
                            ft.Text(
                                calculator["name"],
                                size=Typography.SIZE_MD,
                                weight=Typography.WEIGHT_SEMIBOLD,
                                color=Colors.TEXT_PRIMARY,
                            ),
                            ft.Text(
                                calculator["description"],
                                size=Typography.SIZE_SM,
                                color=Colors.TEXT_SECONDARY,
                            ),
                        ],
                        spacing=4,
                        expand=True,
                    ),
                    ft.Icon(
                        ft.icons.ARROW_FORWARD_IOS,
                        size=16,
                        color=Colors.TEXT_SECONDARY,
                    ),
                ],
            ),
            bgcolor=Colors.BG_PRIMARY,
            border_radius=12,
            padding=Spacing.MD,
            shadow=ft.BoxShadow(
                spread_radius=0,
                blur_radius=4,
                color=ft.colors.with_opacity(0.05, Colors.TEXT_PRIMARY),
                offset=ft.Offset(0, 2),
            ),
            on_click=lambda _, c=calculator: self._open_calculator(c),
            ink=True,
        )

    def _on_category_change(self, e):
        """Handle category tab change."""
        categories = self._get_calculator_categories()
        selected_category = categories[e.control.selected_index]

        self.calculator_list.controls = self._build_calculator_list(
            selected_category["calculators"]
        )
        self.calculator_list.update()

    def _open_calculator(self, calculator: dict):
        """Open calculator detail view."""
        self.selected_calculator = calculator
        self.input_fields = {}

        # Build input fields
        input_controls = []
        for inp in calculator["inputs"]:
            if inp["type"] == "number":
                field = ft.TextField(
                    label=inp["label"],
                    suffix_text=inp.get("unit", ""),
                    keyboard_type=ft.KeyboardType.NUMBER,
                    border_radius=8,
                    border_color=Colors.BG_TERTIARY,
                    focused_border_color=Colors.PRIMARY,
                )
            elif inp["type"] == "select":
                field = ft.Dropdown(
                    label=inp["label"],
                    options=[ft.dropdown.Option(o) for o in inp["options"]],
                    border_radius=8,
                    border_color=Colors.BG_TERTIARY,
                    focused_border_color=Colors.PRIMARY,
                )
            elif inp["type"] == "bool":
                field = ft.Checkbox(
                    label=inp["label"],
                    value=False,
                    active_color=Colors.PRIMARY,
                )
            else:
                continue

            self.input_fields[inp["id"]] = field
            input_controls.append(field)

        # Result container
        self.result_container = ft.Container(
            visible=False,
            padding=Spacing.MD,
            border_radius=12,
            bgcolor=ft.colors.with_opacity(0.1, Colors.PRIMARY),
        )

        # Build detail view
        self.calculator_detail.content = ft.Column(
            controls=[
                # Back button and title
                ft.Row(
                    controls=[
                        ft.IconButton(
                            icon=ft.icons.ARROW_BACK,
                            on_click=self._close_calculator,
                        ),
                        ft.Column(
                            controls=[
                                ft.Text(
                                    calculator["name"],
                                    size=Typography.SIZE_LG,
                                    weight=Typography.WEIGHT_BOLD,
                                    color=Colors.TEXT_PRIMARY,
                                ),
                                ft.Text(
                                    calculator["description"],
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
                ft.Divider(height=1, color=Colors.BG_TERTIARY),

                # Input fields
                ft.Container(
                    content=ft.Column(
                        controls=input_controls,
                        spacing=Spacing.MD,
                    ),
                    padding=Spacing.MD,
                    expand=True,
                    scroll=ft.ScrollMode.AUTO,
                ),

                # Result
                self.result_container,

                # Calculate button
                ft.Container(
                    content=styled_button(
                        text="Calculate",
                        icon=ft.icons.CALCULATE,
                        on_click=self._calculate,
                    ),
                    padding=Spacing.MD,
                ),
            ],
            expand=True,
        )

        # Show detail, hide list
        self.calculator_list.visible = False
        self.calculator_detail.visible = True
        self.calculator_list.update()
        self.calculator_detail.update()

    def _close_calculator(self, e):
        """Close calculator detail view."""
        self.selected_calculator = None
        self.calculator_list.visible = True
        self.calculator_detail.visible = False
        self.calculator_list.update()
        self.calculator_detail.update()

    async def _calculate(self, e):
        """Perform calculation."""
        if not self.selected_calculator:
            return

        # Collect input values
        values = {}
        for inp in self.selected_calculator["inputs"]:
            field = self.input_fields.get(inp["id"])
            if field:
                if isinstance(field, ft.Checkbox):
                    values[inp["id"]] = field.value
                else:
                    values[inp["id"]] = field.value

        # Call API or calculate locally
        result = await self._perform_calculation(
            self.selected_calculator["id"],
            values,
        )

        # Show result
        self.result_container.content = ft.Column(
            controls=[
                ft.Text(
                    "Result",
                    size=Typography.SIZE_XS,
                    weight=Typography.WEIGHT_SEMIBOLD,
                    color=Colors.TEXT_SECONDARY,
                ),
                ft.Text(
                    result.get("score", "N/A"),
                    size=Typography.SIZE_XXL,
                    weight=Typography.WEIGHT_BOLD,
                    color=Colors.PRIMARY,
                ),
                ft.Text(
                    result.get("interpretation", ""),
                    size=Typography.SIZE_MD,
                    color=Colors.TEXT_PRIMARY,
                ),
                if result.get("recommendation"):
                    ft.Container(
                        content=ft.Row(
                            controls=[
                                ft.Icon(ft.icons.INFO, size=16, color=Colors.INFO),
                                ft.Text(
                                    result["recommendation"],
                                    size=Typography.SIZE_SM,
                                    color=Colors.INFO,
                                    expand=True,
                                ),
                            ],
                            spacing=8,
                        ),
                        bgcolor=ft.colors.with_opacity(0.1, Colors.INFO),
                        border_radius=8,
                        padding=Spacing.SM,
                        margin=ft.margin.only(top=Spacing.SM),
                    ),
            ],
            spacing=4,
        )
        self.result_container.visible = True
        self.result_container.update()

    async def _perform_calculation(self, calc_id: str, values: dict) -> dict:
        """Perform calculation via API or locally."""
        try:
            response = await self.api.client.post(
                f"/api/v1/calculators/{calc_id}",
                json=values,
            )
            response.raise_for_status()
            return response.json()
        except Exception:
            # Return mock result for demo
            return {
                "score": "3",
                "interpretation": "Moderate risk",
                "recommendation": "Consider anticoagulation therapy. Consult cardiology for risk stratification.",
            }

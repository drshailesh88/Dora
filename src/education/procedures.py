"""
Procedure Guide Generator

Generates pre-procedure preparation instructions and post-procedure care guides.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta

from ..llm.synthesizer import Synthesizer
from .models import (
    ProcedurePrep,
    PostCareGuide,
    WarningSign,
    SeverityLevel,
    DosDonts,
    ReadingLevel,
)


class ProcedureGuideGenerator:
    """Generates procedure preparation and post-care guides."""

    def __init__(self, llm_synthesizer: Optional[Synthesizer] = None):
        """
        Initialize procedure guide generator.

        Args:
            llm_synthesizer: LLM for generating content
        """
        self.llm = llm_synthesizer

        # Common procedures with preparation instructions
        self.procedure_library = {
            "colonoscopy": {
                "type": "diagnostic",
                "prep_days": [
                    {
                        "day": "3 days before",
                        "instructions": [
                            "Stop eating high-fiber foods (nuts, seeds, raw vegetables)",
                            "Stop taking iron supplements",
                        ],
                    },
                    {
                        "day": "1 day before",
                        "instructions": [
                            "Eat only light, low-fiber breakfast",
                            "Switch to clear liquids only after breakfast",
                            "Start bowel prep as instructed",
                            "Drink plenty of clear fluids",
                        ],
                    },
                    {
                        "day": "Day of procedure",
                        "instructions": [
                            "Nothing to eat or drink after midnight",
                            "Take only approved medications with small sip of water",
                        ],
                    },
                ],
                "fasting": "Nothing to eat or drink after midnight before procedure",
                "what_to_bring": [
                    "Photo ID",
                    "Insurance card",
                    "List of current medications",
                    "Someone to drive you home",
                ],
            },
            "endoscopy": {
                "type": "diagnostic",
                "prep_days": [
                    {
                        "day": "Night before",
                        "instructions": [
                            "Eat a light dinner",
                            "No food after midnight",
                        ],
                    },
                    {
                        "day": "Day of procedure",
                        "instructions": [
                            "Nothing to eat or drink (not even water)",
                        ],
                    },
                ],
                "fasting": "No food or drink for 8 hours before procedure",
            },
            "surgery": {
                "type": "surgical",
                "prep_days": [
                    {
                        "day": "Week before",
                        "instructions": [
                            "Inform doctor of all medications and supplements",
                            "Stop blood thinners if instructed",
                            "Arrange for help at home after surgery",
                        ],
                    },
                    {
                        "day": "Night before",
                        "instructions": [
                            "Shower with antibacterial soap",
                            "No food or drink after midnight",
                            "Get good sleep",
                        ],
                    },
                    {
                        "day": "Day of surgery",
                        "instructions": [
                            "Shower again with antibacterial soap",
                            "Don't use lotions, makeup, or jewelry",
                            "Wear comfortable, loose clothing",
                        ],
                    },
                ],
                "fasting": "Nothing to eat or drink after midnight",
            },
            "ct_scan": {
                "type": "diagnostic",
                "prep_days": [
                    {
                        "day": "Day of scan",
                        "instructions": [
                            "Wear comfortable clothing without metal",
                            "Remove jewelry and metal objects",
                        ],
                    },
                ],
            },
            "mri": {
                "type": "diagnostic",
                "prep_days": [
                    {
                        "day": "Day of MRI",
                        "instructions": [
                            "Remove all metal objects (jewelry, watches, piercings)",
                            "Inform staff of any metal implants",
                            "Wear clothing without metal zippers or buttons",
                        ],
                    },
                ],
            },
        }

    def generate_prep_guide(
        self,
        procedure_name: str,
        procedure_date: Optional[datetime] = None,
        special_instructions: Optional[List[str]] = None,
        reading_level: ReadingLevel = ReadingLevel.BASIC,
        language: str = "en",
    ) -> ProcedurePrep:
        """
        Generate pre-procedure preparation guide.

        Args:
            procedure_name: Name of procedure
            procedure_date: When procedure is scheduled
            special_instructions: Additional instructions
            reading_level: Target reading level
            language: Language code

        Returns:
            Procedure preparation guide
        """
        procedure_key = procedure_name.lower().strip()

        # Get from library if available
        if procedure_key in self.procedure_library:
            template = self.procedure_library[procedure_key]

            prep = ProcedurePrep(
                procedure_name=procedure_name,
                procedure_type=template.get("type"),
                days_before_instructions=template.get("prep_days", []),
                fasting_instructions=template.get("fasting"),
                what_to_bring=template.get("what_to_bring", []),
                reading_level=reading_level,
                language=language,
            )

        else:
            # Generic prep guide
            prep = ProcedurePrep(
                procedure_name=procedure_name,
                reading_level=reading_level,
                language=language,
            )

        # Add standard items if not present
        if not prep.what_to_bring:
            prep.what_to_bring = self._get_standard_items_to_bring()

        # Add medication adjustments
        prep.medication_adjustments = self._get_medication_adjustments(procedure_name)

        # Add what to expect
        prep.what_happens_during = self._get_procedure_description(procedure_name)

        # Add special instructions if provided
        if special_instructions:
            if prep.days_before_instructions:
                prep.days_before_instructions[-1]["instructions"].extend(
                    special_instructions
                )
            else:
                prep.days_before_instructions = [
                    {"day": "Before procedure", "instructions": special_instructions}
                ]

        return prep

    def generate_post_care_guide(
        self,
        procedure_name: str,
        condition: Optional[str] = None,
        discharge_date: Optional[datetime] = None,
        special_instructions: Optional[List[str]] = None,
        reading_level: ReadingLevel = ReadingLevel.BASIC,
        language: str = "en",
    ) -> PostCareGuide:
        """
        Generate post-procedure care guide.

        Args:
            procedure_name: Name of procedure
            condition: Condition treated
            discharge_date: Discharge date
            special_instructions: Additional instructions
            reading_level: Target reading level
            language: Language code

        Returns:
            Post-care guide
        """
        title = f"After Your {procedure_name}"

        # Generate recovery timeline
        recovery_timeline = self._generate_recovery_timeline(procedure_name)

        # Generate care instructions
        post_care = PostCareGuide(
            title=title,
            condition_or_procedure=procedure_name,
            recovery_timeline=recovery_timeline,
            reading_level=reading_level,
            language=language,
        )

        # Add wound care if applicable
        if self._is_surgical_procedure(procedure_name):
            post_care.wound_care_instructions = self._get_wound_care_instructions()

        # Add activity restrictions
        post_care.activity_restrictions = self._get_activity_restrictions(procedure_name)
        post_care.when_can_resume = self._get_activity_resumption_timeline(procedure_name)

        # Add diet instructions
        post_care.diet_instructions = self._get_diet_instructions(procedure_name)

        # Add pain management
        post_care.pain_management = self._get_pain_management_instructions()

        # Add warning signs
        post_care.warning_signs = self._get_warning_signs(procedure_name)
        post_care.when_to_call_doctor = self._get_when_to_call_doctor()
        post_care.emergency_signs = self._get_emergency_signs()

        # Add follow-up
        post_care.follow_up_appointments = self._get_follow_up_schedule(procedure_name)

        # Add do's and don'ts
        post_care.dos_donts = self._get_post_procedure_dos_donts(procedure_name)

        # Add special instructions if provided
        if special_instructions:
            post_care.wound_care_instructions.extend(special_instructions)

        return post_care

    def _get_standard_items_to_bring(self) -> List[str]:
        """Get standard items to bring to procedure."""
        return [
            "Photo ID",
            "Insurance card",
            "List of current medications",
            "List of allergies",
            "Someone to drive you home (if sedation used)",
            "Comfortable, loose clothing",
        ]

    def _get_medication_adjustments(self, procedure_name: str) -> List[str]:
        """Get medication adjustment instructions."""
        adjustments = [
            "Continue regular medications unless told otherwise",
            "Bring list of all medications to procedure",
        ]

        # Add specific adjustments based on procedure
        if "surgery" in procedure_name.lower():
            adjustments.extend([
                "Stop blood thinners if instructed by doctor",
                "Stop aspirin if instructed (usually 7 days before)",
                "Take only approved medications on morning of surgery",
            ])

        return adjustments

    def _get_procedure_description(self, procedure_name: str) -> List[str]:
        """Get what happens during procedure."""
        procedure_lower = procedure_name.lower()

        descriptions = {
            "colonoscopy": [
                "You will lie on your side",
                "You will receive sedation to make you comfortable",
                "Doctor inserts a thin, flexible tube with camera",
                "Doctor examines your colon",
                "If polyps found, they may be removed",
                "Procedure takes 30-60 minutes",
            ],
            "endoscopy": [
                "You will receive sedation",
                "Doctor inserts thin tube through mouth",
                "Camera allows doctor to see inside",
                "Biopsies may be taken if needed",
                "Procedure takes 15-30 minutes",
            ],
            "ct_scan": [
                "You will lie on a table",
                "Table moves through scanner ring",
                "You may receive contrast dye",
                "Need to stay still during scan",
                "Scan takes 10-30 minutes",
            ],
        }

        for key, desc in descriptions.items():
            if key in procedure_lower:
                return desc

        return [
            "Your doctor will explain the procedure",
            "You may receive anesthesia or sedation",
            "Medical team will monitor you throughout",
        ]

    def _is_surgical_procedure(self, procedure_name: str) -> bool:
        """Check if procedure is surgical."""
        surgical_keywords = ["surgery", "surgical", "operation", "removal", "repair"]
        return any(kw in procedure_name.lower() for kw in surgical_keywords)

    def _generate_recovery_timeline(self, procedure_name: str) -> List[Dict[str, str]]:
        """Generate recovery timeline."""
        if self._is_surgical_procedure(procedure_name):
            return [
                {
                    "period": "First 24 hours",
                    "expect": "Rest, some pain or discomfort, grogginess from anesthesia",
                },
                {
                    "period": "First week",
                    "expect": "Gradual increase in activity, reducing pain, follow wound care",
                },
                {
                    "period": "2-4 weeks",
                    "expect": "Most daily activities resumed, continued healing",
                },
            ]
        else:
            return [
                {
                    "period": "First few hours",
                    "expect": "Rest and recovery from sedation if used",
                },
                {
                    "period": "Next 24 hours",
                    "expect": "Resume normal activities as tolerated",
                },
            ]

    def _get_wound_care_instructions(self) -> List[str]:
        """Get wound care instructions."""
        return [
            "Keep wound clean and dry",
            "Wash hands before touching wound area",
            "Change dressing as instructed",
            "Watch for signs of infection (redness, swelling, warmth, pus)",
            "Don't remove steri-strips - let them fall off naturally",
            "Avoid soaking wound in water (no baths, swimming)",
        ]

    def _get_activity_restrictions(self, procedure_name: str) -> List[str]:
        """Get activity restrictions."""
        if self._is_surgical_procedure(procedure_name):
            return [
                "No heavy lifting (over 10 pounds) for 2 weeks",
                "No strenuous exercise for 2-4 weeks",
                "No driving while taking narcotic pain medication",
                "Avoid activities that strain surgical area",
                "Rest when tired",
            ]
        else:
            return [
                "No driving for 24 hours if sedation was used",
                "Rest for remainder of day",
                "Avoid strenuous activity for 24 hours",
            ]

    def _get_activity_resumption_timeline(
        self, procedure_name: str
    ) -> Dict[str, str]:
        """Get when activities can be resumed."""
        if self._is_surgical_procedure(procedure_name):
            return {
                "Work": "1-2 weeks (or as directed)",
                "Driving": "When off pain medication and cleared by doctor",
                "Exercise": "Light walking immediately, full exercise 4-6 weeks",
                "Lifting": "Light lifting after 2 weeks, heavy lifting after 6 weeks",
                "Sexual activity": "2-4 weeks or when comfortable",
            }
        else:
            return {
                "Work": "Next day",
                "Driving": "24 hours after sedation",
                "Exercise": "Next day",
            }

    def _get_diet_instructions(self, procedure_name: str) -> List[str]:
        """Get diet instructions."""
        procedure_lower = procedure_name.lower()

        if "colonoscopy" in procedure_lower:
            return [
                "Start with clear liquids",
                "Progress to soft, bland foods",
                "Return to normal diet gradually over 1-2 days",
                "Drink plenty of fluids",
            ]
        elif "surgery" in procedure_lower:
            return [
                "Start with clear liquids",
                "Advance to soft foods as tolerated",
                "Eat small, frequent meals",
                "Avoid spicy, fatty, or hard-to-digest foods initially",
                "Stay hydrated",
            ]
        else:
            return [
                "Resume normal diet as tolerated",
                "Start with light foods if needed",
                "Stay well hydrated",
            ]

    def _get_pain_management_instructions(self) -> List[str]:
        """Get pain management instructions."""
        return [
            "Take pain medication as prescribed",
            "Don't wait until pain is severe",
            "Use ice packs as directed (wrapped in towel)",
            "Rest and elevate affected area if applicable",
            "Call doctor if pain is not controlled",
        ]

    def _get_warning_signs(self, procedure_name: str) -> List[WarningSign]:
        """Get warning signs to watch for."""
        warnings = [
            WarningSign(
                symptom="Fever over 101°F (38.3°C)",
                action="Call your doctor",
                urgency=SeverityLevel.SEVERE,
            ),
            WarningSign(
                symptom="Increasing pain not relieved by medication",
                action="Call your doctor",
                urgency=SeverityLevel.SEVERE,
            ),
        ]

        if self._is_surgical_procedure(procedure_name):
            warnings.extend([
                WarningSign(
                    symptom="Signs of infection (redness, swelling, pus, bad odor)",
                    action="Call your doctor",
                    urgency=SeverityLevel.SEVERE,
                ),
                WarningSign(
                    symptom="Wound opens or bleeding doesn't stop",
                    action="Call your doctor or go to ER",
                    urgency=SeverityLevel.EMERGENCY,
                ),
            ])

        return warnings

    def _get_when_to_call_doctor(self) -> List[str]:
        """Get when to call doctor."""
        return [
            "Fever or chills",
            "Increasing pain or swelling",
            "Redness or warmth at site",
            "Drainage or bad odor",
            "Nausea or vomiting that won't stop",
            "Unable to eat or drink",
            "Any concerns or questions",
        ]

    def _get_emergency_signs(self) -> List[str]:
        """Get emergency signs requiring immediate attention."""
        return [
            "Chest pain or difficulty breathing",
            "Heavy bleeding that won't stop",
            "Severe pain not relieved by medication",
            "Signs of stroke (weakness, confusion, trouble speaking)",
            "Loss of consciousness",
            "Severe allergic reaction (difficulty breathing, severe swelling)",
        ]

    def _get_follow_up_schedule(self, procedure_name: str) -> List[Dict[str, str]]:
        """Get follow-up appointment schedule."""
        if self._is_surgical_procedure(procedure_name):
            return [
                {
                    "when": "1-2 weeks after surgery",
                    "purpose": "Wound check and suture removal if needed",
                },
                {
                    "when": "4-6 weeks after surgery",
                    "purpose": "Post-operative check-up",
                },
            ]
        else:
            return [
                {
                    "when": "As directed by doctor",
                    "purpose": "Discuss results and next steps",
                },
            ]

    def _get_post_procedure_dos_donts(self, procedure_name: str) -> DosDonts:
        """Get do's and don'ts after procedure."""
        dos = [
            "Rest and get plenty of sleep",
            "Follow all instructions",
            "Take medications as prescribed",
            "Keep follow-up appointments",
            "Ask questions if unsure",
        ]

        donts = [
            "Don't ignore warning signs",
            "Don't skip medications",
            "Don't do restricted activities",
            "Don't hesitate to call with concerns",
        ]

        if self._is_surgical_procedure(procedure_name):
            dos.extend([
                "Keep wound clean and dry",
                "Walk regularly to prevent blood clots",
            ])
            donts.extend([
                "Don't get wound wet",
                "Don't lift heavy objects",
                "Don't smoke",
            ])

        return DosDonts(dos=dos, donts=donts)

"""Voice UI components for Dora desktop application."""

import logging
import threading
from typing import Callable, Optional

import flet as ft
import numpy as np

from src.voice.service import VoiceService, VoiceServiceMode

logger = logging.getLogger(__name__)


class VoiceControlPanel(ft.UserControl):
    """
    Voice control panel with microphone, waveform, and status.

    Features:
    - Push-to-talk button
    - Wake word mode toggle
    - Ambient dictation mode
    - Waveform visualization
    - Volume indicator
    - Status display
    """

    def __init__(
        self,
        voice_service: VoiceService,
        on_response: Callable[[str], None] | None = None,
    ):
        """
        Initialize voice control panel.

        Args:
            voice_service: Voice service instance.
            on_response: Callback when response received.
        """
        super().__init__()

        self.voice_service = voice_service
        self.on_response_callback = on_response

        # UI elements
        self.status_text = ft.Text("Ready", size=14, color=ft.colors.GREEN)
        self.transcription_text = ft.Text("", size=12, italic=True)
        self.mic_button = None
        self.mode_dropdown = None
        self.ambient_button = None
        self.waveform = None
        self.volume_indicator = None

        # State
        self._recording = False
        self._ambient_active = False

    def build(self):
        """Build the voice control UI."""
        # Microphone button (push-to-talk)
        self.mic_button = ft.IconButton(
            icon=ft.icons.MIC,
            icon_size=40,
            tooltip="Hold to speak (Push-to-talk)",
            on_click=self._toggle_recording,
            bgcolor=ft.colors.BLUE_ACCENT,
            icon_color=ft.colors.WHITE,
        )

        # Mode selector
        self.mode_dropdown = ft.Dropdown(
            width=200,
            label="Voice Mode",
            value="push_to_talk",
            options=[
                ft.dropdown.Option("push_to_talk", "Push-to-Talk"),
                ft.dropdown.Option("wake_word", "Wake Word (Hey DocAssist)"),
                ft.dropdown.Option("continuous", "Continuous (Ambient)"),
            ],
            on_change=self._on_mode_changed,
        )

        # Ambient dictation button
        self.ambient_button = ft.ElevatedButton(
            "Start Ambient Dictation",
            icon=ft.icons.RECORD_VOICE_OVER,
            on_click=self._toggle_ambient,
        )

        # Waveform visualization (placeholder)
        self.waveform = ft.Container(
            content=ft.Row(
                [
                    ft.Container(
                        width=4,
                        height=20,
                        bgcolor=ft.colors.BLUE_200,
                        border_radius=2,
                    )
                    for _ in range(20)
                ],
                spacing=2,
            ),
            height=40,
            alignment=ft.alignment.center,
        )

        # Volume indicator
        self.volume_indicator = ft.ProgressBar(
            width=200,
            value=0,
            color=ft.colors.GREEN,
        )

        # Layout
        return ft.Container(
            content=ft.Column(
                [
                    # Title
                    ft.Text("Voice Assistant", size=20, weight=ft.FontWeight.BOLD),
                    ft.Divider(),
                    # Status
                    ft.Row(
                        [
                            ft.Icon(ft.icons.INFO_OUTLINE, color=ft.colors.BLUE),
                            self.status_text,
                        ],
                        spacing=10,
                    ),
                    # Transcription
                    ft.Container(
                        content=self.transcription_text,
                        padding=10,
                        bgcolor=ft.colors.GREY_100,
                        border_radius=5,
                        height=60,
                    ),
                    # Waveform
                    self.waveform,
                    # Volume
                    ft.Row(
                        [
                            ft.Icon(ft.icons.VOLUME_UP),
                            self.volume_indicator,
                        ],
                        spacing=10,
                    ),
                    # Controls
                    ft.Row(
                        [
                            self.mic_button,
                            self.mode_dropdown,
                        ],
                        spacing=20,
                        alignment=ft.MainAxisAlignment.CENTER,
                    ),
                    # Ambient dictation
                    ft.Container(
                        content=self.ambient_button,
                        alignment=ft.alignment.center,
                        padding=ft.padding.only(top=10),
                    ),
                ],
                spacing=15,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            padding=20,
            border=ft.border.all(1, ft.colors.GREY_300),
            border_radius=10,
        )

    def _toggle_recording(self, e):
        """Toggle push-to-talk recording."""
        if not self._recording:
            # Start recording
            self._recording = True
            self.mic_button.icon = ft.icons.MIC_OFF
            self.mic_button.bgcolor = ft.colors.RED_ACCENT
            self.status_text.value = "Listening..."
            self.status_text.color = ft.colors.RED
            self.update()

            # Start voice service in background
            threading.Thread(target=self._record_and_process, daemon=True).start()

        else:
            # Stop recording
            self._recording = False
            self.mic_button.icon = ft.icons.MIC
            self.mic_button.bgcolor = ft.colors.BLUE_ACCENT
            self.status_text.value = "Processing..."
            self.status_text.color = ft.colors.ORANGE
            self.update()

    def _record_and_process(self):
        """Record audio and process through voice service."""
        try:
            # This is a simplified version - in production, integrate with actual audio recording
            # For now, we'll use text input simulation

            # Simulate recording delay
            import time

            time.sleep(2)

            # For demo, use text input instead of actual audio
            # In production, capture audio and call voice_service.process_audio()

            # Stop recording indicator
            self._recording = False
            self.mic_button.icon = ft.icons.MIC
            self.mic_button.bgcolor = ft.colors.BLUE_ACCENT
            self.status_text.value = "Ready"
            self.status_text.color = ft.colors.GREEN
            self.update()

        except Exception as e:
            logger.error(f"Recording error: {e}")
            self._recording = False
            self.status_text.value = f"Error: {str(e)}"
            self.status_text.color = ft.colors.RED
            self.update()

    def _on_mode_changed(self, e):
        """Handle voice mode change."""
        mode = e.control.value

        if mode == "wake_word":
            self.voice_service.set_mode(VoiceServiceMode.WAKE_WORD)
            self.status_text.value = "Listening for 'Hey DocAssist'..."
            self.status_text.color = ft.colors.BLUE

        elif mode == "push_to_talk":
            self.voice_service.set_mode(VoiceServiceMode.PUSH_TO_TALK)
            self.status_text.value = "Ready (Push-to-talk)"
            self.status_text.color = ft.colors.GREEN

        elif mode == "continuous":
            self.voice_service.set_mode(VoiceServiceMode.CONTINUOUS)
            self.status_text.value = "Continuous listening..."
            self.status_text.color = ft.colors.PURPLE

        self.update()

    def _toggle_ambient(self, e):
        """Toggle ambient dictation mode."""
        if not self._ambient_active:
            # Start ambient dictation
            self.voice_service.start_ambient_dictation()
            self._ambient_active = True
            self.ambient_button.text = "Stop Ambient Dictation"
            self.ambient_button.icon = ft.icons.STOP
            self.status_text.value = "Ambient dictation active..."
            self.status_text.color = ft.colors.PURPLE

        else:
            # Stop ambient dictation
            soap_note = self.voice_service.stop_ambient_dictation()
            self._ambient_active = False
            self.ambient_button.text = "Start Ambient Dictation"
            self.ambient_button.icon = ft.icons.RECORD_VOICE_OVER
            self.status_text.value = "SOAP note generated"
            self.status_text.color = ft.colors.GREEN

            # Show SOAP note dialog
            if soap_note:
                self._show_soap_note(soap_note)

        self.update()

    def _show_soap_note(self, soap_note: dict):
        """Show SOAP note in dialog."""
        dialog = ft.AlertDialog(
            title=ft.Text("Generated SOAP Note"),
            content=ft.Container(
                content=ft.Column(
                    [
                        ft.Text("Subjective:", weight=ft.FontWeight.BOLD),
                        ft.Text("\n".join(soap_note.get("subjective", [])) or "None"),
                        ft.Divider(),
                        ft.Text("Objective:", weight=ft.FontWeight.BOLD),
                        ft.Text("\n".join(soap_note.get("objective", [])) or "None"),
                        ft.Divider(),
                        ft.Text("Assessment:", weight=ft.FontWeight.BOLD),
                        ft.Text("\n".join(soap_note.get("assessment", [])) or "None"),
                        ft.Divider(),
                        ft.Text("Plan:", weight=ft.FontWeight.BOLD),
                        ft.Text("\n".join(soap_note.get("plan", [])) or "None"),
                    ],
                    scroll=ft.ScrollMode.AUTO,
                ),
                width=600,
                height=400,
            ),
            actions=[
                ft.TextButton("Close", on_click=lambda e: self._close_dialog()),
                ft.ElevatedButton("Copy to Clipboard", on_click=lambda e: self._copy_soap_note(soap_note)),
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

    def _copy_soap_note(self, soap_note: dict):
        """Copy SOAP note to clipboard."""
        import pyperclip

        text = soap_note.get("text", "")
        pyperclip.copy(text)

        # Show snackbar
        self.page.snack_bar = ft.SnackBar(ft.Text("SOAP note copied to clipboard!"))
        self.page.snack_bar.open = True
        self.page.update()

        self._close_dialog()

    def on_transcription(self, text: str):
        """Handle transcription event."""
        self.transcription_text.value = f'"{text}"'
        self.update()

    def on_response(self, response: str):
        """Handle response event."""
        self.status_text.value = "Speaking response..."
        self.status_text.color = ft.colors.BLUE
        self.update()

        if self.on_response_callback:
            self.on_response_callback(response)

    def on_error(self, error: str):
        """Handle error event."""
        self.status_text.value = f"Error: {error}"
        self.status_text.color = ft.colors.RED
        self.update()


class VoiceTextInput(ft.UserControl):
    """
    Voice-enabled text input with microphone button.

    Can be used in any text input field to add voice input capability.
    """

    def __init__(
        self,
        voice_service: VoiceService,
        label: str = "Ask a question",
        on_submit: Callable[[str], None] | None = None,
    ):
        """
        Initialize voice text input.

        Args:
            voice_service: Voice service instance.
            label: Input label.
            on_submit: Callback when text submitted.
        """
        super().__init__()

        self.voice_service = voice_service
        self.label = label
        self.on_submit_callback = on_submit

        self.text_field = None
        self.mic_button = None

    def build(self):
        """Build voice text input UI."""
        # Text field
        self.text_field = ft.TextField(
            label=self.label,
            multiline=False,
            on_submit=self._on_text_submit,
            expand=True,
        )

        # Microphone button
        self.mic_button = ft.IconButton(
            icon=ft.icons.MIC,
            tooltip="Voice input",
            on_click=self._on_voice_click,
        )

        return ft.Row(
            [
                self.text_field,
                self.mic_button,
            ],
            spacing=10,
        )

    def _on_text_submit(self, e):
        """Handle text submission."""
        if self.on_submit_callback and self.text_field.value:
            self.on_submit_callback(self.text_field.value)
            self.text_field.value = ""
            self.update()

    def _on_voice_click(self, e):
        """Handle voice input click."""
        # Show recording dialog
        dialog = ft.AlertDialog(
            title=ft.Text("Voice Input"),
            content=ft.Column(
                [
                    ft.Icon(ft.icons.MIC, size=60, color=ft.colors.RED),
                    ft.Text("Listening...", size=16),
                    ft.ProgressRing(),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=20,
            ),
        )

        self.page.dialog = dialog
        dialog.open = True
        self.page.update()

        # Simulate voice input (in production, use actual voice recording)
        # For now, just close the dialog after a delay
        import time
        import threading

        def simulate_voice():
            time.sleep(2)
            dialog.open = False
            self.page.update()

        threading.Thread(target=simulate_voice, daemon=True).start()

    def set_value(self, value: str):
        """Set text field value."""
        self.text_field.value = value
        self.update()

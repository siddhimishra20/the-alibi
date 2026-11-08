from textual.app import ComposeResult
from textual.screen import ModalScreen
from textual.widgets import Static, Button, Select, RadioSet, RadioButton, Label
from textual.containers import Container, Vertical, Horizontal, VerticalScroll
from rich.panel import Panel

class AccuseModalScreen(ModalScreen):
    """Interactive accusation modal to select contradictory quote and target."""

    BINDINGS = [
        ("escape", "dismiss_cancel", "Cancel Accusation")
    ]

    def __init__(self, game_manager):
        super().__init__()
        self.game_manager = game_manager
        self.selected_quote = ""
        self.selected_target = ""
        self.is_dossier_fact = True

    def compose(self) -> ComposeResult:
        session = self.game_manager.session
        quotes = []
        if session:
            for s in session.transcript:
                quotes.append((f"Turn {s.turn_number}: \"{s.answer[:60]}...\"", s.answer))

        dossier_options = []
        if session:
            for f in session.case.dossier:
                dossier_options.append((f"[{f.id.upper()}] {f.text[:65]}...", f.text))

        with Container(id="accuse-modal-container"):
            yield Static("FORMAL CONTRADICTION ACCUSATION", classes="section-header", id="accuse-title")
            
            with VerticalScroll(id="accuse-scroll"):
                yield Label("[bold cyan]Step 1: Select the Suspect's Contradictory Statement:[/bold cyan]")
                if quotes:
                    yield Select(options=quotes, id="select-quote", prompt="Select suspect quote from transcript...")
                else:
                    yield Static("[dim red]No suspect statements recorded yet! Ask questions first.[/dim red]")

                yield Label("\n[bold cyan]Step 2: Select What It Contradicts:[/bold cyan]")
                yield Select(options=dossier_options, id="select-target", prompt="Select verified fact from dossier...")

                yield Static("", id="accuse-status-msg")

            with Horizontal(id="accuse-buttons"):
                yield Button("SUBMIT ACCUSATION", id="btn-submit-accuse", variant="error")
                yield Button("Cancel (Esc)", id="btn-cancel-accuse", variant="default")

    def action_dismiss_cancel(self):
        self.dismiss(None)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-cancel-accuse":
            self.dismiss(None)
        elif event.button.id == "btn-submit-accuse":
            quote_select = self.query_one("#select-quote", Select)
            target_select = self.query_one("#select-target", Select)

            if quote_select.value == Select.BLANK or not quote_select.value:
                self.query_one("#accuse-status-msg", Static).update("[bold red]Please select a suspect quote to accuse.[/bold red]")
                return
            if target_select.value == Select.BLANK or not target_select.value:
                self.query_one("#accuse-status-msg", Static).update("[bold red]Please select a target fact.[/bold red]")
                return

            self.query_one("#accuse-status-msg", Static).update("[bold yellow]Submitting to the Contradiction Judge...[/bold yellow]")
            
            # Dismiss and return payload to interrogation screen
            self.dismiss({
                "quote": str(quote_select.value),
                "target": str(target_select.value),
                "is_dossier": True
            })

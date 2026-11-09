import os
import time
import subprocess
from datetime import datetime
from typing import Optional, List, Dict, Any
from textual import work
from textual.app import App, ComposeResult
from textual.screen import Screen
from textual.widgets import (
    Header, Footer, Static, Button, Input, Label,
    RichLog, Select, TabbedContent, TabPane, DataTable
)
from textual.containers import Container, Horizontal, Vertical, VerticalScroll, Grid, Center
from rich.text import Text
from rich.panel import Panel
from rich.table import Table

from alibi.models.schema import Case
from alibi.llm.client import OllamaClient
from alibi.game.session import GameManager
from alibi.game.scoring import get_detective_rank
from alibi.agents.case_architect import CaseArchitectAgent
from alibi.ui.ascii_art import (
    TITLE_BANNER, ASCII_FACES, SUSPECT_QUOTES, render_tokens,
    DOTS_SQUARE_FRAMES, JUDGE_LOADING_FRAMES, HINT_LOADING_FRAMES,
    WIN_HEADER_BANNER, LOSE_HEADER_BANNER, MENU_PIXEL_ANIM_FRAMES
)
from alibi.ui.debug_panel import DebugPanelScreen
from alibi.ui.accuse_modal import AccuseModalScreen

# CSS definitions for CRT Green and Amber Phosphor themes with spacious layout
BASE_CSS = """
Screen {
    background: #061109;
    color: #20f065;
}

.theme-amber {
    background: #120902;
    color: #ffaa11;
}

/* Global Section Headers */
.section-header {
    width: 100%;
    text-align: center;
    content-align: center middle;
    text-style: bold;
    color: #2bf870;
    background: #092113;
    border: solid #20f065;
    padding: 0 1;
    margin-bottom: 1;
}

.theme-amber .section-header {
    color: #ffbb22;
    background: #251203;
    border: solid #ffaa11;
}

/* Title Screen Layout */
#title-container {
    align: center middle;
    padding: 1 2;
    width: 100%;
    height: 100%;
    overflow-y: auto;
}

#title-box {
    width: 86;
    height: auto;
    border: double #20f065;
    padding: 1 2;
    align: center middle;
}

.theme-amber #title-box {
    border: double #ffaa11;
}

#title-banner {
    content-align: center middle;
    text-align: center;
    color: #2bf870;
    width: 100%;
}

.theme-amber #title-banner {
    color: #ffb822;
}

#title-case-info {
    text-align: center;
    content-align: center middle;
    margin-top: 1;
    width: 100%;
}

#title-streak-info {
    text-align: center;
    content-align: center middle;
    margin-bottom: 0;
    width: 100%;
}

#title-pixel-anim {
    text-align: center;
    content-align: center middle;
    margin: 1 0;
    width: 100%;
    height: 4;
}

#title-menu {
    width: 54;
    height: auto;
    margin-top: 1;
    align: center middle;
}

#title-menu Button {
    width: 100%;
    margin-bottom: 0;
    content-align: center middle;
    text-align: center;
    border: solid #20f065;
    background: #0a2012;
    color: #20f065;
}

.theme-amber #title-menu Button {
    border: solid #ffaa11;
    background: #251203;
    color: #ffaa11;
}

#title-menu Button:hover {
    background: #184d28;
    color: #ffffff;
}

.theme-amber #title-menu Button:hover {
    background: #502706;
    color: #ffffff;
}

/* Archive Screen Layout */
#archive-container {
    padding: 1 2;
    width: 100%;
    height: 100%;
}

#archive-title {
    text-align: center;
    margin-bottom: 1;
}

#archive-stats-text {
    content-align: center middle;
    text-align: center;
    margin-bottom: 1;
}

#archive-table {
    height: 1fr;
    border: heavy #20f065;
    background: #020703;
}

.theme-amber #archive-table {
    border: heavy #ffaa11;
    background: #090401;
}

#archive-preview-box {
    height: 6;
    border: round #14401e;
    padding: 0 1;
    margin: 1 0;
}

.theme-amber #archive-preview-box {
    border: round #401f05;
}

#archive-buttons {
    height: 3;
    align: center middle;
}

#archive-buttons Button {
    margin: 0 1;
}

/* Briefing Screen */
#briefing-container {
    padding: 1 2;
    width: 100%;
    height: 100%;
    align: center middle;
}

#briefing-title {
    text-align: center;
    content-align: center middle;
    color: #38ff7e;
    margin-bottom: 1;
    text-style: bold;
}

.theme-amber #briefing-title {
    color: #ffbb33;
}

#briefing-scroll {
    height: 1fr;
    border: heavy #20f065;
    padding: 1 2;
}

.theme-amber #briefing-scroll {
    border: heavy #ffaa11;
}

#briefing-buttons {
    height: 3;
    margin-top: 1;
    align: center middle;
}

#briefing-buttons Button {
    margin: 0 1;
}

/* Interrogation Screen Layout (Spacious 50-col dossier side panel) */
#interrogation-grid {
    layout: grid;
    grid-size: 2;
    grid-columns: 50 1fr;
    height: 1fr;
    padding: 1;
}

#dossier-panel {
    border: heavy #20f065;
    padding: 1;
    height: 100%;
}

.theme-amber #dossier-panel {
    border: heavy #ffaa11;
}

#dossier-facts-scroll {
    height: 1fr;
    margin-bottom: 1;
}

#token-counter-text {
    content-align: center middle;
    text-align: center;
    margin: 1 0;
    text-style: bold;
}

#suspect-box {
    border: round #14401e;
    padding: 1;
    margin-bottom: 1;
    align: center middle;
}

.theme-amber #suspect-box {
    border: round #401f05;
}

#suspect-face-text {
    content-align: center middle;
    text-align: center;
}

#suspect-quote-text {
    content-align: center middle;
    text-align: center;
    color: #88ffaa;
    margin-top: 1;
}

.theme-amber #suspect-quote-text {
    color: #ffcc66;
}

#suspect-status-text {
    content-align: center middle;
    text-align: center;
    margin-top: 1;
    text-style: bold;
}

#interrogation-buttons {
    height: 3;
    align: center middle;
}

#interrogation-buttons Button {
    margin: 0 1;
    min-width: 13;
}

/* Chat & Transcript Panel */
#chat-panel {
    border: heavy #20f065;
    height: 100%;
    margin-left: 1;
    padding: 1;
}

.theme-amber #chat-panel {
    border: heavy #ffaa11;
}

#transcript-log {
    height: 1fr;
    background: #020703;
    border: solid #14401e;
    padding: 1;
}

.theme-amber #transcript-log {
    background: #090401;
    border: solid #401f05;
}

#thinking-indicator {
    height: 2;
    margin: 1 0 0 0;
    content-align: left middle;
    color: #ffdd44;
    text-style: bold;
}

.theme-amber #thinking-indicator {
    color: #ffbb22;
}

#input-bar {
    height: 3;
    margin-top: 1;
}

#question-input {
    border: solid #20f065;
    background: #081a0e;
    color: #20f065;
}

.theme-amber #question-input {
    border: solid #ffaa11;
    background: #1c0c02;
    color: #ffaa11;
}

/* Debug Modal */
#debug-modal-container {
    width: 90%;
    height: 90%;
    background: #030a05;
    border: double #00ff66;
    padding: 1 2;
    align: center middle;
}

.theme-amber #debug-modal-container {
    background: #0c0500;
    border: double #ffaa11;
}

#debug-title {
    text-align: center;
    color: #00ff66;
    margin-bottom: 1;
    text-style: bold;
}

.theme-amber #debug-title {
    color: #ffaa11;
}

/* Accuse Modal */
#accuse-modal-container {
    width: 86;
    height: 30;
    background: #07140a;
    border: heavy #ff3333;
    padding: 1 2;
}

#accuse-title {
    text-align: center;
    color: #ff4444;
    text-style: bold;
}

#accuse-buttons {
    height: 3;
    margin-top: 1;
    align: center middle;
}

#accuse-buttons Button {
    margin: 0 1;
}

/* Result Screen */
#result-container {
    padding: 2;
    align: center middle;
}

#result-box {
    width: 86;
    border: heavy #20f065;
    padding: 1 2;
}

.theme-amber #result-box {
    border: heavy #ffaa11;
}

#result-header {
    text-align: center;
    content-align: center middle;
    margin-bottom: 1;
    text-style: bold;
}

#result-share-grid {
    border: solid #14401e;
    padding: 1;
    margin: 1 0;
    text-align: center;
    content-align: center middle;
}

.theme-amber #result-share-grid {
    border: solid #401f05;
}

#result-countdown {
    text-align: center;
    content-align: center middle;
    margin: 1 0;
}

#result-buttons {
    height: 3;
    margin-top: 1;
    align: center middle;
}

#result-buttons Button {
    margin: 0 1;
}
"""

class TitleScreen(Screen):
    """Title Screen with ASCII art, live countdown, and navigation."""

    def compose(self) -> ComposeResult:
        with Container(id="title-container"):
            with Vertical(id="title-box"):
                yield Static(TITLE_BANNER, id="title-banner")
                yield Static("", id="title-case-info")
                yield Static("", id="title-streak-info")
                yield Static(MENU_PIXEL_ANIM_FRAMES[0], id="title-pixel-anim")
                with Center():
                    with Vertical(id="title-menu"):
                        yield Button("▶  INVESTIGATE TODAY'S CASE", id="btn-play-daily", variant="success")
                        yield Button("⚡  PRACTICE MODE (UNLIMITED)", id="btn-play-practice")
                        yield Button("📁  CASE ARCHIVES & HISTORY", id="btn-archive", variant="primary")
                        yield Button("📖  HOW TO PLAY", id="btn-how-to-play")
                        yield Button("⚙  SETTINGS & THEME", id="btn-settings")
                        yield Button("✖  QUIT", id="btn-quit", variant="error")

    def on_mount(self):
        self.pixel_anim_idx = 0
        self.update_case_and_streak()
        # Start title music
        self.app.game_manager.audio.play_music("title", loop=True)
        # Active live countdown timer
        self.countdown_timer = self.set_interval(1.0, self.update_countdown)
        # Active noir pixel art animation loop
        self.pixel_timer = self.set_interval(0.35, self.cycle_pixel_animation)

    def on_screen_resume(self):
        """Called when returning back to TitleScreen."""
        self.app.game_manager.audio.play_music("title", loop=True)
        self.update_case_and_streak()
        if hasattr(self, "pixel_timer") and self.pixel_timer:
            self.pixel_timer.resume()
        if hasattr(self, "countdown_timer") and self.countdown_timer:
            self.countdown_timer.resume()

    def on_screen_suspend(self):
        """Called when navigating away to another screen."""
        if hasattr(self, "pixel_timer") and self.pixel_timer:
            self.pixel_timer.pause()
        if hasattr(self, "countdown_timer") and self.countdown_timer:
            self.countdown_timer.pause()

    def cycle_pixel_animation(self) -> None:
        """Cycle through noir pixel art animation frames."""
        self.pixel_anim_idx = (self.pixel_anim_idx + 1) % len(MENU_PIXEL_ANIM_FRAMES)
        try:
            self.query_one("#title-pixel-anim", Static).update(MENU_PIXEL_ANIM_FRAMES[self.pixel_anim_idx])
        except Exception:
            pass

    def update_countdown(self):
        gm = self.app.game_manager
        today = datetime.now().strftime("%Y-%m-%d")
        if gm.is_daily_completed(today):
            res = gm.get_completed_result(today)
            outcome = "[bold green]SOLVED (WON)[/bold green]" if (res and res.get("won")) else "[bold red]FAILED (UNSOLVED)[/bold red]"
            info_text = f"[bold cyan]DATE:[/bold cyan] {today}  |  [bold yellow]STATUS:[/bold yellow] {outcome}  |  [bold magenta]Next in:[/bold magenta] [bold yellow]{gm.get_time_until_midnight()}[/bold yellow]"
            self.query_one("#title-case-info", Static).update(info_text)

    def update_case_and_streak(self):
        gm = self.app.game_manager
        today = datetime.now().strftime("%Y-%m-%d")
        stats = gm.progress_data

        info_text = f"[bold cyan]DATE:[/bold cyan] {today}  |  [bold yellow]STATUS:[/bold yellow] "
        if gm.is_daily_completed(today):
            res = gm.get_completed_result(today)
            outcome = "[bold green]SOLVED (WON)[/bold green]" if (res and res.get("won")) else "[bold red]FAILED (UNSOLVED)[/bold red]"
            info_text += f"{outcome}  |  [bold magenta]Next in:[/bold magenta] [bold yellow]{gm.get_time_until_midnight()}[/bold yellow]"
        else:
            info_text += "[bold green]READY FOR TRIAL[/bold green]"

        self.query_one("#title-case-info", Static).update(info_text)
        streak_text = f"[cyan]Total Cases:[/cyan] {stats.get('games_played', 0)}  [cyan]Solved:[/cyan] {stats.get('games_won', 0)}  [yellow]Streak:[/yellow] {stats.get('current_streak', 0)} (Best: {stats.get('max_streak', 0)})"
        self.query_one("#title-streak-info", Static).update(streak_text)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        btn_id = event.button.id
        if btn_id == "btn-play-daily":
            today = datetime.now().strftime("%Y-%m-%d")
            if self.app.game_manager.is_daily_completed(today):
                self.app.push_screen(ResultScreen(is_already_completed=True))
            else:
                self.app.start_game(is_practice=False)
        elif btn_id == "btn-play-practice":
            self.app.start_game(is_practice=True)
        elif btn_id == "btn-archive":
            self.app.push_screen(ArchiveScreen())
        elif btn_id == "btn-how-to-play":
            self.app.push_screen(HowToPlayScreen())
        elif btn_id == "btn-settings":
            self.app.push_screen(SettingsScreen())
        elif btn_id == "btn-quit":
            self.app.exit()


class ArchiveScreen(Screen):
    """Case Archives Browser to review and play historical daily micro-crimes."""

    BINDINGS = [
        ("escape", "app.pop_screen", "Back to Menu"),
        ("enter", "play_selected", "Play Case")
    ]

    def __init__(self):
        super().__init__()
        self.archive_data = []

    def compose(self) -> ComposeResult:
        with Container(id="archive-container"):
            yield Static("THE ALIBI: CASE ARCHIVES & HISTORY", classes="section-header", id="archive-title")
            yield Static("", id="archive-stats-text")
            yield DataTable(id="archive-table", cursor_type="row")
            with Vertical(id="archive-preview-box"):
                yield Static("CASE PREVIEW", classes="section-header")
                yield Static("Select a case above to preview details.", id="archive-preview-text")
            with Horizontal(id="archive-buttons"):
                yield Button("▶  INVESTIGATE SELECTED CASE (Enter)", id="btn-play-selected", variant="success")
                yield Button("BACK TO MAIN MENU (Esc)", id="btn-back-archive", variant="default")

    def on_mount(self):
        table = self.query_one("#archive-table", DataTable)
        table.add_columns("Date", "Status", "Case Title", "Suspect", "Setting")

        architect = self.app.case_architect
        progress = self.app.game_manager.progress_data
        self.archive_data = architect.registry.get_archive_list(progress)

        solved_count = sum(1 for c in self.archive_data if c["won"])
        self.query_one("#archive-stats-text", Static).update(
            f"[bold cyan]Archived Cases:[/bold cyan] {len(self.archive_data)}  |  "
            f"[bold green]Solved:[/bold green] {solved_count}  |  "
            f"[bold yellow]Available to Play:[/bold yellow] {len(self.archive_data) - solved_count}"
        )

        for item in self.archive_data:
            st = item["status"]
            if st == "SOLVED":
                st_render = "[bold green]★ SOLVED[/bold green]"
            elif st == "FAILED":
                st_render = "[bold red]✖ FAILED[/bold red]"
            elif st == "TODAY":
                st_render = "[bold yellow]▶ TODAY[/bold yellow]"
            else:
                st_render = "[cyan]○ READY[/cyan]"

            table.add_row(
                item["date"],
                st_render,
                item["title"],
                item["suspect_name"],
                item["setting"],
                key=item["date"]
            )

        if self.archive_data:
            self._update_preview(0)
            table.focus()

    def on_data_table_row_highlighted(self, event: DataTable.RowHighlighted):
        if event.cursor_row < len(self.archive_data):
            self._update_preview(event.cursor_row)

    def _update_preview(self, row_idx: int):
        if 0 <= row_idx < len(self.archive_data):
            item = self.archive_data[row_idx]
            preview = (
                f"[bold yellow]{item['title']}[/bold yellow]  |  [cyan]{item['date']}[/cyan]\n"
                f"[bold]Suspect:[/bold] {item['suspect_name']}  |  [bold]Location:[/bold] {item['setting']}\n"
                f"[dim]Status: {item['status']}[/dim]"
            )
            self.query_one("#archive-preview-text", Static).update(preview)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-back-archive":
            self.app.pop_screen()
        elif event.button.id == "btn-play-selected":
            self.action_play_selected()

    def on_data_table_row_selected(self, event: DataTable.RowSelected):
        self.action_play_selected()

    def action_play_selected(self):
        table = self.query_one("#archive-table", DataTable)
        row_idx = table.cursor_row
        if 0 <= row_idx < len(self.archive_data):
            target_date = self.archive_data[row_idx]["date"]
            today = datetime.now().strftime("%Y-%m-%d")

            # If this case was already completed, view its saved conclusion and truth timeline!
            if self.app.game_manager.is_daily_completed(target_date):
                self.app.push_screen(ResultScreen(is_already_completed=True, date_str=target_date))
                return

            # Otherwise, start investigation (is_practice=True for historical cases to avoid corrupting today)
            is_practice = (target_date != today)
            case = self.app.case_architect.get_daily_case(date_str=target_date, practice=is_practice)
            self.app.game_manager.init_session(case, is_practice=is_practice)
            self.app.game_manager.audio.play_music("interrogation", loop=True)
            self.app.push_screen(BriefingScreen())


class HowToPlayScreen(Screen):
    """How to play rules and mechanics screen."""

    BINDINGS = [("escape", "app.pop_screen", "Back")]

    def compose(self) -> ComposeResult:
        with Container(id="briefing-container"):
            yield Static("╔════════════════════════════════════════════════════════════════════════╗\n║                     HOW TO PLAY: THE ALIBI                             ║\n╚════════════════════════════════════════════════════════════════════════╝", id="briefing-title")
            with VerticalScroll(id="briefing-scroll"):
                instructions = (
                    "[bold yellow]THE PREMISE:[/bold yellow]\n"
                    "Each day an absurd micro-crime occurs. You are the detective. A guilty, eccentric suspect is in the interrogation room.\n\n"
                    "[bold yellow]1. THE DOSSIER:[/bold yellow]\n"
                    "You are given 3 100% VERIFIED FORENSIC FACTS. These are immutable physical truths.\n\n"
                    "[bold yellow]2. QUESTION TOKENS (5 TOTAL):[/bold yellow]\n"
                    "You have 5 tokens. Every question costs 1 token. Ask strategic questions about times, objects, clothing, or places.\n\n"
                    "[bold yellow]3. THE WEAK POINTS:[/bold yellow]\n"
                    "The suspect has a planned cover story with hidden weak points. When pressed, their lies will directly conflict with a dossier fact or an earlier statement.\n\n"
                    "[bold yellow]4. ACCUSE (KEY A or /accuse):[/bold yellow]\n"
                    "Spot a contradiction? Press [bold cyan]A[/bold cyan]. Select the suspect's quote and pick what it contradicts.\n"
                    "The Contradiction Judge will rule. If VALID, you win! If INVALID, you lose 1 token penalty!\n\n"
                    "[bold yellow]5. KEYBOARD SHORTCUTS:[/bold yellow]\n"
                    "• [bold cyan]Enter[/bold cyan] : Send question\n"
                    "• [bold cyan]A[/bold cyan]     : Accuse\n"
                    "• [bold cyan]H[/bold cyan]     : Hint (costs 1 token, once per case)\n"
                    "• [bold cyan]F2[/bold cyan]    : Live Architecture Debug Panel (Agent traces, RAG, Tool Calls)\n"
                    "• [bold cyan]M[/bold cyan]     : Mute audio\n"
                    "• [bold cyan]Esc[/bold cyan]   : Back / Cancel"
                )
                yield Static(instructions)
                yield Button("BACK TO TITLE (Esc)", id="btn-back-rules", variant="primary")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-back-rules":
            self.app.pop_screen()


class SettingsScreen(Screen):
    """Settings screen for Volume, Theme, and Mute."""

    BINDINGS = [("escape", "app.pop_screen", "Back")]

    def compose(self) -> ComposeResult:
        vol_options = [("100%", "1.0"), ("75%", "0.75"), ("50%", "0.5"), ("25%", "0.25"), ("Off (0%)", "0.0")]
        valid_vals = ["1.0", "0.75", "0.5", "0.25", "0.0"]
        m_vol = min(valid_vals, key=lambda x: abs(float(x) - float(self.app.game_manager.audio.music_volume)))
        s_vol = min(valid_vals, key=lambda x: abs(float(x) - float(self.app.game_manager.audio.sfx_volume)))
        theme_val = self.app.crt_theme if self.app.crt_theme in ["green", "amber"] else "green"

        with Container(id="briefing-container"):
            yield Static("╔════════════════════════════════════════════════════════════════════════╗\n║                         SETTINGS & CRT DISPLAY                         ║\n╚════════════════════════════════════════════════════════════════════════╝", id="briefing-title")
            with VerticalScroll(id="briefing-scroll"):
                yield Label("[bold cyan]CRT Phosphor Theme:[/bold cyan]")
                yield Select([("CRT Classic Green", "green"), ("CRT Amber Phosphor", "amber")], id="select-theme", value=theme_val)

                yield Label("\n[bold cyan]Music Volume:[/bold cyan]")
                yield Select(vol_options, id="select-music-vol", value=m_vol)

                yield Label("\n[bold cyan]SFX Volume:[/bold cyan]")
                yield Select(vol_options, id="select-sfx-vol", value=s_vol)

                yield Static("", id="settings-status")
                yield Button("APPLY & BACK (Esc)", id="btn-back-settings", variant="primary")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-back-settings":
            theme_val = self.query_one("#select-theme", Select).value
            m_vol = float(self.query_one("#select-music-vol", Select).value or 0.6)
            s_vol = float(self.query_one("#select-sfx-vol", Select).value or 0.7)
            self.app.set_theme(theme_val)
            self.app.game_manager.audio.set_music_volume(m_vol)
            self.app.game_manager.audio.set_sfx_volume(s_vol)
            self.app.pop_screen()


class BriefingScreen(Screen):
    """Case Briefing Screen introducing the crime, suspect, and dossier."""

    BINDINGS = [
        ("enter", "start_interrogation", "Proceed"),
        ("escape", "back_to_title", "Back to Menu")
    ]

    def compose(self) -> ComposeResult:
        with Container(id="briefing-container"):
            yield Static("CASE BRIEFING DOSSIER", classes="section-header", id="briefing-title")
            with VerticalScroll(id="briefing-scroll"):
                yield Static("", id="briefing-content")
            with Horizontal(id="briefing-buttons"):
                yield Button("BEGIN INTERROGATION (Enter)", id="btn-start-interrogation", variant="success")
                yield Button("BACK TO MAIN MENU (Esc)", id="btn-back-menu", variant="default")

    def on_mount(self):
        case = self.app.game_manager.session.case
        briefing_text = (
            f"[bold yellow]CASE #{case.id.upper()}[/bold yellow]  |  [cyan]{case.date}[/cyan]\n"
            f"[bold underline]TITLE:[/bold underline] {case.title}\n"
            f"[bold underline]LOCATION:[/bold underline] {case.setting}\n\n"
            f"[bold red]INCIDENT REPORT:[/bold red]\n{case.crime_description}\n\n"
            f"[bold green]SUSPECT IN CUSTODY:[/bold green]\n"
            f"  • [bold]Name:[/bold] {case.suspect.name}\n"
            f"  • [bold]Occupation:[/bold] {case.suspect.occupation}\n"
            f"  • [bold]Speech Quirk:[/bold] {case.suspect.quirk}\n\n"
            f"[bold cyan]VERIFIED FORENSIC DOSSIER (3 IMMUTABLE FACTS):[/bold cyan]\n"
        )
        for f in case.dossier:
            briefing_text += f"\n  [bold cyan]▶ [{f.id.upper()}]:[/bold cyan] {f.text}"

        self.query_one("#briefing-content", Static).update(briefing_text)

    def action_start_interrogation(self):
        self.app.push_screen(InterrogationScreen())

    def action_back_to_title(self):
        self.app.return_to_title()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-start-interrogation":
            self.action_start_interrogation()
        elif event.button.id == "btn-back-menu":
            self.action_back_to_title()


class InterrogationScreen(Screen):
    """Main Interrogation Screen: spacious dossier, live thinking animation, transcript, buttons."""

    BINDINGS = [
        ("a", "accuse", "Accuse"),
        ("h", "hint", "Hint"),
        ("f2", "debug", "Debug Panel"),
        ("m", "mute", "Mute Audio"),
        ("escape", "back_to_title", "Back to Menu")
    ]

    def __init__(self):
        super().__init__()
        self.anim_timer = None
        self.anim_frame_idx = 0
        self.anim_frames = DOTS_SQUARE_FRAMES

    def compose(self) -> ComposeResult:
        with Container(id="interrogation-grid"):
            # Left pane: Spacious Dossier & Suspect Status
            with Vertical(id="dossier-panel"):
                yield Static("CASE DOSSIER: 3 IMMUTABLE FACTS", classes="section-header")
                with VerticalScroll(id="dossier-facts-scroll"):
                    yield Static("", id="dossier-facts-text")
                yield Static("", id="token-counter-text")
                with Vertical(id="suspect-box"):
                    yield Static("SUSPECT IN CUSTODY", classes="section-header")
                    yield Static("", id="suspect-face-text")
                    yield Static("", id="suspect-quote-text")
                    yield Static("", id="suspect-status-text")
                with Horizontal(id="interrogation-buttons"):
                    yield Button("ACCUSE (A)", id="btn-accuse", variant="error")
                    yield Button("HINT (H)", id="btn-hint", variant="warning")
                    yield Button("MENU (Esc)", id="btn-back-menu", variant="default")

            # Right pane: Transcript & Input Box
            with Vertical(id="chat-panel"):
                yield Static("INTERROGATION ROOM TRANSCRIPT", classes="section-header")
                yield RichLog(id="transcript-log", wrap=True, highlight=True, markup=True)
                yield Static("", id="thinking-indicator")
                with Horizontal(id="input-bar"):
                    yield Input(placeholder="Ask suspect a question (costs 1 token)...", id="question-input")
                    yield Button("SEND", id="btn-send-question", variant="primary")

    def on_mount(self):
        self.app.game_manager.audio.play_music("interrogation", loop=True)
        session = self.app.game_manager.session
        log = self.query_one("#transcript-log", RichLog)

        if session and session.transcript:
            # Resuming an in-progress investigation!
            log.write(f"[bold yellow]▶ RESUMING SAVED INVESTIGATION ({len(session.transcript)} previous question{'s' if len(session.transcript) > 1 else ''} recorded)[/bold yellow]")
            for stmt in session.transcript:
                log.write(f"\n[bold #00e5ff]DETECTIVE:[/bold #00e5ff] \"{stmt.question}\"\n")
                log.write(f"\n[bold #ff8c00]{session.case.suspect.name}[/bold #ff8c00] [italic dim]({stmt.emotion.upper()}):[/italic dim]\n  \"{stmt.answer}\"\n")
            last_emotion = session.transcript[-1].emotion
            self.update_dossier_panel(last_emotion)
        else:
            # Fresh interrogation greeting
            self.update_dossier_panel()
            log.write(f"[bold cyan]Detective enters the room.[/bold cyan] Sitting across the metal table is [bold #ff8c00]{session.case.suspect.name}[/bold #ff8c00] ({session.case.suspect.occupation}).")
            log.write(f"[dim]Behavioral speech quirk: {session.case.suspect.quirk}[/dim]\n")

    def update_dossier_panel(self, emotion: str = "calm"):
        session = self.app.game_manager.session
        dossier_lines = []
        for f in session.case.dossier:
            dossier_lines.append(f"[bold cyan]▶ [{f.id.upper()}][/bold cyan]\n  {f.text}")
        self.query_one("#dossier-facts-text", Static).update("\n\n".join(dossier_lines))

        # Token counter with clean dot glyphs
        self.query_one("#token-counter-text", Static).update(render_tokens(session.remaining_tokens))

        # Suspect face (clean ascii art without overlapping side text)
        face_art = ASCII_FACES.get(emotion, ASCII_FACES["calm"])
        self.query_one("#suspect-face-text", Static).update(face_art)

        # Suspect quote displayed neatly underneath the face art
        quote_text = SUSPECT_QUOTES.get(emotion, SUSPECT_QUOTES["calm"])
        self.query_one("#suspect-quote-text", Static).update(f"[italic]{quote_text}[/italic]")

        # Color-coded emotion badge
        emotion_colors = {
            "calm": "green",
            "smug": "yellow",
            "nervous": "magenta",
            "defensive": "dark_orange",
            "panicked": "red"
        }
        color = emotion_colors.get(emotion, "green")
        self.query_one("#suspect-status-text", Static).update(f"[bold #ff8c00]{session.case.suspect.name}[/bold #ff8c00]  |  Demeanor: [bold {color}]{emotion.upper()}[/bold {color}]")

    def on_input_submitted(self, event: Input.Submitted) -> None:
        self.process_question()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-send-question":
            self.process_question()
        elif event.button.id == "btn-accuse":
            self.action_accuse()
        elif event.button.id == "btn-hint":
            self.action_hint()
        elif event.button.id == "btn-back-menu":
            self.action_back_to_title()

    def action_back_to_title(self):
        self.app.return_to_title()

    # -------------------------------------------------------------
    # Question Processing with Live Dots-in-a-Square Animation
    # -------------------------------------------------------------
    def process_question(self):
        input_widget = self.query_one("#question-input", Input)
        q_text = input_widget.value.strip()
        if not q_text:
            return

        if q_text.lower() == "/accuse":
            input_widget.value = ""
            self.action_accuse()
            return

        input_widget.value = ""
        input_widget.disabled = True
        self.query_one("#btn-send-question", Button).disabled = True

        log = self.query_one("#transcript-log", RichLog)
        log.write(f"\n[bold #00e5ff]DETECTIVE:[/bold #00e5ff] \"{q_text}\"\n")

        # Start live retro dots-in-a-square animation
        self.anim_frame_idx = 0
        self.anim_frames = DOTS_SQUARE_FRAMES
        self._update_loading_frame()
        self.anim_timer = self.set_interval(0.18, self._cycle_loading_animation)

        # Asynchronously interrogate suspect in background worker thread
        self._async_ask_question(q_text)

    def _cycle_loading_animation(self):
        self.anim_frame_idx = (self.anim_frame_idx + 1) % len(self.anim_frames)
        self._update_loading_frame()

    def _update_loading_frame(self):
        indicator = self.query_one("#thinking-indicator", Static)
        indicator.update(self.anim_frames[self.anim_frame_idx])

    @work(thread=True)
    def _async_ask_question(self, q_text: str):
        success, err, stmt = self.app.game_manager.ask_question(q_text)
        self.app.call_from_thread(self._on_question_finished, success, err, stmt)

    def _on_question_finished(self, success: bool, err: str, stmt):
        if self.anim_timer:
            self.anim_timer.stop()
            self.anim_timer = None
        self.query_one("#thinking-indicator", Static).update("")

        input_widget = self.query_one("#question-input", Input)
        input_widget.disabled = False
        self.query_one("#btn-send-question", Button).disabled = False
        input_widget.focus()

        log = self.query_one("#transcript-log", RichLog)
        if not success:
            log.write(f"[bold red]ERROR:[/bold red] {err}")
            return

        self.app.game_manager.audio.play_sfx("key_click")
        session = self.app.game_manager.session
        log.write(f"\n[bold #ff8c00]{session.case.suspect.name}[/bold #ff8c00] [italic dim]({stmt.emotion.upper()}):[/italic dim]\n  \"{stmt.answer}\"\n")
        self.update_dossier_panel(stmt.emotion)

        if session.game_over:
            self.app.push_screen(ResultScreen(is_already_completed=False))

    # -------------------------------------------------------------
    # Accusation Processing with Live Judge Animation
    # -------------------------------------------------------------
    def action_accuse(self):
        def accuse_callback(result_payload):
            if not result_payload:
                return
            quote = result_payload["quote"]
            target = result_payload["target"]
            is_dossier = result_payload["is_dossier"]

            log = self.query_one("#transcript-log", RichLog)
            log.write(f"\n[bold red]╔═══════════════════════════════════════════════╗[/bold red]")
            log.write(f"[bold red]║             FORMAL ACCUSATION LEVELED         ║[/bold red]")
            log.write(f"[bold red]╚═══════════════════════════════════════════════╝[/bold red]")
            log.write(f"[yellow]Quote:[/yellow] \"{quote}\"")
            log.write(f"[yellow]Target:[/yellow] \"{target}\"\n")

            # Start judge analysis animation
            self.anim_frame_idx = 0
            self.anim_frames = JUDGE_LOADING_FRAMES
            self._update_loading_frame()
            self.anim_timer = self.set_interval(0.18, self._cycle_loading_animation)

            self._async_judge(quote, target, is_dossier)

        self.app.push_screen(AccuseModalScreen(self.app.game_manager), accuse_callback)

    @work(thread=True)
    def _async_judge(self, quote: str, target: str, is_dossier: bool):
        res = self.app.game_manager.accuse(quote, target, is_dossier_fact=is_dossier)
        self.app.call_from_thread(self._on_judge_finished, res)

    def _on_judge_finished(self, res):
        if self.anim_timer:
            self.anim_timer.stop()
            self.anim_timer = None
        self.query_one("#thinking-indicator", Static).update("")

        log = self.query_one("#transcript-log", RichLog)
        if res.valid:
            log.write(f"[bold green]JUDGE VERDICT: VALID CONTRADICTION![/bold green]")
            log.write(f"[italic]{res.explanation}[/italic]")
            if res.breakdown_confession:
                s_name = self.app.game_manager.session.case.suspect.name
                log.write(f"\n[bold #ff8c00]{s_name} CONFESSION:[/bold #ff8c00]\n  \"{res.breakdown_confession}\"\n")
            self.app.push_screen(ResultScreen(is_already_completed=False))
        else:
            log.write(f"[bold red]JUDGE VERDICT: INVALID CONTRADICTION.[/bold red]")
            log.write(f"[italic]{res.explanation}[/italic]")
            log.write("[dim red]Penalty applied: -1 Question Token.[/dim red]\n")
            self.update_dossier_panel(emotion="smug")
            if self.app.game_manager.session.game_over:
                self.app.push_screen(ResultScreen(is_already_completed=False))

    # -------------------------------------------------------------
    # Hint Processing with Live Narrator Animation
    # -------------------------------------------------------------
    def action_hint(self):
        session = self.app.game_manager.session
        if not session:
            return
        if session.hint_used:
            log = self.query_one("#transcript-log", RichLog)
            log.write("[bold red]HINT:[/bold red] You have already used your 1 hint for this case.\n")
            return
        if session.remaining_tokens <= 1:
            log = self.query_one("#transcript-log", RichLog)
            log.write("[bold red]HINT:[/bold red] Not enough tokens to afford a hint (costs 1 token).\n")
            return

        self.anim_frame_idx = 0
        self.anim_frames = HINT_LOADING_FRAMES
        self._update_loading_frame()
        self.anim_timer = self.set_interval(0.18, self._cycle_loading_animation)

        self._async_hint()

    @work(thread=True)
    def _async_hint(self):
        success, hint_or_err = self.app.game_manager.use_hint()
        self.app.call_from_thread(self._on_hint_finished, success, hint_or_err)

    def _on_hint_finished(self, success: bool, hint_or_err: str):
        if self.anim_timer:
            self.anim_timer.stop()
            self.anim_timer = None
        self.query_one("#thinking-indicator", Static).update("")

        log = self.query_one("#transcript-log", RichLog)
        if success:
            log.write(f"\n[bold magenta]NOIR NARRATOR HINT (-1 Token):[/bold magenta] [italic]\"{hint_or_err}\"[/italic]\n")
            self.update_dossier_panel()
        else:
            log.write(f"[bold red]HINT UNAVAILABLE:[/bold red] {hint_or_err}\n")

    def action_debug(self):
        self.app.push_screen(DebugPanelScreen(self.app.game_manager))

    def action_mute(self):
        is_muted = self.app.game_manager.audio.toggle_mute()
        log = self.query_one("#transcript-log", RichLog)
        log.write(f"[cyan]Audio {'MUTED' if is_muted else 'UNMUTED'}.[/cyan]")


class ResultScreen(Screen):
    """Case Conclusion Screen with win/lose announcement, Truth Timeline, and clean Wordle share grid."""

    BINDINGS = [
        ("escape", "to_title", "Title Screen")
    ]

    def __init__(self, is_already_completed: bool = False, date_str: Optional[str] = None):
        super().__init__()
        self.is_already_completed = is_already_completed
        self.date_str = date_str
        self.countdown_timer = None

    def compose(self) -> ComposeResult:
        with Container(id="result-container"):
            with Container(id="result-box"):
                yield Static("", id="result-header")
                with VerticalScroll():
                    yield Static("", id="result-story-text")
                    yield Static("", id="result-share-grid")
                    yield Static("", id="result-countdown")
                with Horizontal(id="result-buttons"):
                    yield Button("COPY RESULT", id="btn-copy-share", variant="primary")
                    yield Button("PLAY PRACTICE CASE", id="btn-practice-again", variant="success")
                    yield Button("RETURN TO TITLE (Esc)", id="btn-result-title", variant="default")

    def on_mount(self):
        gm = self.app.game_manager
        today = datetime.now().strftime("%Y-%m-%d")
        target_date = self.date_str or today

        if self.is_already_completed:
            # Strictly load the verified result for this specific date
            res = gm.get_completed_result(target_date)
            won = res.get("won", False) if res else False
            header = WIN_HEADER_BANNER if won else LOSE_HEADER_BANNER
            grid = res.get("share_grid", "") if res else ""
            try:
                completed_case = self.app.case_architect.get_daily_case(date_str=target_date, practice=False)
                story_events = "\n".join([f"• [{e.time}] {e.event}" for e in completed_case.truth_timeline])
                story = f"[bold cyan]THE FORENSIC TRUTH REVEALED ({target_date}):[/bold cyan]\n{story_events}\n\n[dim]Concluded at {res.get('completed_at', 'today') if res else 'today'}[/dim]"
            except Exception:
                story = f"Case {target_date} concluded."
        else:
            session = gm.session
            won = session.won if session else False
            header = WIN_HEADER_BANNER if won else LOSE_HEADER_BANNER
            if session:
                story_events = "\n".join([f"• [{e.time}] {e.event}" for e in session.case.truth_timeline])
                story = f"[bold cyan]THE FORENSIC TRUTH REVEALED:[/bold cyan]\n{story_events}\n\n"
                if won and session.accusation_result:
                    story += f"[bold yellow]THE DECISIVE CATCH:[/bold yellow]\n\"{session.accusation_result.highlighted_quote}\"\nContradicted: \"{session.accusation_result.target_text}\"\n"
                    if session.accusation_result.breakdown_confession:
                        s_name = session.case.suspect.name
                        story += f"\n[bold #ff8c00]{s_name} CONFESSION:[/bold #ff8c00]\n  \"{session.accusation_result.breakdown_confession}\"\n"
                grid = gm.generate_share_grid()
            else:
                story = "Case concluded."
                grid = ""

        self.query_one("#result-header", Static).update(header)
        self.query_one("#result-story-text", Static).update(story)
        # Clean formatting without any backticks
        self.query_one("#result-share-grid", Static).update(f"[bold cyan]═══ INVESTIGATION SUMMARY ═══[/bold cyan]\n{grid}")
        self.query_one("#result-countdown", Static).update(f"[bold magenta]Next Daily Micro-Crime Available In:[/bold magenta] [bold yellow]{gm.get_time_until_midnight()}[/bold yellow]")

        # Active live countdown timer
        self.countdown_timer = self.set_interval(1.0, self.update_countdown)

    def update_countdown(self):
        gm = self.app.game_manager
        self.query_one("#result-countdown", Static).update(
            f"[bold magenta]Next Daily Micro-Crime Available In:[/bold magenta] [bold yellow]{gm.get_time_until_midnight()}[/bold yellow]"
        )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-copy-share":
            gm = self.app.game_manager
            grid = gm.generate_share_grid()
            try:
                process = subprocess.Popen('pbcopy', env={'LANG': 'en_US.UTF-8'}, stdin=subprocess.PIPE)
                process.communicate(grid.encode('utf-8'))
                self.query_one("#result-countdown", Static).update("[bold green]Copied to clipboard![/bold green]")
            except Exception:
                self.query_one("#result-countdown", Static).update("[dim yellow]Result ready to copy above.[/dim yellow]")
        elif event.button.id == "btn-practice-again":
            self.app.start_game(is_practice=True)
        elif event.button.id == "btn-result-title":
            self.action_to_title()

    def action_to_title(self):
        self.app.return_to_title()


class TheAlibiApp(App):
    """Main Textual Application for THE ALIBI."""

    CSS = BASE_CSS
    TITLE = "THE ALIBI - Daily Detective Interrogation Game"

    def __init__(self, client: OllamaClient, saves_path: str = "saves/progress.json"):
        super().__init__()
        self.client = client
        self.game_manager = GameManager(client, saves_path=saves_path)
        self.case_architect = CaseArchitectAgent(client)
        self.crt_theme = "green"

    def on_mount(self):
        self.push_screen(TitleScreen())

    def set_theme(self, theme_name: str):
        self.crt_theme = theme_name
        if theme_name == "amber":
            self.screen.add_class("theme-amber")
        else:
            self.screen.remove_class("theme-amber")

    def return_to_title(self):
        """Pops screens back until TitleScreen is the active screen and cleans transient session."""
        while len(self.screen_stack) > 1 and not isinstance(self.screen, TitleScreen):
            self.pop_screen()
        if not isinstance(self.screen, TitleScreen):
            self.push_screen(TitleScreen())
        self.game_manager.audio.play_music("title", loop=True)
        # Clear transient practice or archive session so it never contaminates today's case
        if self.game_manager.session and (self.game_manager.session.game_over or getattr(self.game_manager, "is_practice", False)):
            self.game_manager.session = None

    def start_game(self, is_practice: bool = False):
        """Fetch/generate case, initialize session, start background music, and show briefing."""
        today = datetime.now().strftime("%Y-%m-%d")
        if not is_practice and self.game_manager.is_daily_completed(today):
            self.push_screen(ResultScreen(is_already_completed=True, date_str=today))
            return
        case = self.case_architect.get_daily_case(date_str=today, practice=is_practice)
        self.game_manager.init_session(case, is_practice=is_practice)
        self.game_manager.audio.play_music("interrogation", loop=True)
        self.push_screen(BriefingScreen())

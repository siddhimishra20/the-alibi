import os
import sys
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.prompt import Prompt

from alibi.models.schema import Case
from alibi.game.session import GameManager
from alibi.ui.ascii_art import TITLE_BANNER, ASCII_FACES, render_tokens

console = Console()

def run_cli_game(game_manager: GameManager, case: Case, is_practice: bool = False):
    """Run an interactive CLI session using Rich (lightweight alternative to full TUI)."""
    game_manager.init_session(case, is_practice=is_practice)
    session = game_manager.session

    console.print(TITLE_BANNER, style="bold green")
    console.print(Panel(
        f"[bold yellow]CASE:[/bold yellow] {case.title}\n"
        f"[bold yellow]CRIME:[/bold yellow] {case.crime_description}\n"
        f"[bold yellow]SETTING:[/bold yellow] {case.setting}\n"
        f"[bold yellow]SUSPECT:[/bold yellow] {case.suspect.name} ({case.suspect.occupation})\n"
        f"[bold yellow]QUIRK:[/bold yellow] {case.suspect.quirk}",
        title="[bold cyan]CASE BRIEFING[/bold cyan]",
        border_style="cyan"
    ))

    # Print Dossier Facts
    dossier_table = Table(title="VERIFIED FORENSIC DOSSIER", border_style="green")
    dossier_table.add_column("Fact ID", style="bold cyan", width=10)
    dossier_table.add_column("Immutable Forensic Truth", style="white")
    for f in case.dossier:
        dossier_table.add_row(f.id.upper(), f.text)
    console.print(dossier_table)
    console.print()

    console.print(f"[bold yellow]Suspect enters the room:[/bold yellow] {case.suspect.name}")
    console.print("[dim]Type your question, or 'A' to accuse, 'H' for hint, 'Q' to quit.[/dim]\n")

    while not session.game_over:
        # Display token status
        token_str = "● " * session.remaining_tokens + "○ " * (5 - session.remaining_tokens)
        console.print(f"\n[bold cyan]Tokens:[/bold cyan] {token_str} [dim]({session.remaining_tokens}/5)[/dim]")

        action = Prompt.ask("[bold green]Detective[/bold green] (question, 'A' to accuse, 'H' hint, 'Q' quit)")
        action = action.strip()
        if not action:
            continue

        if action.lower() in ["q", "quit", "exit"]:
            console.print("[yellow]Exiting interrogation.[/yellow]")
            break

        if action.lower() in ["a", "accuse", "/accuse"]:
            _handle_cli_accusation(game_manager, console)
            if session.game_over:
                break
            continue

        if action.lower() in ["h", "hint", "/hint"]:
            success, hint_or_err = game_manager.use_hint()
            if success:
                console.print(f"\n[bold magenta]Noir Narrator:[/bold magenta] [italic]\"{hint_or_err}\"[/italic]\n")
            else:
                console.print(f"[red]{hint_or_err}[/red]")
            continue

        # Standard Question
        console.print("[dim yellow]Suspect is deliberating and weighing their words...[/dim yellow]")
        success, err, stmt = game_manager.ask_question(action)
        if not success:
            console.print(f"[bold red]Error:[/bold red] {err}")
            continue

        face = ASCII_FACES.get(stmt.emotion, ASCII_FACES["calm"])
        console.print(Panel(
            f"[bold yellow]{case.suspect.name}[/bold yellow] ({stmt.emotion.upper()}):\n"
            f"\"{stmt.answer}\"\n\n"
            f"[dim]{face.strip()}[/dim]",
            title=f"[bold green]Suspect Response (Turn #{stmt.turn_number})[/bold green]",
            border_style="green"
        ))

    # Game Over Summary
    console.print("\n" + "=" * 60)
    if session.won:
        console.print("[bold green]★★★★★ CASE SOLVED: SUSPECT CONVICTED! ★★★★★[/bold green]")
        if session.accusation_result and session.accusation_result.breakdown_confession:
            console.print(f"\n[bold yellow]CONFESSION:[/bold yellow] {session.accusation_result.breakdown_confession}")
    else:
        console.print("[bold red]✖✖✖✖✖ CASE COLD: SUSPECT WALKED FREE! ✖✖✖✖✖[/bold red]")

    grid = game_manager.generate_share_grid()
    console.print(f"\n[bold yellow]Wordle-Style Investigation Grid:[/bold yellow]\n{grid}")
    console.print("=" * 60 + "\n")

def _handle_cli_accusation(game_manager: GameManager, console: Console):
    session = game_manager.session
    if not session.transcript:
        console.print("[red]Cannot accuse before the suspect has spoken! Ask at least one question first.[/red]")
        return

    console.print("\n[bold red]── FORMAL ACCUSATION ──[/bold red]")
    console.print("[yellow]Select the suspect quote you want to contradict:[/yellow]")
    for idx, stmt in enumerate(session.transcript, 1):
        console.print(f"  [{idx}] Turn #{stmt.turn_number}: \"{stmt.answer}\"")

    choice_q = Prompt.ask("Quote #", default="1")
    try:
        q_idx = int(choice_q) - 1
        chosen_quote = session.transcript[q_idx].answer
    except (ValueError, IndexError):
        console.print("[red]Invalid quote selection.[/red]")
        return

    console.print("\n[yellow]Select contradictory dossier fact (or type 'S' to contradict an earlier statement):[/yellow]")
    facts = session.case.dossier
    for idx, f in enumerate(facts, 1):
        console.print(f"  [{idx}] [{f.id.upper()}] {f.text}")

    choice_f = Prompt.ask("Fact #", default="1")
    try:
        f_idx = int(choice_f) - 1
        chosen_target = facts[f_idx].text
    except (ValueError, IndexError):
        console.print("[red]Invalid fact selection.[/red]")
        return

    console.print("\n[dim yellow]Contradiction Judge is analyzing claims...[/dim yellow]")
    res = game_manager.accuse(chosen_quote, chosen_target, is_dossier_fact=True)

    if res.valid:
        console.print(f"[bold green]JUDGE RULING: VALID CONTRADICTION![/bold green]")
        console.print(f"[italic]{res.explanation}[/italic]")
    else:
        console.print(f"[bold red]JUDGE RULING: INVALID CONTRADICTION.[/bold red]")
        console.print(f"[italic]{res.explanation}[/italic]")
        console.print("[red]Penalty: -1 Question Token deducted![/red]")


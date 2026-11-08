"""ASCII art, iconography, and animation frames for THE ALIBI."""

import math

TITLE_BANNER = r"""
 ████████╗██╗  ██╗███████╗     █████╗ ██╗     ██╗██████╗ ██╗
 ╚══██╔══╝██║  ██║██╔════╝    ██╔══██╗██║     ██║██╔══██╗██║
    ██║   ███████║█████╗      ███████║██║     ██║██████╔╝██║
    ██║   ██╔══██║██╔══╝      ██╔══██║██║     ██║██╔══██╗██║
    ██║   ██║  ██║███████╗    ██║  ██║███████╗██║██████╔╝██║
    ╚═╝   ╚═╝  ╚═╝╚══════╝    ╚═╝  ╚═╝╚══════╝╚═╝╚═════╝ ╚═╝
           [ DAILY NOIR MICRO-CRIME INVESTIGATION ]
"""

# Clean 4-line centered facial expressions (without side text overlap)
ASCII_FACES = {
    "calm": """  .---.  
 / - - \\ 
|   •   |
 \\ ___ / """,

    "smug": """  .---.  
 / ¬ ‿ ¬\\
|   ~   |
 \\  -  / """,

    "nervous": """  .---.  
 / • _ •;\\
|  ' '  |
 \\ ~~~ / """,

    "defensive": """  .---.  
 / ಠ _ ಠ \\
|   =   |
 \\ ___ / """,

    "panicked": """  .---.  
 / ⊙ _ ⊙;\\
|   O   |
 \\ ~~~ / """
}

# Associated default quotes for suspect emotions
SUSPECT_QUOTES = {
    "calm": '"I have nothing to hide, officer."',
    "smug": '"Your deductions are amateur at best."',
    "nervous": '"Is it getting hot in here, or is it just me?"',
    "defensive": '"I demand to speak with my maritime attorney!"',
    "panicked": '"Wait, that\'s not what I meant at all!"'
}

def get_suspect_face(emotion: str = "calm") -> str:
    """Return 4-line clean ASCII face for given emotion."""
    return ASCII_FACES.get(emotion.lower(), ASCII_FACES["calm"])

def render_tokens(remaining: int, total: int = 5) -> str:
    """Renders retro terminal token counter with clean glyphs (no raw markup escape bugs)."""
    dots = []
    for i in range(total):
        if i < remaining:
            dots.append("[bold cyan]●[/bold cyan]")
        else:
            dots.append("[dim]○[/dim]")
    return "[bold cyan]TOKENS:[/bold cyan] " + " ".join(dots) + f" [bold]({remaining}/{total})[/bold]"

# Clockwise dots-in-a-square retro CRT loading animation frames
DOTS_SQUARE_FRAMES = [
    "[bold yellow]⠋ Suspect is nervously sweating & formulating an alibi...[/bold yellow]  [bold cyan]┌ ● · ┐[/bold cyan]",
    "[bold yellow]⠙ Suspect is nervously sweating & formulating an alibi...[/bold yellow]  [bold cyan]┌ · ● ┐[/bold cyan]",
    "[bold yellow]⠸ Suspect is nervously sweating & formulating an alibi...[/bold yellow]  [bold cyan]└ · ● ┘[/bold cyan]",
    "[bold yellow]⠴ Suspect is nervously sweating & formulating an alibi...[/bold yellow]  [bold cyan]└ ● · ┘[/bold cyan]",
]

WIN_HEADER_BANNER = """[bold green]
  ██████╗ ██╗   ██╗██╗██╗  ████████╗██╗   ██╗██╗
 ██╔════╝ ██║   ██║██║██║  ╚══██╔══╝╚██╗ ██╔╝██║
 ██║  ███╗██║   ██║██║██║     ██║    ╚████╔╝ ██║
 ██║   ██║██║   ██║██║██║     ██║     ╚██╔╝  ╚═╝
 ╚██████╔╝╚██████╔╝██║███████╗██║      ██║   ██╗
  ╚═════╝  ╚═════╝ ╚═╝╚══════╝╚═╝      ╚═╝   ╚═╝
══════════════════════════════════════════════════════════════════
    ★ ★ ★   CASE CLOSED: SUSPECT CONVICTED & JAILED!   ★ ★ ★
       CONTRADICTION EXPOSED // SUSPECT GUILTY AS CHARGED
══════════════════════════════════════════════════════════════════[/bold green]"""

LOSE_HEADER_BANNER = """[bold red]
  ██████╗ █████╗ ███████╗███████╗    ██████╗ ██████╗ ██╗     ██████╗ 
 ██╔════╝██╔══██╗██╔════╝██╔════╝   ██╔════╝██╔═══██╗██║     ██╔══██╗
 ██║     ███████║███████╗█████╗     ██║     ██║   ██║██║     ██║  ██║
 ██║     ██╔══██║╚════██║██╔══╝     ██║     ██║   ██║██║     ██║  ██║
 ╚██████╗██║  ██║███████║███████╗   ╚██████╗╚██████╔╝███████╗██████╔╝
  ╚═════╝╚═╝  ╚═╝╚══════╝╚══════╝    ╚═════╝ ╚═════╝ ╚══════╝╚═════╝ 
══════════════════════════════════════════════════════════════════════
     ✖ ✖ ✖   CASE COLD: INSUFFICIENT EVIDENCE   ✖ ✖ ✖
        OUT OF TOKENS // SUSPECT WALKED FREE
══════════════════════════════════════════════════════════════════════[/bold red]"""

JUDGE_LOADING_FRAMES = [
    "[bold red]⠋ Contradiction Judge is verifying logic against dossier...[/bold red]  [bold yellow]┌ ● · ┐[/bold yellow]",
    "[bold red]⠙ Contradiction Judge is verifying logic against dossier...[/bold red]  [bold yellow]┌ · ● ┐[/bold yellow]",
    "[bold red]⠸ Contradiction Judge is verifying logic against dossier...[/bold red]  [bold yellow]└ · ● ┘[/bold yellow]",
    "[bold red]⠴ Contradiction Judge is verifying logic against dossier...[/bold red]  [bold yellow]└ ● · ┘[/bold yellow]",
]

HINT_LOADING_FRAMES = [
    "[bold magenta]⠋ Noir Narrator is scouring shadows for a cryptic lead...[/bold magenta]  [bold cyan]┌ ● · ┐[/bold cyan]",
    "[bold magenta]⠙ Noir Narrator is scouring shadows for a cryptic lead...[/bold magenta]  [bold cyan]┌ · ● ┐[/bold cyan]",
    "[bold magenta]⠸ Noir Narrator is scouring shadows for a cryptic lead...[/bold magenta]  [bold cyan]└ · ● ┘[/bold cyan]",
    "[bold magenta]⠴ Noir Narrator is scouring shadows for a cryptic lead...[/bold magenta]  [bold cyan]└ ● · ┘[/bold cyan]",
]

# Procedural Voice-Stress Polygraph & Digital Number Matrix Animation Generator
def generate_polygraph_frames(count: int = 16) -> list:
    """Generate 4-line, exactly 72-character wide voice-stress polygraph frames with live numbers."""
    chars_wave = [' ', '▂', '▃', '▄', '▅', '▆', '▇', '█']
    frames = []
    for i in range(count):
        t = (i / count) * 2 * math.pi

        hex_reg = f"{(int(18400 + 4000 * math.sin(t))):04X}"
        freq_val = 138.4 + 14.2 * math.sin(t * 1.5)
        freq = f"{freq_val:5.1f}"
        stress = max(10, min(99, int(72 + 20 * math.sin(t * 2))))
        truth = max(10, min(99, int(22 - 12 * math.cos(t * 1.2))))
        bpm = max(60, min(99, int(84 + 14 * math.sin(t))))
        rec = "[bold red]● REC[/bold red]" if (i % 2 == 0) else "[dim red]○ REC[/dim red]"

        wave = ""
        for x in range(26):
            v = (math.sin(x * 0.45 + t * 2) + math.cos(x * 0.2 - t) + 2.0) / 4.0
            idx = int(v * (len(chars_wave) - 1))
            wave += chars_wave[max(0, min(len(chars_wave) - 1, idx))]

        digits = "".join([str((int(x * 3 + i * 5 + math.sin(x + t) * 10)) % 10) for x in range(24)])

        l0 = f"[bold cyan]┌─[/bold cyan] [bold yellow]VOICE-STRESS POLYGRAPH[/bold yellow] [dim cyan]────[/dim cyan] [dim]NODE:[/dim][cyan]0x{hex_reg}[/cyan] [dim cyan]──[/dim cyan] [dim]FREQ:[/dim][yellow]{freq}k[/yellow] [dim cyan]──[/dim cyan] {rec} [bold cyan]────┐[/bold cyan]"
        l1 = f"[bold cyan]│[/bold cyan] [dim]SIGNAL:[/dim] [bold green]{wave}[/bold green] [bold yellow]STRESS:[/bold yellow][bold red]{stress:2d}%[/bold red] [dim]|[/dim] [dim]BPM:[/dim][orange3]{bpm:2d}[/orange3] [dim]|[/dim] [bold yellow]TRUTH:[/bold yellow][bold red]{truth:2d}%[/bold red]   [bold cyan]│[/bold cyan]"
        l2 = f"[bold cyan]│[/bold cyan] [dim]CIPHER:[/dim] [cyan]{digits[:4]} {digits[4:8]} {digits[8:12]} {digits[12:16]} {digits[16:20]} {digits[20:]}[/cyan] [dim]|[/dim] [dim]MEM:[/dim][yellow]0x7FFE[/yellow] [dim]|[/dim] [dim]CONF:[/dim][green]94.2%[/green]      [bold cyan]│[/bold cyan]"
        l3 = f"[bold cyan]└─[/bold cyan] [dim]FORENSIC LIE-DETECTION ENGINE // DISCREPANCY PROBABILITY: [bold red]HIGH[/bold red][/dim] [dim cyan]─────┘[/dim cyan]"

        frames.append(f"{l0}\n{l1}\n{l2}\n{l3}")
    return frames

# Looped Title Menu Pixel Animation (Voice-stress polygraph, rolling cipher numbers, frequency waveform)
MENU_PIXEL_ANIM_FRAMES = generate_polygraph_frames(16)

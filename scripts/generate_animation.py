#!/usr/bin/env python3
"""Procedural Cyber & Number Animation Generator for THE ALIBI.

Generates mathematically-smooth, retro-cyber terminal animations including:
- Polygraph: Voice-stress frequency equalizer, live pulse BPM, hex registers, cipher numbers.
- Matrix: Digital forensic rain with cascading code & deciphering status.
- Spectrum: Audio FFT frequency analyzer with live decibel meters.
"""

import math
import sys
import time
import argparse
from typing import List
from rich.console import Console

console = Console()

from alibi.ui.ascii_art import generate_polygraph_frames

def generate_matrix_frames(count: int = 16) -> List[str]:
    """Generate 4-line digital matrix cipher numbers animation."""
    frames = []
    for i in range(count):
        t = (i / count) * 2 * math.pi
        hex_target = f"0x{(int(32000 + 10000 * math.sin(t * 1.5))):04X}"
        pct = max(10, min(99, int(50 + 45 * math.sin(t))))

        row1 = " ".join([f"{(int(x * 7 + i * 3 + math.sin(x + t) * 50)) % 100:02d}" for x in range(14)])
        row2 = " ".join([f"{(int(x * 11 + i * 5 + math.cos(x + t) * 80)) % 100:02d}" for x in range(14)])

        l0 = f"[bold green]┌─[/bold green] [bold cyan]CYBER-FORENSIC CIPHER STREAM[/bold cyan] [dim green]──────[/dim green] [dim]HASH:[/dim][yellow]{hex_target}[/yellow] [dim green]───────[/dim green] [bold green]─┐[/bold green]"
        l1 = f"[bold green]│[/bold green] [dim]STREAM 1:[/dim] [green]{row1}[/green] [dim]|[/dim] [dim]RATE:[/dim][cyan]1.4MB/s[/cyan] [bold green]│[/bold green]"
        l2 = f"[bold green]│[/bold green] [dim]STREAM 2:[/dim] [dim green]{row2}[/dim green] [dim]|[/dim] [dim]CONF:[/dim][yellow]91.8%[/yellow]   [bold green]│[/bold green]"
        l3 = f"[bold green]└─[/bold green] [dim]DECRYPTING TESTIMONY -- PROBABILITY OF FABRICATION:[/dim] [bold red]{pct:2d}%[/bold red] [dim green]──┘[/dim green]"
        frames.append(f"{l0}\n{l1}\n{l2}\n{l3}")
    return frames

def run_live_preview(style: str = "polygraph", fps: float = 8.0, duration: float = 5.0) -> None:
    """Run a live in-terminal preview loop."""
    frames = generate_polygraph_frames(16) if style == "polygraph" else generate_matrix_frames(16)
    interval = 1.0 / fps
    end_time = time.time() + duration if duration > 0 else float("inf")

    console.clear()
    console.print(f"[bold cyan]>>> Live Preview: {style.upper()} ({fps} FPS) -- Press Ctrl+C to Stop <<<\n[/bold cyan]")

    idx = 0
    try:
        while time.time() < end_time:
            # Print frame with carriage return repositioning
            frame = frames[idx % len(frames)]
            console.print(f"\r{frame}", end="")
            time.sleep(interval)
            idx += 1
            # Move cursor up 4 lines
            sys.stdout.write("\033[4A\r")
            sys.stdout.flush()
    except KeyboardInterrupt:
        pass
    finally:
        sys.stdout.write("\033[4B\n")
        sys.stdout.flush()
        console.print("[dim]Preview completed.[/dim]")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Procedural Number & Polygraph Animation Generator")
    parser.add_argument("--style", choices=["polygraph", "matrix"], default="polygraph", help="Animation style")
    parser.add_argument("--preview", action="store_true", help="Run live in-terminal preview")
    parser.add_argument("--fps", type=float, default=8.0, help="Frames per second for preview")
    parser.add_argument("--duration", type=float, default=5.0, help="Duration in seconds (0 = infinite)")
    args = parser.parse_args()

    if args.preview:
        run_live_preview(style=args.style, fps=args.fps, duration=args.duration)
    else:
        frames = generate_polygraph_frames(16) if args.style == "polygraph" else generate_matrix_frames(16)
        console.print(f"[bold green]Generated {len(frames)} procedural {args.style} frames successfully![/bold green]\n")
        console.print(frames[0])

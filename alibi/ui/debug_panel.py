from textual.app import ComposeResult
from textual.screen import ModalScreen
from textual.widgets import Header, Footer, Static, TabbedContent, TabPane, RichLog, Button
from textual.containers import Container, Horizontal, VerticalScroll
from rich.text import Text
from rich.panel import Panel
from rich.table import Table

class DebugPanelScreen(ModalScreen):
    """F2 Live Debug Panel showing Agent Traces, RAG Retrievals, and Tool Executions."""

    BINDINGS = [
        ("f2", "dismiss", "Close Debug Panel"),
        ("escape", "dismiss", "Close Debug Panel")
    ]

    def __init__(self, game_manager):
        super().__init__()
        self.game_manager = game_manager

    def compose(self) -> ComposeResult:
        with Container(id="debug-modal-container"):
            yield Static("═══ [ LIVE AGENTIC & RAG ARCHITECTURE TRACE (F2) ] ═══", id="debug-title")
            with TabbedContent():
                with TabPane("Agent Traces", id="tab-traces"):
                    yield VerticalScroll(id="traces-scroll")
                with TabPane("RAG Retrievals", id="tab-rag"):
                    yield VerticalScroll(id="rag-scroll")
                with TabPane("Tool Calls", id="tab-tools"):
                    yield VerticalScroll(id="tools-scroll")
                with TabPane("Hidden State", id="tab-hidden"):
                    yield VerticalScroll(id="hidden-scroll")
            with Horizontal(id="debug-actions"):
                yield Button("Refresh Traces", id="btn-refresh-debug", variant="primary")
                yield Button("Close (F2 / Esc)", id="btn-close-debug", variant="default")

    def on_mount(self):
        self.refresh_views()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-close-debug":
            self.dismiss()
        elif event.button.id == "btn-refresh-debug":
            self.refresh_views()

    def refresh_views(self):
        client = self.game_manager.client
        rag = self.game_manager.rag_store
        suspect = self.game_manager.suspect_agent
        session = self.game_manager.session

        # 1. Traces Pane
        traces_scroll = self.query_one("#traces-scroll", VerticalScroll)
        traces_scroll.remove_children()
        
        if not client.last_trace:
            traces_scroll.mount(Static("[dim]No LLM calls recorded in this session yet.[/dim]"))
        else:
            for item in reversed(client.last_trace[-10:]):
                t_table = Table(title=f"Agent: [bold yellow]{item['agent']}[/bold yellow] | Latency: [cyan]{item['latency_ms']}ms[/cyan] | Model: {item['model']}", expand=True)
                t_table.add_column("Field", style="bold green", width=12)
                t_table.add_column("Content", style="white")
                t_table.add_row("Timestamp", item["iso_time"])
                t_table.add_row("Prompt", item["prompt"][:250] + ("..." if len(item["prompt"]) > 250 else ""))
                t_table.add_row("Response", item["response"][:250] + ("..." if len(item["response"]) > 250 else ""))
                traces_scroll.mount(Static(Panel(t_table, border_style="green")))

        # 2. RAG Retrievals Pane
        rag_scroll = self.query_one("#rag-scroll", VerticalScroll)
        rag_scroll.remove_children()
        if not rag or not rag.last_retrievals:
            rag_scroll.mount(Static("[dim]No RAG retrievals performed yet.[/dim]"))
        else:
            for ret in reversed(rag.last_retrievals[-6:]):
                r_table = Table(title=f"Query: \"{ret['query']}\" | Collection: [bold magenta]{ret['collection']}[/bold magenta]", expand=True)
                r_table.add_column("Rank / ID", style="bold cyan", width=15)
                r_table.add_column("Score (Sim+Overlap)", style="bold yellow", width=22)
                r_table.add_column("Retrieved Chunk Text", style="white")
                for i, r in enumerate(ret["results"], 1):
                    r_table.add_row(f"#{i} {r['id']}", str(r['score']), r['text'])
                rag_scroll.mount(Static(Panel(r_table, border_style="magenta")))

        # 3. Tool Calls Pane
        tools_scroll = self.query_one("#tools-scroll", VerticalScroll)
        tools_scroll.remove_children()
        if not suspect or not suspect.last_tool_calls:
            tools_scroll.mount(Static("[dim]No suspect tool calls executed in the latest turn.[/dim]"))
        else:
            for tc in suspect.last_tool_calls:
                tc_table = Table(title=f"Tool Execution: [bold yellow]{tc.get('tool')}[/bold yellow]", expand=True)
                tc_table.add_column("Key", style="bold green", width=10)
                tc_table.add_column("Detail", style="white")
                tc_table.add_row("Topic", str(tc.get("topic")))
                tc_table.add_row("Output", str(tc.get("result")))
                tools_scroll.mount(Static(Panel(tc_table, border_style="yellow")))

        # 4. Hidden State Pane
        hidden_scroll = self.query_one("#hidden-scroll", VerticalScroll)
        hidden_scroll.remove_children()
        if not session:
            hidden_scroll.mount(Static("[dim]No active session.[/dim]"))
        else:
            h_table = Table(title="Suspect Hidden State & Lie Strategy", expand=True)
            h_table.add_column("Component", style="bold cyan", width=20)
            h_table.add_column("Details", style="white")
            h_table.add_row("Cover Story", session.case.lie_plan.cover_story)
            wp_desc = "\n".join([f"• [{wp.id}] Conflicts: {wp.conflicts_with} | Slip: {wp.planned_slip}" for wp in session.case.lie_plan.weak_points])
            h_table.add_row("Planned Weak Points", wp_desc)
            if session.transcript:
                latest = session.transcript[-1]
                h_table.add_row("Latest Emotion", latest.emotion)
                h_table.add_row("Latest Inner Reasoning", latest.inner_reasoning or "N/A")
            hidden_scroll.mount(Static(Panel(h_table, border_style="cyan")))

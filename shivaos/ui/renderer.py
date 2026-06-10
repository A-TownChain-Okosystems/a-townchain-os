"""
ShivaOS UI Renderer — Issue #28 (Kap. 40)
Terminal-basierter UI-Renderer für ShivaOS (L10 UI Layer).
Unterstützt: TUI, ANSI-Escape, Web-Export.
"""
import os, time
from typing import List, Dict, Any, Optional
from enum import Enum

class Color(Enum):
    BLACK   = "[30m"
    RED     = "[31m"
    GREEN   = "[32m"
    YELLOW  = "[33m"
    BLUE    = "[34m"
    MAGENTA = "[35m"
    CYAN    = "[36m"
    WHITE   = "[37m"
    NEON    = "[96m"
    RESET   = "[0m"
    BOLD    = "[1m"
    DIM     = "[2m"

class UIComponent:
    def render(self, width: int = 80) -> str: return ""

class TextBox(UIComponent):
    def __init__(self, text: str, color: Color = Color.WHITE,
                  bold: bool = False):
        self.text = text; self.color = color; self.bold = bold
    def render(self, width=80) -> str:
        prefix = (Color.BOLD.value if self.bold else "") + self.color.value
        return f"{prefix}{self.text}{Color.RESET.value}"

class Panel(UIComponent):
    def __init__(self, title: str, children: List[UIComponent],
                  border_color: Color = Color.CYAN):
        self.title = title; self.children = children
        self.border_color = border_color
    def render(self, width=80) -> str:
        bc = self.border_color.value
        r  = Color.RESET.value
        lines = [f"{bc}╔{'═'*(width-2)}╗{r}",
                  f"{bc}║ {Color.BOLD.value}{self.title:<{width-4}}{r}{bc} ║{r}",
                  f"{bc}╠{'═'*(width-2)}╣{r}"]
        for child in self.children:
            content = child.render(width-4)
            lines.append(f"{bc}║ {content:<{width-4}} {bc}║{r}")
        lines.append(f"{bc}╚{'═'*(width-2)}╝{r}")
        return "
".join(lines)

class ProgressBar(UIComponent):
    def __init__(self, label: str, value: float, max_val: float = 100,
                  color: Color = Color.NEON):
        self.label = label; self.value = value
        self.max_val = max_val; self.color = color
    def render(self, width=80) -> str:
        pct   = min(1.0, self.value / self.max_val)
        bar_w = width - len(self.label) - 12
        filled= int(bar_w * pct)
        bar   = "█" * filled + "░" * (bar_w - filled)
        return f"{self.label:<20} {self.color.value}{bar}{Color.RESET.value} {pct*100:.1f}%"

class ShivaOSRenderer:
    """ShivaOS TUI Renderer — Neon-Cyberpunk Ästhetik."""
    WIDTH = 80

    def __init__(self):
        self._screen: List[UIComponent] = []
        self._fps    = 0
        self._last   = time.time()

    def clear(self):
        os.system("clear" if os.name != "nt" else "cls")

    def add(self, component: UIComponent): self._screen.append(component)
    def reset(self): self._screen = []

    def render_frame(self):
        now = time.time(); self._fps = round(1/(now - self._last + 0.001)); self._last = now
        output = []
        for comp in self._screen:
            output.append(comp.render(self.WIDTH))
        print("
".join(output))

    def dashboard(self, stats: Dict[str, Any]):
        """Standard ShivaOS Dashboard rendern."""
        self.reset()
        self.add(TextBox(f"  ShivaOS v2.0.0 | FPS: {self._fps}",
                          Color.NEON, bold=True))
        self.add(Panel("SYSTEM STATUS", [
            TextBox(f"Uptime:  {stats.get('uptime','?')}s"),
            TextBox(f"Prozesse: {stats.get('processes','?')}"),
            ProgressBar("CPU", stats.get('cpu',0)),
            ProgressBar("RAM", stats.get('ram',0)),
        ]))
        self.add(Panel("BLOCKCHAIN", [
            TextBox(f"Block-Höhe: {stats.get('height',0)}"),
            TextBox(f"TPS:        {stats.get('tps',0.0)}"),
            ProgressBar("Sync", stats.get('sync',100)),
        ], Color.MAGENTA))
        self.render_frame()

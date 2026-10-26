from dataclasses import dataclass, asdict
from pathlib import Path

@dataclass
class Clip:
    path: str
    source_start: float = 0.0
    source_end: float | None = None
    label: str = ""

    @property
    def name(self): return self.label or Path(self.path).name
    @property
    def duration(self): return max(0.0, (self.source_end or 0.0) - self.source_start)
    def clone(self): return Clip(**asdict(self))

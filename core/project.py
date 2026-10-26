import json
from dataclasses import asdict
from pathlib import Path
from .models import Clip

class Project:
    def __init__(self): self.name="Projeto sem nome"; self.clips=[]
    def snapshot(self): return [c.clone() for c in self.clips]
    def restore(self, snap): self.clips=[c.clone() for c in snap]
    @property
    def duration(self): return sum(c.duration for c in self.clips)
    def save(self,path):
        Path(path).write_text(json.dumps({"version":2,"name":self.name,"clips":[asdict(c) for c in self.clips]},ensure_ascii=False,indent=2),encoding="utf-8")
    def load(self,path):
        d=json.loads(Path(path).read_text(encoding="utf-8")); self.name=d.get("name","Projeto")
        self.clips=[Clip(**x) for x in d.get("clips",[])]

from core.models import Clip
from core.project import Project
def test_duration():
    p=Project(); p.clips=[Clip("a.mp4",1,3),Clip("b.mp4",0,4)]; assert p.duration==6

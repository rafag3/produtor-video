from PySide6.QtCore import Qt,Signal,QRectF
from PySide6.QtGui import QColor,QPainter,QPen,QFont
from PySide6.QtWidgets import QWidget,QToolTip

class TimelineWidget(QWidget):
    seekRequested=Signal(float); clipSelected=Signal(int)
    def __init__(self):
        super().__init__(); self.clips=[]; self.playhead=0.0; self.selected=-1; self.zoom=1.0; self.setMinimumHeight(190); self.setMouseTracking(True)
    @property
    def total(self): return sum(c.duration for c in self.clips)
    def set_clips(self,clips): self.clips=clips; self.update()
    def set_playhead(self,t): self.playhead=max(0,min(t,self.total)); self.update()
    def time_to_x(self,t):
        usable=max(1,self.width()-24); return 12+(t/max(self.total,1))*usable
    def x_to_time(self,x): return max(0,min(self.total,(x-12)/max(1,self.width()-24)*max(self.total,1)))
    def clip_at(self,t):
        acc=0
        for i,c in enumerate(self.clips):
            if acc<=t<=acc+c.duration:return i,acc
            acc+=c.duration
        return -1,0
    def mousePressEvent(self,e):
        t=self.x_to_time(e.position().x()); i,_=self.clip_at(t); self.selected=i; self.clipSelected.emit(i); self.seekRequested.emit(t); self.update()
    def mouseMoveEvent(self,e):
        t=self.x_to_time(e.position().x()); QToolTip.showText(e.globalPosition().toPoint(),f"{t:.2f} s",self)
    def paintEvent(self,e):
        p=QPainter(self); p.fillRect(self.rect(),QColor("#17191c")); p.setRenderHint(QPainter.Antialiasing)
        total=max(self.total,1); left=12; right=self.width()-12; top=40; h=68
        p.setPen(QColor("#aab2bd")); p.setFont(QFont("Segoe UI",8))
        step=1 if total<=30 else 5 if total<=120 else 10 if total<=600 else 60
        t=0
        while t<=total:
            x=self.time_to_x(t); p.drawLine(int(x),20,int(x),32); p.drawText(int(x)-12,15,f"{int(t//60):02d}:{int(t%60):02d}"); t+=step
        colors=[QColor("#2878c8"),QColor("#386fa4")]; acc=0
        for i,c in enumerate(self.clips):
            x1=self.time_to_x(acc); x2=self.time_to_x(acc+c.duration); r=QRectF(x1,top,max(2,x2-x1-2),h)
            p.setBrush(QColor("#e39b25") if i==self.selected else colors[i%2]); p.setPen(QPen(QColor("white") if i==self.selected else QColor("#79b8ff"),2)); p.drawRoundedRect(r,4,4)
            p.setPen(Qt.white); name=c.name[:24]; p.drawText(r.adjusted(6,5,-4,-4),Qt.TextWordWrap,name); acc+=c.duration
        p.setPen(QPen(QColor("#55d6be"),2)); p.drawText(12,135,"ÁUDIO"); p.drawLine(65,132,right,132)
        x=self.time_to_x(self.playhead); p.setPen(QPen(QColor("#ff4d4d"),2)); p.drawLine(int(x),25,int(x),160); p.setBrush(QColor("#ff4d4d")); p.drawEllipse(int(x)-4,21,8,8)

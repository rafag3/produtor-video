import json
from pathlib import Path
from PySide6.QtCore import Qt,QUrl,QThread,Signal
from PySide6.QtGui import QAction,QKeySequence
from PySide6.QtMultimedia import QMediaPlayer,QAudioOutput
from PySide6.QtMultimediaWidgets import QVideoWidget
from PySide6.QtWidgets import *
from core.models import Clip
from core.project import Project
from engines.ffmpeg_engine import FFmpegEngine
from engines.scene_engine import SceneEngine
from engines.whisper_engine import WhisperEngine
from ui.timeline import TimelineWidget

class Worker(QThread):
    progress=Signal(int); done=Signal(object); failed=Signal(str)
    def __init__(self,fn): super().__init__(); self.fn=fn
    def run(self):
        try:self.done.emit(self.fn(self.progress.emit))
        except Exception as e:self.failed.emit(str(e))

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__(); self.setWindowTitle("Rafa Video Studio AI V2 - Timeline e Auto Cut"); self.resize(1400,900)
        self.project=Project(); self.engine=FFmpegEngine(); self.scene=SceneEngine(); self.whisper=WhisperEngine(); self.undo_stack=[]; self.redo_stack=[]; self.current_project_time=0; self.loading=False
        self.player=QMediaPlayer(); self.audio=QAudioOutput(); self.player.setAudioOutput(self.audio); self.audio.setVolume(.75)
        self.build_ui(); self.build_menu(); self.sync()
    def build_ui(self):
        root=QWidget(); self.setCentralWidget(root); outer=QVBoxLayout(root); upper=QHBoxLayout(); outer.addLayout(upper,1)
        left=QVBoxLayout(); upper.addLayout(left,2); left.addWidget(QLabel("Mídia / segmentos")); self.list=QListWidget(); self.list.currentRowChanged.connect(self.select_list); left.addWidget(self.list)
        row=QHBoxLayout();
        for txt,fn in [("+ Vídeos",self.add_videos),("Remover",self.delete_selected),("↑",lambda:self.move(-1)),("↓",lambda:self.move(1))]:
            b=QPushButton(txt); b.clicked.connect(fn); row.addWidget(b)
        left.addLayout(row)
        center=QVBoxLayout(); upper.addLayout(center,5); self.video=QVideoWidget(); self.video.setMinimumHeight(360); self.player.setVideoOutput(self.video); center.addWidget(self.video)
        ctl=QHBoxLayout(); self.play=QPushButton("▶ / ⏸"); self.play.clicked.connect(self.toggle); ctl.addWidget(self.play); self.position=QLabel("00:00.00 / 00:00.00"); ctl.addWidget(self.position); center.addLayout(ctl)
        right=QVBoxLayout(); upper.addLayout(right,2); right.addWidget(QLabel("Edição e IA"))
        buttons=[("✂ Dividir no playhead",self.split_at_playhead),("🗑 Excluir segmento",self.delete_selected),("↶ Desfazer",self.undo),("↷ Refazer",self.redo),("🎬 Detectar cenas",self.detect_scenes),("🔇 Auto corte de silêncio",self.auto_silence),("🎙 Transcrever",self.transcribe)]
        for txt,fn in buttons:
            b=QPushButton(txt); b.clicked.connect(fn); right.addWidget(b)
        right.addStretch(); self.progress=QProgressBar(); self.progress.hide(); right.addWidget(self.progress); exp=QPushButton("🎬 Exportar vídeo final"); exp.clicked.connect(self.export); right.addWidget(exp)
        bar=QHBoxLayout(); outer.addLayout(bar); bar.addWidget(QLabel("TIMELINE")); self.time_label=QLabel("Playhead: 0.00 s"); bar.addWidget(self.time_label); bar.addStretch(); minus=QPushButton("−"); plus=QPushButton("+"); bar.addWidget(QLabel("Zoom")); bar.addWidget(minus); bar.addWidget(plus)
        self.timeline=TimelineWidget(); self.timeline.seekRequested.connect(self.seek_project); self.timeline.clipSelected.connect(self.select_timeline_clip); outer.addWidget(self.timeline)
        self.player.positionChanged.connect(self.on_position); self.player.mediaStatusChanged.connect(self.on_status)
    def build_menu(self):
        m=self.menuBar().addMenu("Projeto")
        for text,fn,shortcut in [("Novo",self.new,"Ctrl+N"),("Abrir",self.open_project,"Ctrl+O"),("Salvar",self.save_project,"Ctrl+S")]:
            a=QAction(text,self); a.triggered.connect(fn); a.setShortcut(QKeySequence(shortcut)); m.addAction(a)
    def push_undo(self): self.undo_stack.append(self.project.snapshot()); self.redo_stack.clear()
    def undo(self):
        if self.undo_stack:self.redo_stack.append(self.project.snapshot()); self.project.restore(self.undo_stack.pop()); self.sync()
    def redo(self):
        if self.redo_stack:self.undo_stack.append(self.project.snapshot()); self.project.restore(self.redo_stack.pop()); self.sync()
    def fmt(self,s): return f"{int(s//60):02d}:{s%60:05.2f}"
    def sync(self):
        self.list.blockSignals(True); self.list.clear()
        for i,c in enumerate(self.project.clips): self.list.addItem(f"{i+1:02d}. {c.name} | {self.fmt(c.duration)}")
        self.list.blockSignals(False); self.timeline.set_clips(self.project.clips); self.statusBar().showMessage(f"{len(self.project.clips)} segmentos | duração final {self.fmt(self.project.duration)}")
    def add_videos(self):
        files,_=QFileDialog.getOpenFileNames(self,"Adicionar vídeos","","Vídeos (*.mp4 *.mov *.mkv *.avi *.webm)")
        if not files:return
        self.push_undo()
        try:
            for f in files:self.project.clips.append(Clip(f,0,self.engine.duration(f)))
            self.sync()
        except Exception as e:QMessageBox.critical(self,"Erro",str(e))
    def project_location(self,t):
        acc=0
        for i,c in enumerate(self.project.clips):
            if t<=acc+c.duration:return i,c.source_start+(t-acc),acc
            acc+=c.duration
        return (-1,0,acc)
    def seek_project(self,t):
        i,source,_=self.project_location(t)
        if i<0:return
        self.current_project_time=t; self.timeline.set_playhead(t); self.time_label.setText(f"Playhead: {t:.2f} s"); self.loading=True
        self.player.setSource(QUrl.fromLocalFile(self.project.clips[i].path)); self.player.setPosition(int(source*1000)); self.list.setCurrentRow(i); self.loading=False
    def select_timeline_clip(self,i):
        if i>=0:self.list.setCurrentRow(i)
    def select_list(self,i):
        if i<0 or self.loading:return
        acc=sum(c.duration for c in self.project.clips[:i]); self.seek_project(acc)
    def on_position(self,ms):
        i=self.list.currentRow()
        if i<0:return
        c=self.project.clips[i]; acc=sum(x.duration for x in self.project.clips[:i]); t=acc+max(0,ms/1000-c.source_start); self.current_project_time=min(t,acc+c.duration); self.timeline.set_playhead(self.current_project_time); self.time_label.setText(f"Playhead: {self.current_project_time:.2f} s"); self.position.setText(f"{self.fmt(max(0,ms/1000-c.source_start))} / {self.fmt(c.duration)}")
        if ms/1000>=c.source_end-.03:
            if i+1<len(self.project.clips): self.seek_project(acc+c.duration+.001); self.player.play()
            else:self.player.pause()
    def on_status(self,status): pass
    def toggle(self):
        if self.player.playbackState()==QMediaPlayer.PlayingState:self.player.pause()
        else:self.player.play()
    def split_at_playhead(self):
        i,source,_=self.project_location(self.current_project_time)
        if i<0:return
        c=self.project.clips[i]
        if source<=c.source_start+.05 or source>=c.source_end-.05:return QMessageBox.information(self,"Corte","Posicione o playhead dentro do segmento.")
        self.push_undo(); self.project.clips[i:i+1]=[Clip(c.path,c.source_start,source,c.label),Clip(c.path,source,c.source_end,c.label)]; self.sync(); self.list.setCurrentRow(i+1)
    def delete_selected(self):
        i=self.list.currentRow()
        if i>=0:self.push_undo(); self.project.clips.pop(i); self.sync()
    def move(self,d):
        i=self.list.currentRow(); j=i+d
        if i>=0 and 0<=j<len(self.project.clips):self.push_undo(); self.project.clips[i],self.project.clips[j]=self.project.clips[j],self.project.clips[i]; self.sync(); self.list.setCurrentRow(j)
    def detect_scenes(self):
        i=self.list.currentRow()
        if i<0:return
        c=self.project.clips[i]
        try:
            scenes=self.scene.detect(c.path); scenes=[(max(a,c.source_start),min(b,c.source_end)) for a,b in scenes if min(b,c.source_end)>max(a,c.source_start)]
            self.push_undo(); self.project.clips[i:i+1]=[Clip(c.path,a,b,c.label) for a,b in scenes]; self.sync(); QMessageBox.information(self,"Cenas",f"{len(scenes)} segmentos criados e exibidos na timeline.")
        except Exception as e:QMessageBox.critical(self,"Erro",str(e))
    def auto_silence(self):
        i=self.list.currentRow()
        if i<0:return
        c=self.project.clips[i]
        dlg=QDialog(self); dlg.setWindowTitle("Auto corte de silêncio"); f=QFormLayout(dlg); db=QDoubleSpinBox(); db.setRange(-80,-5); db.setValue(-35); dur=QDoubleSpinBox(); dur.setRange(.2,10); dur.setValue(.7); pad=QDoubleSpinBox(); pad.setRange(0,.8); pad.setValue(.15); f.addRow("Limiar (dB)",db); f.addRow("Silêncio mínimo (s)",dur); f.addRow("Margem preservada (s)",pad); box=QDialogButtonBox(QDialogButtonBox.Ok|QDialogButtonBox.Cancel); box.accepted.connect(dlg.accept); box.rejected.connect(dlg.reject); f.addRow(box)
        if dlg.exec()!=QDialog.Accepted:return
        try:
            sil=self.engine.detect_silences(c.path,db.value(),dur.value()); sil=[(max(a,c.source_start),min(b,c.source_end)) for a,b in sil if b>c.source_start and a<c.source_end]
            if not sil:return QMessageBox.information(self,"Auto Cut","Nenhum silêncio foi encontrado com esses parâmetros.")
            msg="\n".join(f"{a:.2f}s → {b:.2f}s" for a,b in sil[:20]); ans=QMessageBox.question(self,"Revisar sugestões",f"Silêncios encontrados: {len(sil)}\n\n{msg}\n\nAplicar os cortes e remover esses intervalos?")
            if ans!=QMessageBox.Yes:return
            keep=[]; cursor=c.source_start
            for a,b in sil:
                end=max(cursor,a+pad.value())
                if end-cursor>.05:keep.append(Clip(c.path,cursor,end,c.label))
                cursor=max(cursor,b-pad.value())
            if c.source_end-cursor>.05:keep.append(Clip(c.path,cursor,c.source_end,c.label))
            self.push_undo(); self.project.clips[i:i+1]=keep; self.sync(); QMessageBox.information(self,"Auto Cut",f"Timeline atualizada com {len(keep)} trechos preservados.")
        except Exception as e:QMessageBox.critical(self,"Erro",str(e))
    def transcribe(self):
        i=self.list.currentRow()
        if i<0:return
        try:
            c=self.project.clips[i]; data=self.whisper.transcribe(c.path); p=Path(c.path).with_suffix(".transcricao.json"); p.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding="utf-8"); QMessageBox.information(self,"Transcrição",f"Transcrição salva em:\n{p}")
        except Exception as e:QMessageBox.critical(self,"Erro",str(e))
    def export(self):
        out,_=QFileDialog.getSaveFileName(self,"Exportar","video_final.mp4","MP4 (*.mp4)")
        if not out:return
        self.progress.show(); self.worker=Worker(lambda cb:(self.engine.export(list(self.project.clips),out,cb),out)[1]); self.worker.progress.connect(self.progress.setValue); self.worker.done.connect(lambda p:(self.progress.hide(),QMessageBox.information(self,"Concluído",f"Vídeo criado:\n{p}"))); self.worker.failed.connect(lambda e:(self.progress.hide(),QMessageBox.critical(self,"Erro",e))); self.worker.start()
    def new(self): self.project=Project(); self.undo_stack=[]; self.redo_stack=[]; self.sync()
    def save_project(self):
        p,_=QFileDialog.getSaveFileName(self,"Salvar projeto","projeto_v2.rvs.json","Projeto (*.json)")
        if p:self.project.save(p)
    def open_project(self):
        p,_=QFileDialog.getOpenFileName(self,"Abrir projeto","","Projeto (*.json)")
        if p:self.project.load(p); self.undo_stack=[]; self.redo_stack=[]; self.sync()

import json,re,shutil,subprocess,tempfile
from pathlib import Path

class FFmpegEngine:
    def __init__(self,ffmpeg="ffmpeg",ffprobe="ffprobe"): self.ffmpeg=ffmpeg; self.ffprobe=ffprobe
    def available(self): return shutil.which(self.ffmpeg) is not None and shutil.which(self.ffprobe) is not None
    def duration(self,path):
        p=subprocess.run([self.ffprobe,"-v","error","-show_entries","format=duration","-of","json",path],capture_output=True,text=True,check=True)
        return float(json.loads(p.stdout)["format"]["duration"])
    def detect_silences(self,path,threshold=-35,min_duration=.7):
        cmd=[self.ffmpeg,"-hide_banner","-i",path,"-af",f"silencedetect=noise={threshold}dB:d={min_duration}","-f","null","-"]
        p=subprocess.run(cmd,capture_output=True,text=True)
        starts=[float(x) for x in re.findall(r"silence_start: ([0-9.]+)",p.stderr)]
        ends=[float(x) for x in re.findall(r"silence_end: ([0-9.]+)",p.stderr)]
        if len(starts)>len(ends): ends.append(self.duration(path))
        return list(zip(starts,ends))
    def export(self,clips,output,progress=None):
        if not self.available(): raise RuntimeError("FFmpeg/FFprobe não encontrados. Instale com: winget install Gyan.FFmpeg")
        if not clips: raise RuntimeError("A timeline está vazia.")
        with tempfile.TemporaryDirectory(prefix="rvs2_") as td:
            td=Path(td); parts=[]
            for i,c in enumerate(clips):
                out=td/f"part_{i:04d}.mp4"
                vf="scale=1280:720:force_original_aspect_ratio=decrease,pad=1280:720:(ow-iw)/2:(oh-ih)/2,setsar=1,fps=30"
                cmd=[self.ffmpeg,"-y","-ss",f"{c.source_start:.3f}","-to",f"{c.source_end:.3f}","-i",c.path,"-vf",vf,"-c:v","libx264","-preset","veryfast","-crf","20","-c:a","aac","-ar","48000","-ac","2",str(out)]
                subprocess.run(cmd,check=True,capture_output=True); parts.append(out)
                if progress: progress(int((i+1)*75/len(clips)))
            lst=td/"concat.txt"; lst.write_text("\n".join(f"file '{p.as_posix()}'" for p in parts),encoding="utf-8")
            subprocess.run([self.ffmpeg,"-y","-f","concat","-safe","0","-i",str(lst),"-c","copy",output],check=True,capture_output=True)
            if progress: progress(100)

class WhisperEngine:
    def transcribe(self,path,model_name="small"):
        from faster_whisper import WhisperModel
        model=WhisperModel(model_name,device="auto",compute_type="int8")
        segments,_=model.transcribe(path,vad_filter=True)
        return [{"start":s.start,"end":s.end,"text":s.text.strip()} for s in segments]

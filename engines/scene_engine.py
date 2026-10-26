class SceneEngine:
    def detect(self,path):
        from scenedetect import detect,AdaptiveDetector
        return [(a.get_seconds(),b.get_seconds()) for a,b in detect(path,AdaptiveDetector())]

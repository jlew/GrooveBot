from groovebot.ActionType import MediaSource
from groovebot.utils.FilePlayer import FilePlayer
from groovebot.MediaObject import MediaObject
from groovebot.GrooveBot import updateStatus
class FileData(MediaSource):
    def __init__(self):
        
        def stateChange(state, text):
            updateStatus(state, text)
        self.fp = FilePlayer(stateChange)
        
    def search(self, text):
        return [MediaObject(self, "LIN-ME-FO", title="Foreword", artist="Linkin Park", album="Meteora")]

    def play(self, mID):
        self.fp.playFile("/home/jlew/Music/Linkin Park/Meteora/1 - Foreword.ogg")

    def pause(self):
        self.fp.pause()

    def stop(self):
        self.fp.stop()

    def status(self):
        state, pos, dur = self.fp.get_time()
        return state, "%s/%s" % (pos, dur)

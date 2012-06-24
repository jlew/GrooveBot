from groovebot.ActionType import MediaSource

class DummySource(MediaSource):
    def search(self, text):
        return []

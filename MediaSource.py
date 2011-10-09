from PluginFramework import MediaSourceMount
from Constants import Status

class MediaSource(object):
    __metaclass__ = MediaSourceMount
    def search(self, text):
        return []

    def moreInfo(self, mediaId):
        pass

    def play(self, mediaId):
        pass

    def pause(self):
        pass

    def stop(self):
        pass

    def status(self):
        return Status.STOP, "Stopped"


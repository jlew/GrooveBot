class QueueContainer(object):
    def __init__(self):
        self.__played = []
        self.__queued = []

    def getNext(self):
        nextItm = self.__queued.pop(0)
        self.__played.append(nextItm)
        nextItm._setPlayed()
        return nextItm

    def add(self, queueobj):
        self.__queued.append(queueobj)

    def getQueuedItems(self):
        return self.__queued

    def getPlayedItems(self):
        return self.__played


from datetime import datetime
class QueueObject(object):
    def __init__(self, user, mediaObj):
        self.user = user
        self.mediaObj = mediaObj
        self.queueDate = datetime.now()
        self.played = False

    def _setPlayed(self):
        self.played = datetime.now()

class States(object):
    BUFFER = "Buffering"
    PLAY = "Playing"
    PAUSE = "Paused"
    STOP = "Stopped"
    ERROR = "Error"
    INIT = "Initializing"

class QueueActions(object):
    ADD = "ADDED"
    REMOVED = "REMOVED"
    PLAY = "PLAYING"
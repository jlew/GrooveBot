class States(object):
    BUFFER = "Buffering"
    PLAY = "Playing"
    PAUSE = "Paused"
    STOP = "Stopped"
    ERROR = "Error"
    INIT = "Initializing"

class QueueActions(object):
    ADD = "ADDED"
    REMOVE = "REMOVED"
    PLAY = "PLAYING"

class SearchKeys(object):
    ARTIST = "artist:"
    ALBUM = "album:"
    TITLE = "title:"

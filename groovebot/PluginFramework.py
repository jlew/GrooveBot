from twisted.python import log as logger

from Constants import States, QueueActions

def log(msg):
    logger.msg(msg, system="Plugin Framework")

class PluginMount(type):
    """
    METACLASS to capture plugins as they are loaded.
    """
    def __init__(cls, name, bases, attrs):
        if not hasattr(cls, "plugins"):
            # Meta classes are being created for the first time
            cls.plugins = []
        else:
            cls.plugins.append(cls)

class Plugin(object):
    def __init__(self, config):
        log("Initalizing Plugin: %s" % self.__class__.__name__)
        
    def configuration_change(self, key, value):
        log("Configuration Change: [%s] %s" % (key, value))


    
class MediaController(Plugin):
    __metaclass__ = PluginMount

    def statusUpdate(self, status, text, mediaObject):
        log("Status Changed: [%s] %s %s" % (status, text, mediaObject))
        
    def queueUpdated(self, action, queueObject):
        log("Queued Updated: [%s] %s" % (action, queueObject))

    def searchCompleted(self, context, search_results):
        for media_item in search_results:
            log("Searh Result: \"%s\" by \"%s\" on \"%s\"." % \
                (media_item.title, media_item.artist, media_item.album))
        

class MediaSource(Plugin):
    __metaclass__ = PluginMount
        
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
        return States.STOP, "Stopped"

class RadioSource(Plugin):
    __metaclass__ = PluginMount
    
    def play(self, mediaId):
        pass

    def pause(self):
        pass

    def stop(self):
        pass

    def status(self):
        return States.STOP, "Stopped"

from PluginFramework import MediaControllerMount, MediaSourceMount, ConfigurableMount
from Constants import States, QueueActions

class MediaController(object):
    __metaclass__ = MediaControllerMount
    def __init__(self):
        pass

    def statusUpdate(self, status):
        print "Status Changed: ", status
        
    def queueUpdated(self, action, queueObject):
        print "Queued Updated", action, queueObject

    def searchCompleted(self, context, search_results):
        for media_item in search_results:
            print "Searh Result: \"%s\" by \"%s\" on \"%s\"." % \
                (media_item.title, media_item.artist, media_item.album)
        

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
        return States.STOP, "Stopped"
    
class Configurable(object):
    __metaclass__ = ConfigurableMount
    def configuration_change(self, key, value):
        print "Configuration Change", key, value
        
    def getKeys(self):
        return [{"key":"exampleKey", "description": "An Example Key", "default":"42"}]
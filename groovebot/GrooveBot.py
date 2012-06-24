# Import twisted libraries
from twisted.internet.defer import DeferredList
from twisted.internet.threads import deferToThread
from twisted.python import log

# Import GrooveBot Classes
from groovebot.ActionType import MediaSource, MediaController
from groovebot.Queue import QueueContainer, QueueObject
from groovebot.Constants import States

import os

__runningPlugins = {}
__mediaSources = {}
__controllers = {}
__activeSource = None
__queue = QueueContainer()
__initalized = False

def registerSource(sourceId, sourceObj):
    log.msg("Registering Source: %s" % sourceId)
    if sourceId in __runningPlugins:
        __mediaSources[sourceId] = __runningPlugins[sourceId]
    else:
        log.msg("Creating new instance of plugin")
        __mediaSources[sourceId] = sourceObj()

def registerController(controllerId, controllerObj):
    log.msg("Registering Controller: %s" % controllerId)
    if controllerId in __runningPlugins:
        __controllers[controllerId] = __runningPlugins[controllerId]
    else:
        log.msg("Creating new instance of plugin")
        __controllers[controllerId] = controllerObj()

def initiateSearch(search_context, text):
    """
    Fires off a search in parallel to all the registered sources.
    When all the sources return their results (which will be in
    form of a list of media objects that match), the lists will
    be joined and sent to all controller searchCompleted methods.
    It is up to the controllers how they handle a request by using
    the search context (some controllers will listen for all where
    others may want to only react to requests by their own controller
    and/or user).

    @param search_context
            A search context object that stores information
            that may be needed by controllers sending the
            search request.  This object has information about
            the user, the source, and any extra context information
            if needed.

    @param text
            The text to be searched for in all the sources.
    """
    searches = []
    log.msg("Searching: \033[94m%s\033[0m" % text)

    # Fire off search in parallel
    for key, mediasrc in __mediaSources.items():
        log.msg("\tSending Search Request to \033[92m%s\033[0m" % key)
        searches.append(deferToThread(mediasrc.search, text))

    # When all searches return combine them.  The lists will be
    # returned as a list of a touples consisting of a sucess/failure
    # boolean followed by the results returned by the individual source
    dl = DeferredList(searches)

    def sendResults(results):
        """
        Combines the results returned by the deferred list
        into master_result and passes it to all the registered
        controllers.
        """
        log.msg("Search Returned from all sources")
        master_result = []
        for status, result in results:
            if status:
                master_result += result

        for key, mediactr in __controllers.items():
            log.msg("\tSending Result to \033[92m%s\033[0m" % key)
            mediactr.searchCompleted(search_context, master_result)

    dl.addCallback(sendResults)

def queue(mediaObj):
    log.msg("Queueing %s" % mediaObj)
    
    __queue.add(QueueObject(mediaObj))
    
    if not __activeSource:
        play()
    

def pause():
    if __activeSource:
        __activeSource.pause()

def resume():
    if __activeSource:
        __activeSource.resume()

def stop():
    if __activeSource:
        __activeSource.stop()

def play():
    global __activeSource
    nextItem = __queue.getNext()
    if nextItem:
        log.msg("Playing %s" % nextItem.mediaObj)
        __activeSource = nextItem.mediaObj.source
        __activeSource.play(nextItem.mediaObj.mid)

    else:
        log.msg("Queue Is Empty")
        #TODO: Radio

def getQueuedItems():
    return __queue.getQueuedItems()

def getPlayedItems():
    return __queue.getPlayedItems()

def updateStatus(status, text):
    log.msg("Status %s: %s" %(status, text))
    if status == States.STOP:
        __activeSource = None
        play()

def getStatus():
    if __activeSource:
        return __activeSource.status()
    
if not __initalized:
    log.msg("Initalizing GrooveBot")
    __initalized = True
    
    log.msg("Loading GrooveBot Plugins")
    # Import Sources
    for f in os.listdir(os.path.join(os.path.dirname(__file__), "plugins")):
        module_name, ext = os.path.splitext(f)
        if module_name != "__init__" and ext == '.py':
            log.msg('importing Plugin: %s' % module_name)
            __import__("groovebot.plugins." + module_name)
    
    # Create the imported Media Sources and register with GrooveBot
    for plugin in MediaSource.plugins:
        registerSource(plugin.__name__, plugin)
    
    # Create the imported Media Controllers and register with GrooveBot
    for plugin in MediaController.plugins:
        registerController(plugin.__name__, plugin)
                
    log.msg("GrooveBot Plugins Loaded")

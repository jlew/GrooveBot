# Import twisted libraries
from twisted.internet.defer import DeferredList
from twisted.internet.threads import deferToThread
from twisted.python import log

# Import GrooveBot Classes
from groovebot.ActionType import MediaSource, MediaController
from groovebot.Constants import States, QueueActions

from groovebot.db import Queue, Session
import os

__runningPlugins = {}
__mediaSources = {}
__controllers = {}
__activeSource = None
__activeQueue = None
__initalized = False

def registerSource(sourceId, sourceObj):
    global __runningPlugins
    log.msg("Registering Source: %s" % sourceId)
    if sourceId in __runningPlugins:
        __mediaSources[sourceId] = __runningPlugins[sourceId]
    else:
        log.msg("Creating new instance of plugin")
        p = sourceObj()
        __runningPlugins[sourceId] = p
        __mediaSources[sourceId] = p

def registerController(controllerId, controllerObj):
    global __runningPlugins
    log.msg("Registering Controller: %s" % controllerId)
    if controllerId in __runningPlugins:
        __controllers[controllerId] = __runningPlugins[controllerId]
    else:
        log.msg("Creating new instance of plugin")
        p = controllerObj()
        __runningPlugins[controllerId] = p
        __controllers[controllerId] = p

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
    log.msg("Searching: %s" % text)

    # Fire off search in parallel
    for key, mediasrc in __mediaSources.items():
        log.msg("\tSending Search Request to %s" % key)
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
            log.msg("\tSending Result to %s" % key)
            mediactr.searchCompleted(search_context, master_result)

    dl.addCallback(sendResults)

def queue(mediaObj):
    log.msg("Queueing %s" % mediaObj)
    
    qob = Queue(mediaObj)
    session = Session()
    session.add(qob)
    session.commit()
    
    if not __activeSource:
        play()
    else:
        for key, mediactr in __controllers.items():
            log.msg("\tSending Queue Change to %s" % key)
            mediactr.queueUpdated(QueueActions.ADD, qob)

def pause():
    if __activeSource:
        __activeSource.pause()

def resume():
    if __activeSource:
        __activeSource.resume()

def skip():
    if __activeSource:
        __activeSource.stop()
        #__activeSource = None
        #play()

def play():
    global __activeSource
    global __activeQueue
    
    session = Session()
    nextItem = session.query(Queue).filter(Queue.play_date==None).order_by(Queue.queue_date).first()
    
    if nextItem:
        log.msg("Playing %s" % nextItem.media_object)
        __activeSource = __runningPlugins[str(nextItem.media_object.source)]
        __activeQueue = nextItem
        nextItem.setPlayed()
        __activeSource.play(nextItem.media_object)
        session.commit()
        
        for key, mediactr in __controllers.items():
            log.msg("\tSending Queue Change to %s" % key)
        mediactr.queueUpdated(QueueActions.PLAY, __activeQueue)

    else:
        log.msg("Queue Is Empty")
        #TODO: Radio

def getQueuedItems():
    return Session().query(Queue).filter(Queue.play_date==None).order_by(Queue.queue_date)

def getPlayedItems():
    return Session().query(Queue).filter(Queue.play_date!=None).order_by(Queue.queue_date)

def remQueuedItem(remId):
    mysession = Session()
    item = mysession.query(Queue).filter(Queue.id==remId, Queue.play_date==None).first()
    
    if item:
        mysession.delete(item)
        mysession.commit()

        for key, mediactr in __controllers.items():
            log.msg("\tSending Queue Change to %s" % key)
            mediactr.queueUpdated(QueueActions.REMOVE, item.media_object)
        return True
            
    return False

def updateStatus(status, text, mediaObject=None):
    global _activeSource
    global _activeQueue
    log.msg("Status %s: %s" %(status, text))
    if status == States.STOP:
        __activeSource = None
        __activeQueue = None
        play()

    for key, mediactr in __controllers.items():
        log.msg("\tSending Status Update to %s" % key)
        mediactr.statusUpdate(status, text, mediaObject)

def getStatus():
    if __activeSource:
        return __activeQueue, __activeSource.status()
    else:
        return None, (States.STOP, "")
    
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
        registerSource(plugin.__module__, plugin)
    
    # Create the imported Media Controllers and register with GrooveBot
    for plugin in MediaController.plugins:
        registerController(plugin.__module__, plugin)
                
    log.msg("GrooveBot Plugins Loaded")
    play()

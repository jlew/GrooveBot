# Import twisted libraries
from twisted.internet.defer import DeferredList
from twisted.internet import reactor
from twisted.internet.threads import deferToThread
from twisted.python import log as logger

# Import GrooveBot Classes
from groovebot.PluginFramework import MediaController, MediaSource, RadioSource
from groovebot.Constants import States, QueueActions, SearchKeys

from groovebot.db import Queue, Session

from ConfigParser import ConfigParser
import os

CONFIG_FILE_NAME = "gb.ini"
__config = ConfigParser(allow_no_value=True)
__runningPlugins = {}
__activeSource = None
__activeQueue = None
__initalized = False

def getLogger(systemName):
    def lg(msg):
        logger.msg(msg, system=systemName)
    return lg

__log = getLogger("GrooveBot Core")

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
    __log("Searching: %s" % text)

    if not isinstance(text, dict) :
        
        artistStart = text.find(SearchKeys.ARTIST)
        titleStart = text.find(SearchKeys.TITLE)
        albumStart = text.find(SearchKeys.ALBUM)

        if max(artistStart, titleStart, albumStart) != -1:
            d = dict()
            
            def pullout(text2):
                if text2.find(SearchKeys.ARTIST) != -1:
                    text2 = text2[0:text2.find(SearchKeys.ARTIST)]

                if text2.find(SearchKeys.ALBUM) != -1:
                    text2 = text2[0:text2.find(SearchKeys.ALBUM)]

                if text2.find(SearchKeys.TITLE) != -1:
                    text2 = text2[0:text2.find(SearchKeys.TITLE)]
                return text2.strip()

            if artistStart != -1:
                d['artist'] = pullout(text[artistStart+len(SearchKeys.ARTIST) : len(text)])

            if titleStart != -1:
                d['title'] = pullout(text[titleStart+len(SearchKeys.TITLE) : len(text)])
                
            if albumStart != -1:
                d['album'] = pullout(text[albumStart+len(SearchKeys.ALBUM) : len(text)])
            __log("Parsed Search: " + str(d))
            text = d

    # Fire off search in parallel
    for mediasrc in MediaSource.plugins:
        if mediasrc.__module__ in __runningPlugins:
            __log("\tSending Search Request to %s" % mediasrc.__module__)
            searches.append(deferToThread(__runningPlugins[mediasrc.__module__].search, text))

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
        __log("Search Returned from all sources")
        master_result = []
        for status, result in results:
            if status:
                master_result += result

        for mediactr in MediaController.plugins:
            if mediactr.__module__ in __runningPlugins:
                __log("\tSending Result to %s" % mediactr.__module__)
                __runningPlugins[mediactr.__module__].searchCompleted(search_context, master_result)

    dl.addCallback(sendResults)

def queue(mediaObj):
    __log("Queueing %s" % mediaObj)
    
    session = Session()
    inQueue = session.query(Queue).filter(Queue.media_object==mediaObj).filter(Queue.play_date==None).first()

    if not inQueue:
        qob = Queue(mediaObj)
        session.add(qob)
        session.commit()
    
        if not __activeSource:
            play()
        else:
            for mediactr in MediaController.plugins:
                if mediactr.__module__ in __runningPlugins:
                    __log("\tSending Queue Change to %s" % mediactr.__module__)
                    __runningPlugins[mediactr.__module__].queueUpdated(QueueActions.ADD, qob)
        return True
    else:
        return False

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
        __log("Playing %s" % nextItem.media_object)
        __activeSource = __runningPlugins[str(nextItem.media_object.source)]
        __activeQueue = nextItem
        nextItem.setPlayed()
        __activeSource.play(nextItem.media_object)
        session.commit()
        
        for mediactr in MediaController.plugins:
            if mediactr.__module__ in __runningPlugins:
                __log("\tSending Queue Change to %s" % mediactr.__module__)
                __runningPlugins[mediactr.__module__].queueUpdated(QueueActions.PLAY, __activeQueue)

    else:
        __log("Queue Is Empty")
        #TODO: Radio

def getQueuedItems():
    return Session().query(Queue).filter(Queue.play_date==None).order_by(Queue.queue_date)

def getPlayedItems():
    return Session().query(Queue).filter(Queue.play_date!=None).order_by(Queue.queue_date)

def remQueuedItem(remId):
    mysession = Session()
    item = mysession.query(Queue).filter(Queue.media_object_id==remId, Queue.play_date==None).first()
    
    if item:
        mysession.delete(item)
        mysession.commit()
        
        for mediactr in MediaController.plugins:
            if mediactr.__module__ in __runningPlugins:
                __log("\tSending Queue Change to %s" % mediactr.__module__)
                __runningPlugins[mediactr.__module__].queueUpdated(QueueActions.REMOVE, item)
        return True
            
    return False

def updateStatus(status, text, mediaObject=None):
    global __activeSource
    global __activeQueue
    __log("Status %s: %s" %(status, text))

    for mediactr in MediaController.plugins:
        if mediactr.__module__ in __runningPlugins:
            __log("\tSending Status Update to %s" % mediactr.__module__)
            __runningPlugins[mediactr.__module__].statusUpdate(status, text, mediaObject)
        
    if status == States.STOP:
        __activeSource = None
        __activeQueue = None
        play()


def getStatus():
    if __activeSource:
        return __activeQueue, __activeSource.status()
    else:
        return None, (States.STOP, "")

def setConfig(plugin, key, value):
    __log("Setting config for %s: [%s] %s" % (plugin, key, value))

    __config.set(plugin, key, value)

    if __runningPlugins.has_key(plugin):
        __runningPlugins[plugin].configuration_change(key, value)
    

def flushConfig():
    __log("Flushing Config")
    with open(CONFIG_FILE_NAME, 'wb') as configfile:
        __config.write(configfile)

if not __initalized:
    __log("Initalizing GrooveBot")
    __log("Reading Config File")

    __config.read(CONFIG_FILE_NAME)
    
    __initalized = True
    
    __log("Loading GrooveBot Plugins")
    # Import Sources
    for f in os.listdir(os.path.join(os.path.dirname(__file__), "plugins")):
        module_name, ext = os.path.splitext(f)
        if module_name != "__init__" and\
            (ext == '.py' or os.path.isdir(os.path.join(os.path.dirname(__file__), "plugins", f))):
            __log('importing Plugin: %s' % module_name)
            __import__("groovebot.plugins." + module_name)
            
    
    # Create the imported Plugins and register with GrooveBot Framework
    for plugin in set(MediaController.plugins + MediaSource.plugins + RadioSource.plugins):
        __log("Starting Plugin %s" % plugin.__module__)

        # Create plugin section if not exist
        if not __config.has_section(plugin.__module__):
            __config.add_section(plugin.__module__)

        plugin_cfg = dict(__config.items(plugin.__module__))
        __log("Plugin Config: %s" % plugin_cfg)

        if plugin_cfg.get("plugin_disabled", False) != "True":
            __log("Initalizing Plugin %s" % plugin.__module__)
            __runningPlugins[plugin.__module__] = plugin(plugin_cfg)
        else:
            __log("Plugin Disabled")
                
    __log("GrooveBot Plugins Loaded")
    play()

    reactor.addSystemEventTrigger("before", "shutdown", flushConfig)

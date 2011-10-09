# Import twisted libraries
from twisted.internet.defer import DeferredList
from twisted.internet.threads import deferToThread
from twisted.python import log

# Import GrooveBot Classes
from groovebot.MediaSource import MediaSource
from groovebot.Queue import QueueContainer#, QueueObject
from groovebot.MediaController import MediaController

import os

class GrooveBot(object):
    _instance = None
    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(GrooveBot, cls).__new__(cls, *args, **kwargs)
        return cls._instance

    def __init__(self):
        self.__mediaSources = {}
        self.__controllers = {}
        self.__activeSource = None
        self.__queue = QueueContainer()

        # Import Sources
        for f in os.listdir(os.path.join(os.path.dirname(__file__), "plugins")):
            module_name, ext = os.path.splitext(f)
            if module_name != "__init__" and ext == '.py':
                log.msg('importing Plugin: %s' % module_name)
                __import__("groovebot.plugins." + module_name)

        # Create the imported Media Sources and register with GrooveBot
        for plugin in MediaSource.plugins:
            self.registerSource(plugin.__name__, plugin())

        # Create the imported Media Controllers and register with GrooveBot
        for plugin in MediaController.plugins:
            self.registerController(plugin.__name__, plugin())


    def registerSource(self, sourceId, sourceObj):
        log.msg("Registering Source: %s" % sourceId)
        self.__mediaSources[sourceId] = sourceObj

    def registerController(self, controllerId, controllerObj):
        log.msg("Registering Controller: %s" % controllerId)
        self.__controllers[controllerId] = controllerObj

    def initiateSearch(self, search_context, text):
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
        for key, mediasrc in self.__mediaSources.items():
            log.msg("\t%s:\t %s" % (key, text))
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
            master_result = []
            for status, result in results:
                if status:
                    master_result += result

            log.msg("Combined Results: %s" % master_result)
            for key, mediactr in self.__controllers.items():
                log.msg("\tSending Result to %s" % key)
                mediactr.searchCompleted(search_context, master_result)

        dl.addCallback(sendResults)

    def queue(self, queueObj):
        self.__queue.add(queueObj)

    def pause(self):
        pass

    def resume(self):
        pass

    def stop(self):
        pass

    def play(self):
        pass

    def getQueuedItems(self):
        return self.__queue.getQueuedItems()

    def getPlayedItems(self):
        return self.__queue.getPlayedItems()


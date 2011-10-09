# Import twisted libraries
from twisted.internet.defer import DeferredList
from twisted.internet.threads import deferToThread
from twisted.internet import reactor
from twisted.python import log

# Import GrooveBot Classes
from MediaSource import MediaSource
from Queue import QueueContainer#, QueueObject
from MediaController import MediaController

import os, sys
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
        self.__Queue = QueueContainer()

        # Import Sources
        for f in os.listdir(os.path.abspath("plugins/")):
            module_name, ext = os.path.splitext(f)
            if module_name != "__init__" and ext == '.py':
                log.msg('importing Plugin: %s' % module_name)
                __import__("plugins." + module_name)

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

    def initiateSearch(self, text):
        searches = []
        log.msg("Searching: %s" % text)

        # Fire off search in parallel
        for key, mediasrc in self.__mediaSources.items():
            log.msg("\t%s:\t %s" % (key, text))
            searches.append(deferToThread(mediasrc.search, text))

        # When all searches return, send result lists to all the
        # media controllers
        dl = DeferredList(searches)

        def sendResults(results):
            master_result = []
            for status, result in results:
                if status:
                    master_result += result

            log.msg("Combined Results: %s" % master_result)
            for key, mediactr in self.__controllers.items():
                log.msg("\tSending Result to %s" % key)
                mediactr.searchCompleted(master_result)

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

if __name__ == "__main__":
    #log.startLogging(open('log.txt', 'w'))
    log.startLogging(sys.stdout)

    g = GrooveBot()
    reactor.callLater(2, g.initiateSearch, "TEST")
    reactor.run()

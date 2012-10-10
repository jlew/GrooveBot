from groovebot.PluginFramework import MediaController
from groovebot.GrooveBot import queue, initiateSearch, getStatus, getQueuedItems, pause, resume, skip, remQueuedItem
from groovebot.SearchContext import SearchContext
from groovebot.db import Session, MediaObject
from groovebot.plugins.IrcController.JlewBot import JlewBot, JlewBotFactory
from groovebot.Constants import QueueActions
from groovebot.GrooveBot import setConfig, getLogger

from twisted.internet import reactor

import ConfigParser
import os

log = getLogger("Plugin: Irc Controller")

SEARCH = "search"
ADD = "add"
REMOVE = "remove"
PAUSE = "pause"
RESUME = "resume"
SKIP = "skip"
STATUS = "status"
DUMP = "dump"


class IrcControllerProtocol(JlewBot):
    def setup(self, f):
        #f.register_command('vol', self.volume_change)

        for command in [SEARCH, ADD, REMOVE, PAUSE, RESUME, SKIP, STATUS, DUMP]:
            f.register_command(command, self.cmd)

    def cmd(self, responder, user, channel, command, msg):
        if command == PAUSE:
            pause()
            responder("ok")
            
        elif command == RESUME:
            resume()
            responder("ok")

        elif command == SKIP:
            skip()
            responder("ok")

        elif command == STATUS:
            queueObj, statusLookup = getStatus()
            if queueObj:
                title = str(queueObj.media_object)
            else:
                title = ""
        
            if statusLookup:
                status, stat_text = statusLookup
            else:
                status = "IDLE"
                stat_text="Waiting for Activity"

            responder(("%s %s: %s" % (status, stat_text, title)).encode("UTF-8"));

        elif command == DUMP:
            qitems = [x for x in getQueuedItems()]
            if qitems:
                responder("%d item(s) in the queue" % len(qitems))
                for item in qitems:
                    msg = "%i: %s" % (item.media_object.id, item.media_object)
                    responder(msg.encode("UTF-8"))

        elif command == REMOVE:
            if remQueuedItem(int(msg)):
                responder("ok")
            else:
                responder("Failed to remove")

        elif command == SEARCH:
            s = SearchContext(self)
            s.responder = responder
            initiateSearch(s, msg)

        elif command == ADD:
            try:
                dbId = int(msg)
            except:
                responder("Expecting Resource Id")
                return
                
            item = Session().query(MediaObject).filter(MediaObject.id==dbId).first()
            if item:
                if queue(item):
                    responder("ok")
                else:
                    responder("Already in Queue")
            else:
                responder("Not found")

    

class IrcController(MediaController):

    def __init__(self, config):
        super(MediaController, self).__init__(config)

        self.bot_name = config.get("name", "GrooveBot")
        self.bot_channel = config.get("channel", "#GrooveBot")
        self.bot_server = config.get("server", "irc.freenode.net")
        self.bot_port = config.get("port", "6667")
        self.bot_flood_rate = config.get("flood_rate", "0.5")
        
        if len(config) == 0:
            setConfig(self.__module__, "name", self.bot_name)
            setConfig(self.__module__, "channel", self.bot_channel)
            setConfig(self.__module__, "server", self.bot_server)
            setConfig(self.__module__, "port", self.bot_port)
            setConfig(self.__module__, "flood_rate", self.bot_flood_rate)
        
       
    def start_irc(self):
        log("Setting IRC Connection")
         # create factory protocol and application
        self.factory = JlewBotFactory(protocol=IrcControllerProtocol,
            bot_name=self.bot_name, channel=self.bot_channel, line_rate=self.bot_flood_rate)

        # connect factory to this host and port
        self.reactor_connection = reactor.connectTCP(self.bot_server, int(self.bot_port), self.factory)


    def configuration_change(self, key, value):
        log( "Reconfiguration Requested: [%s] %s" % (key, value))
        if key == "name":
            self.bot_name = value

        elif key == "channel":
            self.bot_channel = value

        elif key == "server":
            self.bot_server = value

        elif key == "port":
            self.bot_port = value

        elif key == "flood_rate":
            self.bot_flod_rate = value

        else:
            log("Unsupported Config")
            return
        
        self.reactor_connection.disconnect().addCallback(self.start_irc)

    def searchCompleted(self, context, search_results):
        l = len(search_results)
        context.responder("Found %d matches" % l)
        for i, media_item in enumerate(search_results):
            msg  = "%d: \"%s\" by \"%s\" on \"%s\"." % \
                (media_item.id, media_item.title, media_item.artist, media_item.album)
            context.responder(msg.encode("UTF-8"))
            if i == 10:
                if l > 10:
                    context.responder("...")
                break;


    def queueUpdated(self, action, queueObject):
        if action == QueueActions.PLAY:
            return
            
        msg = "Queue %s: %s" % (action,queueObject.media_object)
        if self.factory.active_bot:
            self.factory.active_bot.me(self.factory.channel, msg.encode("UTF-8"))
        else:
            log("NO ACTIVE BOT")

    def statusUpdate(self, status, text, mediaObject):
        if mediaObject:
            msg = "%s %s" % (status, mediaObject)
        else:
            msg = "%s %s" % (status, text)
            
        if self.factory.active_bot:
            self.factory.active_bot.me(self.factory.channel, msg.encode("UTF-8"))
        else:
            log("NO ACTIVE BOT")










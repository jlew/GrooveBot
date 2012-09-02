from groovebot.ActionType import MediaController
from groovebot.GrooveBot import queue, initiateSearch, getStatus, getQueuedItems, pause, resume, skip, remQueuedItem
from groovebot.SearchContext import SearchContext
from groovebot.db import Session, MediaObject
from groovebot.plugins.IrcController.JlewBot import JlewBot, JlewBotFactory

from twisted.internet import reactor

import ConfigParser
import os

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
                    msg = "%i: %s" % (item.id, item.media_object)
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
                queue(item)
                responder("ok")
            else:
                responder("Not found")

    

class IrcController(MediaController):

    def __init__(self):
        config = ConfigParser.ConfigParser()
        config.read(os.path.join(os.path.dirname(__file__),'config.ini'))

        bot_name = config.get("BotConfig", "name")
        bot_channel = config.get("BotConfig", "channel")
        
        # create factory protocol and application
        self.factory = JlewBotFactory(protocol=IrcControllerProtocol, bot_name=bot_name, channel=bot_channel)

        # connect factory to this host and port
        reactor.connectTCP(config.get("BotConfig", "server"), config.getint("BotConfig", "port"), self.factory)
        

    def searchCompleted(self, context, search_results):
        l = len(search_results)
        if l > 0:
            context.responder("Found %d matches" % l)
            for i, media_item in enumerate(search_results):
                msg  = "%d: \"%s\" by \"%s\" on \"%s\"." % \
                    (media_item.id, media_item.title, media_item.artist, media_item.album)
                context.responder(msg.encode("UTF-8"))
                if i == 10:
                    if l > 10:
                        context.responder("...")
                    break;
        else:
            context.responder("No results found")

    def queueUpdated(self, action, queueObject):
        msg = "Queue %s: %s" % (action,queueObject)
        if self.factory.active_bot:
            self.factory.active_bot.me(self.factory.channel, msg.encode("UTF-8"))
        else:
            print "NO ACTIVE BOT"

    def statusUpdate(self, status, text, mediaObject):
        if mediaObject:
            msg = "%s %s %s" % (status, text, mediaObject)
        else:
            msg = "%s %s" % (status, text)
            
        if self.factory.active_bot:
            self.factory.active_bot.me(self.factory.channel, msg.encode("UTF-8"))
        else:
            print "NO ACTIVE BOT"










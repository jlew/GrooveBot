from groovebot.ActionType import MediaController
from groovebot.GrooveBot import queue, initiateSearch, getStatus, getQueuedItems, pause, resume, skip, remQueuedItem
from groovebot.SearchContext import SearchContext

from twisted.words.protocols.irc import IRCClient
from twisted.internet.protocol import ReconnectingClientFactory
from twisted.internet import reactor

class JlewBot(IRCClient):
    bot_name = "JlewBot"
    channel = "#jlew-test"
    versionNum = 1
    sourceURL = "http://gitorious.com/~jlew"
    lineRate = .25

    def signedOn(self):
        """Called when bot has succesfully signed on to server."""
        self.join(self.factory.channel)
        self.factory.add_bot(self)

    def joined(self, channel):
        """This will get called when the bot joins the channel."""
        print "Joined %s" % channel

    def left(self, channel):
        """This will get called when the bot leaves the channel."""
        print "Left %s" % channel

    def privmsg(self, user, channel, msg):
        """This will get called when the bot receives a message."""
        user = user.split('!', 1)[0]

        # Check to see if they're sending me a private message
        if channel == self.nickname:
            responder = lambda x: self.msg(user, x, length=400)
            msg = msg.split(" ", 1)
            if len(msg) == 1:
                self.factory.handle_command(responder, user, channel, msg[0], "")
            elif len(msg) == 2:
                self.factory.handle_command(responder, user, channel, msg[0], msg[1])

        # Message said in channel to the bot
        elif msg.startswith(self.nickname):
            responder = lambda x: self.msg(channel, "%s: %s" % (user, x))
            msg = msg.split(" ", 2)
            if len(msg) == 2:
                self.factory.handle_command(responder, user, channel, msg[1], "")
            elif len(msg) == 3:
                self.factory.handle_command(responder, user, channel, msg[1], msg[2])


class JlewBotFactory(ReconnectingClientFactory):
    protocol = JlewBot
    active_bot = None

    def __init__(self, protocol=protocol):
        self.protocol = protocol
        self.channel = protocol.channel
        self.registered_commands = {}
        self.default_cmd_handler = self.__default_cmd
        IRCClient.nickname = protocol.bot_name
        IRCClient.realname = protocol.bot_name

    def add_bot(self, bot):
        self.active_bot = bot

    def register_command(self, key, func):
        self.registered_commands[key] = func

    def handle_command(self, responder, user, channel, command, msg):
        cb = self.registered_commands.get(command, self.default_cmd_handler)
        cb(responder, user, channel, command, msg)

    def __default_cmd(self, responder, user, channel, command, msg):
        if command == "help":
            responder("Available Commands: %s" % ', '.join(self.registered_commands.keys()))

        else:
            responder("Command not recognized")

class IrcControllerProtocol(JlewBot):
    bot_name = "Groovebot2"
    channel = "#groove"
    def setup(self, f):
        #f.register_command('vol', self.volume_change)
        #reactor.callWhenRunning(self._set_vol)
        #for command in ['add','remove','show','pause','resume','skip','status','dump','radio']:
        #    f.register_command(command, self.request_queue_song)
        pass

    

class IrcController(MediaController):
    

    def __init__(self):
        # create factory protocol and application
        self.factory = JlewBotFactory(protocol=IrcControllerProtocol)

        for command in ['add','remove','show','pause','resume','skip','status','dump','radio']:
            self.factory.register_command(command, self.cmd)

        # connect factory to this host and port
        reactor.connectTCP("tron", 6667, self.factory)


    def cmd(self, responder, user, channel, command, msg):
        #'add','remove','show',,'skip','status','dump','radio'
        if command == "pause":
            pause()
            responder("ok")
            
        elif command == "resume":
            resume()
            responder("ok")

        elif command == "skip":
            skip()
            responder("ok")

        elif command == "status":
            queue, statusLookup = getStatus()
            if queue:
                title = str(queue.media_object)
            else:
                title = ""
        
            if statusLookup:
                status, stat_text = statusLookup
            else:
                status = "IDLE"
                stat_text="Waiting for Activity"

            responder(("%s %s: %s" % (status, stat_text, title)).encode("UTF-8"));

        elif command == "dump":
            qitems = [x for x in getQueuedItems()]
            if qitems:
                responder("%d item(s) in the queue" % len(qitems))
                for item in qitems:
                    msg = "%i: %s" % (item.id, item.media_object)
                    responder(msg.encode("UTF-8"))

        elif command == "remove":
            if remQueuedItem(int(msg)):
                responder("ok")
            else:
                responder("Failed to remove")

        elif command == "add":
            s = SearchContext(self)
            s.responder = responder
            initiateSearch(s, msg)
                
        

    def searchCompleted(self, context, search_results):
        l = len(search_results)
        if l == 1:
            queue(search_results[0])
        elif l > 1:
            context.responder("Found %d matches" % l)
            for i, media_item in enumerate(search_results):
                msg  = "\"%s\" by \"%s\" on \"%s\"." % \
                    (media_item.title, media_item.artist, media_item.album)
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










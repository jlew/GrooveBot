from twisted.words.protocols.irc import IRCClient
from twisted.internet.protocol import ReconnectingClientFactory
import ConfigParser

class JlewBot(IRCClient):
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

    def __init__(self, protocol=protocol, bot_name="JlewBot", channel="#jlewbot"):
        self.protocol = protocol
        self.channel = channel
        self.registered_commands = {}
        self.default_cmd_handler = self.__default_cmd
        IRCClient.nickname = bot_name
        IRCClient.realname = bot_name

    def buildProtocol(self, address):
        """
        Calls the setup method of the protocal, passing in an instance
        of the factory
        """
        p = ReconnectingClientFactory.buildProtocol(self, address)
        p.setup(self)
        return p

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

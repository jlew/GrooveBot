from groovebot.PluginFramework import MediaSource
from groovebot.GrooveBot import setConfig

class DummySource(MediaSource):

    def __init__(self, config):
        super(MediaSource, self).__init__(config)
        if(len(config) == 0):
            setConfig(self.__module__, 'TEST_CONFIG', 'testval')
            setConfig(self.__module__, 'LIFE', 42)
    
    def search(self, text):
        return []

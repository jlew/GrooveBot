import sqlalchemy
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base


from sqlalchemy import Column, Integer, DateTime, ForeignKey, Unicode, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()
#engine = create_engine('sqlite:///:memory:', echo=True)
engine = create_engine('sqlite:///sqllite.db', echo=False,  connect_args={'check_same_thread':False},
                    poolclass=StaticPool)
Session = sessionmaker(bind=engine)

class MediaObject(Base):
    __tablename__ = "media"
    id = Column(Integer, primary_key=True)
    source = Column(Unicode, nullable=False, )
    source_id = Column(Unicode)
    title = Column(Unicode)
    artist = Column(Unicode)
    album = Column(Unicode)
    dateAdded = Column(DateTime, nullable=False)
    on_demand = Column(Boolean, default=True)
    valid = Column(Boolean, default=True)
    attributes = relationship("MediaObjectAttribute")
    
    def __init__(self, source, title, artist, album, source_id=None, on_demand=True):
        self.source = source
        self.title = title
        self.artist = artist
        self.album = album
        self.source_id = source_id
        self.dateAdded = datetime.now()
        self.on_demand = on_demand
        self.valid = True
        
    def setValidState(self, state):
        self.valid = state
        
    def __str__(self):
        return "%s by %s(%s)" % (self.title, self.artist, self.album)
                
        
class MediaObjectAttribute(Base):
    __tablename__ = "media_attribute"
    id = Column(Integer, primary_key = True)
    parent = Column(Integer, ForeignKey("media.id"))
    key = Column(Unicode)
    value = Column(Unicode)
    
    def __init__(self, parent, key, value):
        self.parent = parent
        self.key = key
        self.value = value

class User(Base):
    __tablename__ = "user"
    id = Column(Integer, primary_key=True)
    username = Column(Unicode, unique=True)
    createDate = Column(DateTime, nullable=False)
    
    def __init__(self, userName):
        self.createDate = datetime.now()
        self.username = userName
        

class Queue(Base):
    __tablename__ = "queue"
    id = Column(Integer, primary_key=True)
    queue_date = Column(DateTime, nullable=False)
    play_date = Column(DateTime)
    media_object_id = Column(Integer, ForeignKey("media.id"))
    media_object = relationship("MediaObject")
    user = Column(Integer, ForeignKey("user.id"))
    
    def __init__(self, mediaObject):
        self.queue_date = datetime.now()
        self.media_object_id = mediaObject.id
        
    def setPlayed(self):
        self.play_date = datetime.now()
        
    def __str__(self):
        return "%s - %s" % (self.queue_date.strftime('%I:%M'), self.media_object)
        
Base.metadata.create_all(engine)
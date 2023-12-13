from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text, ForeignKey
from sqlalchemy.orm import sessionmaker, relationship, backref
from sqlalchemy.ext.declarative import declarative_base
import datetime
import pandas as pd 
import random

# Define the base model
Base = declarative_base()

class Text(Base):
    __tablename__ = 'text'
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String)
    text_content = Column(Text)
    created_at = Column(DateTime, default=datetime.datetime.now())
    updated_at = Column(DateTime, default=datetime.datetime.now(), onupdate=datetime.datetime.now())

class Photo(Base):
    __tablename__ = 'photo'
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String)
    photo_url = Column(String)
    photo_description = Column(String)
    created_at = Column(DateTime, default=datetime.datetime.now())
    updated_at = Column(DateTime, default=datetime.datetime.now(), onupdate=datetime.datetime.now())

class Audio(Base):
    __tablename__ = 'audio'
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String)
    text_id = Column(Integer, ForeignKey('text.id'), nullable=False)
    audio_url = Column(String)
    audio_text = Column(String)
    voice = Column(String)
    created_at = Column(DateTime, default=datetime.datetime.now())
    updated_at = Column(DateTime, default=datetime.datetime.now(), onupdate=datetime.datetime.now())
    text = relationship("Text", backref=backref("audios", lazy=True)) # Relationship back to Text

class Video(Base):
    __tablename__ = 'video'
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String)
    job_id = Column(String)
    created_at = Column(DateTime, default=datetime.datetime.now())
    audio_selection = Column(String)
    audio_row_id = Column(Integer)
    text_selection = Column(String)
    text_row_id = Column(Integer)
    photo_selection = Column(String)
    photo_row_id = Column(Integer)
    video_url = Column(String)

class Powerpoint(Base):
    __tablename__ = 'powerpoint'
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String)
    slide_title = Column(String)
    slide_body_text = Column(String)
    slide_video_url = Column(String)
    created_at = Column(DateTime, default=datetime.datetime.now())
    powerpoint_url = Column(String)

class Project(Base):
    __tablename__ = 'project'
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String)
    project_name = Column(String)
    project_description = Column(String)
    created_at = Column(DateTime, default=datetime.datetime.now())
    updated_at = Column(DateTime, default=datetime.datetime.now(), onupdate=datetime.datetime.now())

class ProjectMedia(Base):
    __tablename__ = 'project_media'
    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(Integer, ForeignKey('project.id'), nullable=False)
    
    project = relationship("Project", backref=backref("project_media", lazy=True)) # Relationship back to Project


# Create an engine that stores data in the local directory's sqlite file
engine = create_engine('sqlite://///Users/hantswilliams/Development/python/digitalclone-iitg/flask_app/dev.db')

# Function to initialize the database
def init_db():
    Base.metadata.create_all(engine)

# Function to get a new session
def get_session():
    return sessionmaker(bind=engine)()

# Create all tables in the engine
Base.metadata.create_all(engine)

# To use the models, create a session
Session = sessionmaker(bind=engine)



# #### Inserting FAKE data for testing 
# ### Create new dataframe with fake data, using random generator; 10 rows
# data = []
# for _ in range(10):
#     row = {
#         "user_id": random.choice(['mvp_001', 'mvp_002', 'mvp_003', 'mvp_004', 'mvp_005']),
#         "data_type": random.choice(['Text']),
#         "text_content": random.choice(["This is a sentance", "This is another sentance", "This is a third sentance", "This is a fourth sentance", "This is a fifth sentance"]),
#         "data_url": random.choice(["", "s3:audio:052", "", "s3:audio:234", "s3:audio:115"]),
#     }
#     data.append(row)
#     row = {
#         "user_id": random.choice(['mvp_001', 'mvp_002', 'mvp_003', 'mvp_004', 'mvp_005']),
#         "data_type": random.choice(['Photo']),
#         "text_content": random.choice(["Photo 1", "Photo 2", "Photo 3", "Photo 4", "Photo 5"]),
#         "data_url": random.choice(["", "s3:audio:052", "", "s3:audio:234", "s3:audio:115"]),
#     }
#     data.append(row)
    
# ## create a session and add the data
# session = Session()
# for row in data:
#     data_entry = DataEntry(
#         user_id=row['user_id'],
#         data_type=row['data_type'],
#         text_content=row['text_content'],
#         data_url=row['data_url'],
#     )
#     session.add(data_entry)
# session.commit()
# session.close()

# ## add new audio entry test
# session = get_session()
# data_entry = session.query(DataEntry).first()
# new_audio = Audio(audio_url='http://example.com/audio.mp3', data_entry=data_entry)
# session.add(new_audio)
# session.commit()


# # QUERYING
# ## Query using pd.read_sql
# query = 'SELECT * FROM data_entries'
# output = pd.read_sql(query, engine)
# print(output)

# ## Query using pd.read_sql for audio
# query = 'SELECT * FROM audio'
# output = pd.read_sql(query, engine)
# print(output)
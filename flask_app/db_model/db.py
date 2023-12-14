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
    projects = relationship("Project", secondary='project_text_association', back_populates="texts")
class Photo(Base):
    __tablename__ = 'photo'
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String)
    photo_url = Column(String)
    photo_description = Column(String)
    created_at = Column(DateTime, default=datetime.datetime.now())
    updated_at = Column(DateTime, default=datetime.datetime.now(), onupdate=datetime.datetime.now())
    projects = relationship("Project", secondary='project_photo_association', back_populates="photos")
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
    projects = relationship("Project", secondary='project_audio_association', back_populates="audios")
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
    projects = relationship("Project", secondary='project_video_association', back_populates="videos")
class Powerpoint(Base):
    __tablename__ = 'powerpoint'
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String)
    slide_title = Column(String)
    slide_body_text = Column(String)
    slide_video_url = Column(String)
    created_at = Column(DateTime, default=datetime.datetime.now())
    powerpoint_url = Column(String)
    projects = relationship("Project", secondary='project_powerpoint_association', back_populates="powerpoints")
class Project(Base):
    __tablename__ = 'project'
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String)
    project_name = Column(String)
    project_description = Column(String)
    created_at = Column(DateTime, default=datetime.datetime.now())
    updated_at = Column(DateTime, default=datetime.datetime.now(), onupdate=datetime.datetime.now())
    texts = relationship("Text", secondary='project_text_association', back_populates="projects")
    photos = relationship("Photo", secondary='project_photo_association', back_populates="projects")
    audios = relationship("Audio", secondary='project_audio_association', back_populates="projects")
    videos = relationship("Video", secondary='project_video_association', back_populates="projects")
    powerpoints = relationship("Powerpoint", secondary='project_powerpoint_association', back_populates="projects")

# Association Tables
class ProjectTextAssociation(Base):
    __tablename__ = 'project_text_association'
    project_id = Column(Integer, ForeignKey('project.id'), primary_key=True)
    text_id = Column(Integer, ForeignKey('text.id'), primary_key=True)
class ProjectPhotoAssociation(Base):
    __tablename__ = 'project_photo_association'
    project_id = Column(Integer, ForeignKey('project.id'), primary_key=True)
    photo_id = Column(Integer, ForeignKey('photo.id'), primary_key=True)
class ProjectAudioAssociation(Base):
    __tablename__ = 'project_audio_association'
    project_id = Column(Integer, ForeignKey('project.id'), primary_key=True)
    audio_id = Column(Integer, ForeignKey('audio.id'), primary_key=True)
class ProjectVideoAssociation(Base):
    __tablename__ = 'project_video_association'
    project_id = Column(Integer, ForeignKey('project.id'), primary_key=True)
    video_id = Column(Integer, ForeignKey('video.id'), primary_key=True)
class ProjectPowerpointAssociation(Base):
    __tablename__ = 'project_powerpoint_association'
    project_id = Column(Integer, ForeignKey('project.id'), primary_key=True)
    powerpoint_id = Column(Integer, ForeignKey('powerpoint.id'), primary_key=True)
    
# Create an engine that stores data in the local directory's sqlite file
engine = create_engine('sqlite://///Users/hantswilliams/Development/python/digitalclone-iitg/flask_app/dev.db')

# Function to initialize the database
def init_db():
    Base.metadata.create_all(engine)

# Function to get a new session
def get_session():
    return sessionmaker(bind=engine)()

# FUnction to close the session
def close_session(session):
    session.close()

# Function to get a new session, queries the Project table, and returns all projects
def get_projects():
    session = get_session()
    projects = session.query(Project).all()
    session.close()
    return projects

# Function to get a new session, takes in a project association type and a row id, and returns the associated data
def get_project_data_associations(association_type, row_id):
    """
    ## association_type: text, photo, audio, video, powerpoint
    """
    session = get_session()
    
    if association_type == 'text':
        ## get list of associated projects
        try:
            associated_projects = session.query(Project).join(ProjectTextAssociation, Project.id == ProjectTextAssociation.project_id).filter(ProjectTextAssociation.text_id == row_id).all()
            non_associated_projects = session.query(Project).filter(~Project.id.in_([project.id for project in associated_projects])).all()     ## get list of non-associated projects
        except Exception as e:
            return f'Error: {str(e)}'
    elif association_type == 'photo':
        ## get list of associated projects
        try:
            associated_projects = session.query(Project).join(ProjectPhotoAssociation, Project.id == ProjectPhotoAssociation.project_id).filter(ProjectPhotoAssociation.photo_id == row_id).all()
            non_associated_projects = session.query(Project).filter(~Project.id.in_([project.id for project in associated_projects])).all()
        except Exception as e:
            return f'Error: {str(e)}'
    elif association_type == 'audio':
        ## get list of associated projects
        try:
            associated_projects = session.query(Project).join(ProjectAudioAssociation, Project.id == ProjectAudioAssociation.project_id).filter(ProjectAudioAssociation.audio_id == row_id).all()
            non_associated_projects = session.query(Project).filter(~Project.id.in_([project.id for project in associated_projects])).all()
        except Exception as e:
            return f'Error: {str(e)}'
    elif association_type == 'video':
        ## get list of associated projects
        try:
            associated_projects = session.query(Project).join(ProjectVideoAssociation, Project.id == ProjectVideoAssociation.project_id).filter(ProjectVideoAssociation.video_id == row_id).all()
            non_associated_projects = session.query(Project).filter(~Project.id.in_([project.id for project in associated_projects])).all()
        except Exception as e:
            return f'Error: {str(e)}'
    elif association_type == 'powerpoint':
        ## get list of associated projects
        try:
            associated_projects = session.query(Project).join(ProjectPowerpointAssociation, Project.id == ProjectPowerpointAssociation.project_id).filter(ProjectPowerpointAssociation.powerpoint_id == row_id).all()
            non_associated_projects = session.query(Project).filter(~Project.id.in_([project.id for project in associated_projects])).all()
        except Exception as e:
            return f'Error: {str(e)}'
    else:
        return 'Error: Invalid association type'
    
        
    project_list_associated = []
    for project in associated_projects:
        project_list_associated.append({
            'project_id': project.id,
            'project_name': project.project_name,
            'project_description': project.project_description
        })
    
    project_list_non_associated = []
    for project in non_associated_projects:
        project_list_non_associated.append({
            'project_id': project.id,
            'project_name': project.project_name,
            'project_description': project.project_description
        })

    session.close()

    return project_list_associated, project_list_non_associated

## Function to update the project associations which takes in a association type and row id, and a list of project ids
def update_project_data_associations(association_type, row_id, project_ids):
    """
    # association_type: text, photo, audio, video, powerpoint
    # row_id: id of the data entry
    # project_ids: list of project ids
    """
    if association_type == 'text':
        association_table = ProjectTextAssociation
        association_table_id = association_table.text_id
    elif association_type == 'photo':
        association_table = ProjectPhotoAssociation
        association_table_id = association_table.photo_id
    elif association_type == 'audio':
        association_table = ProjectAudioAssociation
        association_table_id = association_table.audio_id
    elif association_type == 'video':
        association_table = ProjectVideoAssociation
        association_table_id = association_table.video_id
    elif association_type == 'powerpoint':
        association_table = ProjectPowerpointAssociation
        association_table_id = association_table.powerpoint_id

    session = get_session()

    ## delete all associations
    try:
        session.query(association_table).filter(association_table_id == row_id).delete()
        session.commit()
    except Exception as e:
        session.rollback()
        return f'Error: {str(e)}'
    
    ## add new associations
    try:
        for project_id in project_ids:
            new_association = association_table(project_id=project_id, **{association_table_id.key: row_id})
            session.add(new_association)
        session.commit()
    except Exception as e:
        session.rollback()
        return f'Error: {str(e)}'
    
    session.close()

    return 'Success'

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
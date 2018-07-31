from datetime import datetime
from sqlalchemy import Column, ForeignKey, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy import create_engine

Base = declarative_base()


class Organisation(Base):
    __tablename__ = 'organisation'
    id = Column(Integer, primary_key=True)

    name = Column(String(64))


class Document(Base):
    __tablename__ = 'document'
    id = Column(Integer, primary_key=True)

    author = Column(String(256))
    issue = Column(String(256))
    journal = Column(String(256))
    volume = Column(String(256))
    pub_year = Column(Integer)
    pagination = Column(String(256))
    title = Column(String(1024))
    file_hash = Column(String(32))

    id_organisation = Column(Integer, ForeignKey('organisation.id'))
    organisation = relationship(Organisation)

    datetime_creation = Column(DateTime)
    datetime_update = Column(DateTime, default=datetime.now())


class Reference(Base):
    __tablename__ = 'reference'
    id = Column(Integer, primary_key=True)

    publication_id = Column(String(256))
    cosine_similarity = Column(String(256))

    id_document = Column(Integer, ForeignKey('document.id'))
    document = relationship(Document)

    datetime_creation = Column(DateTime)
    datetime_update = Column(DateTime, default=datetime.now())


class DatabaseEngine():
    def get_session(url):
        engine = create_engine(url)
        Base.metadata.bind = engine
        DBSession = sessionmaker(bind=engine)
        return DBSession()

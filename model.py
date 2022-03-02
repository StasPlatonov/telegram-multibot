from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
import logging

logger = logging.getLogger(__name__)

Base = declarative_base()

# ----------------------------------------------------------------------------


class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    username = Column(String)
    name = Column(String)
    lastname = Column(String)
    language = Column(String)
    update_frequency = Column(Integer)

# ----------------------------------------------------------------------------


class Subscription(Base):
    __tablename__ = 'subscriptions'

    id = Column(Integer, primary_key=True)
    subscriber_id = Column(Integer, ForeignKey('users.id'))
    description = Column(String)

# ----------------------------------------------------------------------------


class ModelCreator:
    def __init__(self, engine, session_maker):
        try:
            #if not engine.dialect.has_table(engine, 'users'):
            #    print("Create model")
            #    Base.metadata.create_all(engine)

            with engine.connect() as connection:
                if not engine.dialect.has_table(connection, 'users'):
                    logger.info('Creating model...')
                    Base.metadata.create_all(engine)
        except Exception as e:
            logger.error("Failed to connect to database: " + str(e))
# ----------------------------------------------------------------------------

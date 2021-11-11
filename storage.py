from sqlalchemy import create_engine
from sqlalchemy import exc
from sqlalchemy.orm import sessionmaker
from model import ModelCreator, User
import messages as texts
import logging

# Enable logging
logging.basicConfig(
    format='%(asctime)s [%(thread)d] %(name)s[%(levelname)s]: %(message)s', level=logging.INFO
)

logger = logging.getLogger(__name__)

class SmartStorage(object):
    def __init__(self, url):
        self.URL = url
        self.engine = create_engine(self.URL)
        self.sessionMaker = sessionmaker(bind=self.engine)
        self.model = ModelCreator(self.engine, self.sessionMaker)

    # ----------------------------------------------------------------------------

    def add_user(self, userid, username, name, lastname):
        try:
            with self.engine.connect() as connection:
                session = self.sessionMaker(bind=connection)
                try:
                    user = User(id=userid, username=username, name=name, lastname=lastname, language=texts.LANG_EN,
                                update_frequency=0)

                    session.add(user)

                    session.commit()
                    logger.info(f'User subscribed: {user.id}, {user.name}')
                    return user
                except Exception as e:
                    logger.error("Failed to add user: " + str(e))
                    session.rollback()
                    raise
                finally:
                    session.close()

        except exc.SQLAlchemyError as e:
            logger.error("Failed to add user: " + str(e))

    # ----------------------------------------------------------------------------

    def get_default_user(self, userid):
        return User(id=userid, username='default', name='', lastname='', language=texts.LANG_EN,
                    update_frequency=0)

    # ----------------------------------------------------------------------------

    def get_user(self, userid):
        try:
            with self.engine.connect() as connection:
                session = self.sessionMaker(bind=connection)
                try:
                    query = session.query(User).filter(User.id == userid)
                    user = query.first()
                    return user

                except Exception as e:
                    logger.error("Failed to get user: " + str(e))
                    session.rollback()
                    return self.get_default_user(userid)
                finally:
                    session.close()

        except exc.SQLAlchemyError as e:
            logger.error("Failed to get user: " + str(e))
            return self.get_default_user(userid)

    # ----------------------------------------------------------------------------

    def update_user(self, userid, user):
        try:
            with self.engine.connect() as connection:
                session = self.sessionMaker(bind=connection)
                try:
                    logger.info(f"Updating user({userid}) settings")
                    cur_user = session.query(User).filter(User.id == userid).first()
                    cur_user.name = user.name
                    cur_user.lastname = user.lastname
                    cur_user.language = user.language
                    cur_user.update_frequency = user.update_frequency

                    session.commit()
                    logger.info(f"User ({userid}) updated")
                except Exception as e:
                    logger.error("Failed to update user: " + str(e))
                    session.rollback()
                    raise
                finally:
                    session.close()

        except exc.SQLAlchemyError as e:
            logger.error("Failed to update user: " + str(e))

    # ----------------------------------------------------------------------------

    def delete_user(self, userid):
        try:
            with self.engine.connect() as connection:
                session = self.sessionMaker(bind=connection)
                try:
                    # Remove user
                    session.query(User).filter_by(id=userid).delete()

                    session.commit()
                    logger.info(f'User deleted: {userid}')

                except Exception as e:
                    logger.error("Failed to delete user: " + str(e))
                    session.rollback()
                    raise
                finally:
                    session.close()

        except exc.SQLAlchemyError as e:
            logger.error("Failed to delete user: " + str(e))

    # ----------------------------------------------------------------------------

    def enum_users(self):
        try:
            with self.engine.connect() as connection:

                session = self.sessionMaker(bind=connection)
                try:
                    users = session.query(User).all()
                    return users

                except Exception as e:
                    logger.error("Failed to enum users: " + str(e))
                    raise
                finally:
                    session.close()

        except exc.SQLAlchemyError as e:
            logger.error("Failed to enum users: " + str(e))
            return []

    # ----------------------------------------------------------------------------


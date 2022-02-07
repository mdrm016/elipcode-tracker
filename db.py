from flask_sqlalchemy import SQLAlchemy

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import scoped_session, sessionmaker

db = SQLAlchemy()

DBSession = scoped_session(sessionmaker())
Base = declarative_base()


def initialize_sql(engine):
    DBSession.configure(bind=engine)
    Base.metadata.bind = engine

    # import hermes.model.db
    # hermes.model.db.Base.metadata.create_all(engine)

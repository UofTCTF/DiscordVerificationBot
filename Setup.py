import os
import sqlalchemy as db

if __name__ == "__main__":
    engine = db.create_engine(os.getenv("DATABASE_URL"))
    connection = engine.connect()
    metadata = db.MetaData()
    db.Table('Users', metadata,
             db.Column('id', db.String(255), nullable=False, unique=True),
             db.Column('email', db.String(255), nullable=True),
             db.Column('code', db.String(255), nullable=False))
    metadata.create_all(engine)

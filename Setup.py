import os
import sqlalchemy as db
from dotenv import load_dotenv

if __name__ == "__main__":
    load_dotenv()
    URI = os.getenv("DATABASE_URL")
    engine = db.create_engine(URI)
    connection = engine.connect()
    metadata = db.MetaData()
    db.Table('Users', metadata,
             db.Column('id', db.String(255), nullable=False, unique=True),
             db.Column('email', db.String(255), nullable=True),
             db.Column('code', db.String(255), nullable=False))
    metadata.create_all(engine)

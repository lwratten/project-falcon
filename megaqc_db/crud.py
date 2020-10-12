from sqlalchemy import create_engine, MetaData
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from config import *

### Base object maintains a catalog of classes/tables mapped to the database
### Also replaces all Column objects with python descriptors
Base = declarative_base()



engine = create_engine(DATABASE_URI, echo = True)
Session = sessionmaker(bind=engine)
session = Session()
Base.metadata.create_all(engine)
# recreate database
def recreate_database():
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)



from models import Base
from db_config import engine

Base.metadata.create_all(engine)
# Base.metadata.drop_all(engine)

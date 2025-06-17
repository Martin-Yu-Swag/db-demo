from sqlalchemy import create_engine

# fmt: off
HOST     = '127.0.0.1'
PORT     = 3306
DATABASE = 'db_demo'
USERNAME = 'admin'
PASSWORD = 'password'
ECHO     = True
# fmt: on

cnt_string = f"mysql+mysqldb://{USERNAME}:{PASSWORD}@{HOST}:{PORT}/{DATABASE}"
engine = create_engine(cnt_string, echo=ECHO, pool_recycle=3600)

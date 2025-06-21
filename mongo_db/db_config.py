from mongoengine import connect

HOST = "127.0.0.1"
PORT = 27017
DATABASE = "db_demo"
USERNAME = "admin"
PASSWORD = "password"


connect(host=HOST, port=PORT, db=DATABASE, username=USERNAME, PASSWORD=PASSWORD)

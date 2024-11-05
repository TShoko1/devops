from sqlalchemy import create_engine, Column, Integer, String, Boolean, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import datetime
import configparser

# Чтение конфигурации
config = configparser.ConfigParser()
config.read('config.ini')

# Получение URL базы данных из файла конфигурации
DATABASE_URL = config['database']['url']

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class Task(Base):
    __tablename__ = "tasks"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False)
    text = Column(String, nullable=False)
    completed = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

# Создание таблицы, если она еще не создана
Base.metadata.create_all(bind=engine)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

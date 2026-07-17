from backend.app.database import Base, engine
import backend.app.models
import logging

Base.metadata.create_all(bind=engine)

logging.info(">> Database schema initialized <<")
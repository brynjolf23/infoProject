from sqlalchemy import Column, String, Integer, DateTime
from sqlalchemy.sql import func
from app import db


class Entity():
    id = Column(Integer, primary_key=True, autoincrement="auto")
    date_created = Column(DateTime(), server_default=func.now())
    date_updated = Column(DateTime(), server_default=func.now())
    last_updated_by = Column(String)

    def __init__(self, created_by = 0):
        self.last_updated_by = created_by

    def toDict(self):
        return {
           'id': self.id,
            'date_created': str(self.date_created)  # TODO Convert to controlled date format
        }

    def toJSON(self):
        import json
        return json.dumps(self.toDict())
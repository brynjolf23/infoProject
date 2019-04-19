from sqlalchemy import Integer, Column, String, DateTime, Float
from sqlalchemy.sql import func
from sqlalchemy.event import listen
from sqlalchemy.ext.declarative import declarative_base
from app import db

class Anime(db.Model):
	__tablename__='anime'
	anime_id = Column(Integer, primary_key=True)
	name = Column(String(100))	
	genre = Column(String(200))
	anime_type = Column(String(10))
	episodes = Column(String(10))
	rating = Column(String(10))
	members = Column(String(10))
	date_created = Column(DateTime(), server_default=func.now())

	def fromCSV(self, csv_rec): #CSV format to Anime class
		if 'anime_id' in csv_rec:
			self.anime_id = csv_rec['anime_id']
		else:
			raise Exception('The anime_id field is required')
		self.name = csv_rec['name'] if 'name' in csv_rec else ''
		self.genre = csv_rec['genre'] if 'genre' in csv_rec else ''
		self.anime_type = csv_rec['anime_type'] if 'anime_type' in csv_rec else ''
		self.episodes = csv_rec['episodes'] if 'episodes' in csv_rec else ''
		self.rating = csv_rec['rating'] if 'rating' in csv_rec else ''
		self.members = csv_rec['members'] if 'members' in csv_rec else ''


def loadAnimeIntoTable(target, connection, **kw):
	import csv
	with open('anime.csv') as csvfile:
		reader = csv.DictReader(csvfile)
		for row in reader:
			a = Anime()
			a.fromCSV(row)
			db.session.add(a)
		db.session.commit()

listen(Anime.__table__, 'after_create', loadAnimeIntoTable) 
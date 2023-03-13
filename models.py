from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

#----------------------------------------------------------------------------#
# Models.
#----------------------------------------------------------------------------#

class Venue(db.Model):
    __tablename__ = 'Venue'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    address = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    genres =  db.Column(db.String(120))
    website = db.Column(db.String(120))
    seeking_talent = db.Column(db.Boolean)
    seeking_description = db.Column(db.String(1000))
    shows = db.relationship('Show', backref='venue', lazy='joined', cascade="all, delete")

    def update(self, d = None):
          if d is not None:
            genres = d.getlist('genres')
            self.genres = ','.join(genres)
            for key, value in d.items():
              if key != "genres":
                setattr(self, key, value)
  
    def __repr__(self):
      return f'<Venue ID: {self.id}, name: {self.name}, city: {self.city}>, state: {self.state}>,\
              address: {self.address}>, phone: {self.phone}>, image_link: {self.image_link}>,    \
              facebook_link: {self.facebook_link}>, genres: {self.genres}>,                      \
              website: {self.website}>, seeking_talent: {self.seeking_talent}>,                  \
              seeking_description: {self.seeking_description}>'

class Artist(db.Model):
    __tablename__ = 'Artist'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    genres =  db.Column(db.String(120))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    website = db.Column(db.String(120))
    seeking_venue = db.Column(db.Boolean)
    seeking_description = db.Column(db.String(1000))
    shows = db.relationship('Show', backref='artist', lazy='joined', cascade="all, delete")

    def update(self, d = None):
          if d is not None:
            genres = d.getlist('genres')
            self.genres = ','.join(genres)
            for key, value in d.items():
              if key != "genres":
                setattr(self, key, value)

    def __repr__(self):
      return f'<Artist ID: {self.id}, name: {self.name}, city: {self.city}>,                     \
              state: {self.state}>, genres: {self.genres}>, image_link: {self.image_link}>,      \
              facebook_link: {self.facebook_link}>'

class Show(db.Model):
    __tablename__ = 'Show'

    id = db.Column(db.Integer, primary_key=True)
    artist_id = db.Column(db.Integer, db.ForeignKey('Artist.id'), nullable=False)
    venue_id = db.Column(db.Integer, db.ForeignKey('Venue.id'), nullable=False)
    start_time = db.Column(db.TIMESTAMP)
    
    def __repr__(self):
      return f'<Show ID: {self.id}, artist_id: {self.artist_id}, venue_id: {self.venue_id},       \
              start_time: {self.start_time}>'

#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import json
import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for, jsonify, abort
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from forms import *
import os
import sys
from config import *
from flask_migrate import Migrate
#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
db = SQLAlchemy(app)

migrate = Migrate(app, db)

app.config['SQLALCHEMY_DATABASE_URI'] = SQLALCHEMY_DATABASE_URI
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

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
    shows = db.relationship('Show', backref='venue', lazy=True)

    def update(self, d = None):
          if d is not None:
            genres = request.form.getlist('genres')
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
    shows = db.relationship('Show', backref='artist', lazy=True)

    def update(self, d = None):
          if d is not None:
            genres = request.form.getlist('genres')
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

#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
  date = dateutil.parser.parse(value)
  if format == 'full':
      format="EEEE MMMM, d, y 'at' h:mma"
  elif format == 'medium':
      format="EE MM, dd, y h:mma"
  return babel.dates.format_datetime(date, format, locale='en')

app.jinja_env.filters['datetime'] = format_datetime

def specify_shows(shows, compare_operator = ">=", refDate = datetime.now()):
  output_shows = []

  if compare_operator != "<" and compare_operator != ">=":
    return render_template('errors/500.html', context="Compare operator should be \"<\" or \">=\"")

  for show in shows:
    show_start_time: datetime
    show_start_time = show.start_time
    if eval("show_start_time.strftime('%Y-%m-%d %H:%M:%S')" + compare_operator + "refDate.strftime('%Y-%m-%d %H:%M:%S')"):
      output_shows.append(show)

  return output_shows

def parse_show(show: Show, type: str, data_list):
  parsed_show = {}

  if type != "Venue" and type != "Artist":
    return render_template('errors/500.html', context="type should be \"Artist\" or \"Venue\"")

  if (type == "Venue"):
    obj = Venue.query.get(show.venue_id)
  else:
    obj = Artist.query.get(show.artist_id)

  for key in data_list:
    parsed_show[type.lower() + "_" + key] = eval("obj." + key)
  parsed_show['start_time'] = show.start_time.strftime('%Y-%m-%d %H:%M:%S')

  return parsed_show

def get_area_from_venue(v: Venue):
  area = {
    'city': v.city,
    'state': v.state,
    'venues':[{
      'id': v.id,
      'name': v.name,
      'num_upcoming_shows': len(specify_shows(v.shows))
    }]
  }
  return area

#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#

@app.route('/')
def index():
  return render_template('pages/home.html')


#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():
  venues = Venue.query.all()
  areasDic = [get_area_from_venue(venues[0])]
  for i in range(1, len(venues)):
    areaExited = False
    for area in areasDic:
      if area.get('city') == venues[i].city and area.get('state') == venues[i].state:
        areaExited = True
        break

    if areaExited == False:
      areasDic.append(get_area_from_venue(venues[i]))
    else:
      area['venues'].append({
        'id': venues[i].id,
        'name': venues[i].name,
        'num_upcoming_shows': len(specify_shows(venues[i].shows))
      })
  return render_template('pages/venues.html', areas=areasDic)

@app.route('/venues/search', methods=['POST'])
def search_venues():
  search_text = request.form.get('search_term', '')
  venues = Venue.query.filter(Venue.name.ilike('%' + search_text + '%')).all()
  response = {
    'count': len(venues),
    'data': []
  }

  result_count = len(venues)
  for i in range(0, result_count):
    response['data'].append({
      'id': venues[i].id,
      'name': venues[i].name,
      'num_upcoming_shows': len(specify_shows(venues[i].shows))
    })

  return render_template('pages/search_venues.html', results=response, search_term=search_text)

@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
  # shows the venue page with the given venue_id
  venue = Venue.query.get(venue_id)
  data = venue.__dict__
  data['genres'] = venue.genres.split(',')
  upcoming_shows = specify_shows(venue.shows)
  data['upcoming_shows'] = []
  for show in upcoming_shows:
    data['upcoming_shows'].append(parse_show(show, "Artist", ["id", "name", "image_link"]))
  data['upcoming_shows_count'] = len(upcoming_shows)

  past_shows = specify_shows(venue.shows, "<")
  data['past_shows'] = []
  for show in past_shows:
    data['past_shows'].append(parse_show(show, "Artist", ["id", "name", "image_link"]))
  data['past_shows_count'] = len(past_shows)

  return render_template('pages/show_venue.html', venue=data)

#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
  form = VenueForm()
  return render_template('forms/new_venue.html', form=form)

@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
  error = False
  errorMsg = ""
  form = VenueForm(request.form, meta={'csrf': False})
  if not form.validate():
    errormsg = "Form format error."
    error = True
  else:
    try:
      venue = Venue()
      venue.update(request.form)
      exists = db.session.query(Venue.query.filter(Venue.name == venue.name).exists()).scalar()
      if exists:
        errorMsg = "Venue's existed already!"
        error = False
        raise Exception(errorMsg)

      venue.id = db.session.query(func.max(Venue.id)).scalar() + 1
      db.session.add(venue)
      db.session.commit()
    except:
        db.session.rollback()
        error = True
        print(sys.exc_info())
    finally:
        db.session.close()

  if not error:
    # on successful db insert, flash success
    flash('Venue ' + request.form['name'] + ' was successfully listed!')
  else:
    flash('An error occurred. Venue'  + request.form['name'] + ' could not be listed. ' + errormsg)

  return render_template('pages/home.html')

@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
  error = False
  try:
    venue = Venue.query.get(venue_id)
    db.session.delete(venue)
    db.session.commit()
  except:
    db.session.rollback()
    error = True
  finally:
    db.session.close()

  if error:
    flash('An error occurred. Venue could not be deleted.')
    abort(500)
  else:
    flash('Venue was deleted successfully.')
    return jsonify({'success': True})


#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
  data = []
  
  for artist in Artist.query.all():
    data.append({
      "id": artist.id,
      "name": artist.name
    })
  return render_template('pages/artists.html', artists=data)

@app.route('/artists/search', methods=['POST'])
def search_artists():
  search_text = request.form.get('search_term', '')
  artists = Artist.query.filter(Artist.name.ilike('%' + search_text + '%')).all()
  response = {
    'count': len(artists),
    'data': []
  }

  result_count = len(artists)
  for i in range(0, result_count):
    response['data'].append({
      'id': artists[i].id,
      'name': artists[i].name,
      'num_upcoming_shows': len(specify_shows(artists[i].shows))
    })
  return render_template('pages/search_artists.html', results=response, search_term=search_text)

@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
  artist = Artist.query.get(artist_id)
  data = artist.__dict__
  data['genres'] = artist.genres.split(',')
  upcoming_shows = specify_shows(artist.shows)
  data['upcoming_shows'] = []
  for show in upcoming_shows:
    data['upcoming_shows'].append(parse_show(show, "Venue", ["id", "name", "image_link"]))
  data['upcoming_shows_count'] = len(upcoming_shows)

  past_shows = specify_shows(artist.shows, "<")
  data['past_shows'] = []
  for show in past_shows:
    data['past_shows'].append(parse_show(show, "Venue", ["id", "name", "image_link"]))
  data['past_shows_count'] = len(past_shows)

  return render_template('pages/show_artist.html', artist=data)

#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
  artist = Artist.query.get(artist_id)
  data = artist.__dict__
  data['website_link'] = artist.website
  data['genres'] = artist.genres.split(',')
  form = ArtistForm(formdata = None, data=data)
  return render_template('forms/edit_artist.html', form=form, artist=data)

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
  error = False
  errormsg = ""
  form = ArtistForm(request.form, meta={'csrf': False})
  if not form.validate():
    errormsg = "Form format error."
    error = True
  else:
    try:
      artist = Artist.query.get(artist_id)
      artist.update(request.form)
      db.session.add(artist)
      db.session.commit()
    except:
        db.session.rollback()
        error = True
        print(sys.exc_info())
    finally:
        db.session.close()

  if not error:
    # on successful db insert, flash success
    flash('Artist ' + request.form['name'] + ' was successfully editted!')
  else:
    flash('An error occurred. Artist '  + request.form['name'] + ' could not be liedittedsted. ' + errormsg)


  return redirect(url_for('show_artist', artist_id=artist_id))

@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
  venue = Venue.query.get(venue_id)
  data = venue.__dict__
  data['website_link'] = venue.website
  data['genres'] = venue.genres.split(',')
  form = VenueForm(formdata = None, data=data)
  return render_template('forms/edit_venue.html', form=form, venue=data)

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
  error = False
  errormsg = ""
  form = VenueForm(request.form, meta={'csrf': False})
  if not form.validate():
    errormsg = "Form format error."
    error = True
  else:
    try:
      venue = Venue.query.get(venue_id)
      venue.update(request.form)

      db.session.add(venue)
      db.session.commit()
    except:
        db.session.rollback()
        error = True
        print(sys.exc_info())
    finally:
        db.session.close()

  if not error:
    # on successful db insert, flash success
    flash('Venue ' + request.form['name'] + ' was successfully edited!')
  else:
    flash('An error occurred. Venue'  + request.form['name'] + ' could not be edited. ' + errormsg)

  return redirect(url_for('show_venue', venue_id=venue_id))

#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
  form = ArtistForm()
  return render_template('forms/new_artist.html', form=form)

@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
  error = False
  errorMsg = ""
  form = ArtistForm(request.form, meta={'csrf': False})
  if not form.validate():
    errorMsg = "Form format error."
    error = True
  else:
    try:
      artist = Artist()
      artist.update(request.form)
      exists = db.session.query(Artist.query.filter(Artist.name == artist.name).exists()).scalar()
      if exists:
        errorMsg = "Artist's existed already!"
        error = False
        raise Exception(errorMsg)

      artist.id = db.session.query(func.max(Artist.id)).scalar() + 1
      db.session.add(artist)
      db.session.commit()
    except:
        db.session.rollback()
        error = True
        print(sys.exc_info())
    finally:
        db.session.close()

  if not error:
    # on successful db insert, flash success
    flash('Artist ' + request.form['name'] + ' was successfully listed!')
  else:
    flash('An error occurred. Artist '  + request.form['name'] + ' could not be listed. ' + errorMsg)

  return render_template('pages/home.html')

#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
  data = []
  for show in Show.query.all():
    show_data_venue = parse_show(show, "Venue", ["id", "name"])
    show_data_artist = parse_show(show, "Artist", ["id", "name", "image_link"])
    data.append({
      "venue_id": show_data_venue["venue_id"],
      "venue_name": show_data_venue["venue_name"],
      "artist_id": show_data_artist["artist_id"],
      "artist_name": show_data_artist["artist_name"],
      "artist_image_link": show_data_artist["artist_image_link"],
      "start_time": show_data_artist["start_time"]
    })
  return render_template('pages/shows.html', shows=data)

@app.route('/shows/create')
def create_shows():
  # renders form. do not touch.
  form = ShowForm()
  return render_template('forms/new_show.html', form=form)

@app.route('/shows/create', methods=['POST'])
def create_show_submission():
  error = False
  errorMsg = ""
  form = ShowForm()
  try:
    if Venue.query.get(form.venue_id.data) is None:
      errorMsg = "Venue is not found"
      raise Exception(errorMsg)
    if Artist.query.get(form.artist_id.data) is None:
      errorMsg = "Artist is not found"
      raise Exception(errorMsg)
    show = Show()
    show.id = db.session.query(func.max(Show.id)).scalar() + 1
    show.venue_id = form.venue_id.data
    show.artist_id = form.artist_id.data
    show.start_time = form.start_time.data
    print(show)
    db.session.add(show)
    db.session.commit()
  except:
    db.session.rollback()
    error = False
  finally:
    db.session.close()
  
  if not error:
    # on successful db insert, flash success
    flash('Show was successfully listed!')
  else:
    flash('An error occurred. Show could not be listed. ' + errorMsg)
  return render_template('pages/home.html')

@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

#----------------------------------------------------------------------------#
# Launch.
#----------------------------------------------------------------------------#

# Default port:
'''
if __name__ == '__main__':
    app.run()
'''

# Or specify port manually:
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 3000))
    app.debug=DEBUG
    app.run(host='0.0.0.0', port=port)

#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import json
import dateutil.parser
import babel
from flask import render_template, request, Response, flash, redirect, url_for, jsonify, abort
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
from models import db, Venue, Artist, Show
from datetime import datetime

moment = Moment(app)
app.config.from_object('config')
db.init_app(app)
migrate = Migrate(app, db)

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
  venue = Venue.query.get_or_404(venue_id)

  past_shows = []
  upcoming_shows = []
  past_shows_query = db.session.query(Show).join(Artist).filter(Show.venue_id==venue_id).filter(Show.start_time < datetime.now()).all()
  for show in past_shows_query:
    past_shows.append({
      'artist_id': show.artist.id,
      'artist_name': show.artist.name,
      'artist_image_link': show.artist.image_link,
      'start_time': show.start_time.isoformat()
    })

  upcoming_shows_query = db.session.query(Show).join(Artist).filter(Show.venue_id==venue_id).filter(Show.start_time >= datetime.now()).all()
  for show in upcoming_shows_query:
    upcoming_shows.append({
      'artist_id': show.artist.id,
      'artist_name': show.artist.name,
      'artist_image_link': show.artist.image_link,
      'start_time': show.start_time.isoformat()
    })

  # object class to dict
  data = vars(venue)

  data['genres'] = venue.genres.split(',')

  data['past_shows'] = past_shows
  data['upcoming_shows'] = upcoming_shows
  data['past_shows_count'] = len(past_shows)
  data['upcoming_shows_count'] = len(upcoming_shows)

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
    errorMsg = "Form format error."
    error = True
    message = []
    for field, errors in form.errors.items():
        for error in errors:
            message.append(f"{field}: {error}")
    flash('Please fix the following errors: ' + ', '.join(message))
  else:
    try:
      venue = Venue()
      venue.name = form.name.data
      venue.city = form.city.data
      venue.state = form.state.data
      venue.address = form.address.data
      venue.phone = form.phone.data
      venue.facebook_link = form.facebook_link.data
      venue.website = form.website_link.data
      venue.image_link = form.image_link.data
      venue.seeking_talent = form.seeking_talent.data
      venue.seeking_description = form.seeking_description.data

      genres = request.form.getlist('genres')
      venue.genres = ','.join(genres)

      exists = db.session.query(Venue.query.filter(Venue.name == venue.name).exists()).scalar()
      if exists:
        errorMsg = "Venue's existed already!"
        error = False
        raise Exception(errorMsg)

      db.session.add(venue)
      db.session.commit()
    except:
        db.session.rollback()
        error = True
        errorMsg = str(sys.exc_info())
        print(sys.exc_info())
    finally:
        db.session.close()

  if not error:
    # on successful db insert, flash success
    flash('Venue ' + request.form['name'] + ' was successfully listed!')
  else:
    flash('An error occurred. Venue'  + request.form['name'] + ' could not be listed. ' + errorMsg)

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
  artist = Artist.query.get_or_404(artist_id)

  past_shows = []
  upcoming_shows = []
  past_shows_query = db.session.query(Show).join(Venue).filter(Show.artist_id==artist_id).filter(Show.start_time < datetime.now()).all()
  for show in past_shows_query:
    past_shows.append({
      'venue_id': show.venue.id,
      'venue_name': show.venue.name,
      'venue_image_link': show.venue.image_link,
      'start_time': show.start_time.isoformat()
    })

  upcoming_shows_query = db.session.query(Show).join(Venue).filter(Show.artist_id==artist_id).filter(Show.start_time >= datetime.now()).all()
  for show in upcoming_shows_query:
    upcoming_shows.append({
      'venue_id': show.venue.id,
      'venue_name': show.venue.name,
      'venue_image_link': show.venue.image_link,
      'start_time': show.start_time.isoformat()
    })

  # object class to dict
  data = vars(artist)

  data['genres'] = artist.genres.split(',')
  data['past_shows'] = past_shows
  data['upcoming_shows'] = upcoming_shows
  data['past_shows_count'] = len(past_shows)
  data['upcoming_shows_count'] = len(upcoming_shows)

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
  errorMsg = ""
  form = ArtistForm(request.form, meta={'csrf': False})
  if not form.validate():
    errorMsg = "Form format error."
    error = True
    message = []
    for field, errors in form.errors.items():
        for error in errors:
            message.append(f"{field}: {error}")
    flash('Please fix the following errors: ' + ', '.join(message))
  else:
    try:
      artist = Artist.query.get(artist_id)
      artist.name = form.name.data
      artist.city = form.city.data
      artist.state = form.state.data
      artist.phone = form.phone.data
      artist.facebook_link = form.facebook_link.data
      artist.image_link = form.image_link.data
      artist.website = form.website_link.data
      artist.seeking_venue = form.seeking_venue.data
      artist.seeking_description = form.seeking_description.data

      genres = request.form.getlist('genres')
      artist.genres = ','.join(genres)

      db.session.add(artist)
      db.session.commit()
    except:
        db.session.rollback()
        error = True
        errorMsg = str(sys.exc_info())
        print(sys.exc_info())
    finally:
        db.session.close()

  if not error:
    # on successful db insert, flash success
    flash('Artist ' + request.form['name'] + ' was successfully editted!')
  else:
    flash('An error occurred. Artist '  + request.form['name'] + ' could not be liedittedsted. ' + errorMsg)


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
  errorMsg = ""
  form = VenueForm(request.form, meta={'csrf': False})
  if not form.validate():
    errorMsg = "Form format error."
    error = True
    message = []
    for field, errors in form.errors.items():
        for error in errors:
            message.append(f"{field}: {error}")
    flash('Please fix the following errors: ' + ', '.join(message))
  else:
    try:
      venue = Venue.query.get(venue_id)
      venue.name = form.name.data
      venue.city = form.city.data
      venue.state = form.state.data
      venue.address = form.address.data
      venue.phone = form.phone.data
      venue.facebook_link = form.facebook_link.data
      venue.website = form.website_link.data
      venue.image_link = form.image_link.data
      venue.seeking_talent = form.seeking_talent.data
      venue.seeking_description = form.seeking_description.data

      genres = request.form.getlist('genres')
      venue.genres = ','.join(genres)

      db.session.add(venue)
      db.session.commit()
    except:
        db.session.rollback()
        error = True
        errorMsg = str(sys.exc_info())
        print(sys.exc_info())
    finally:
        db.session.close()

  if not error:
    # on successful db insert, flash success
    flash('Venue ' + request.form['name'] + ' was successfully edited!')
  else:
    flash('An error occurred. Venue'  + request.form['name'] + ' could not be edited. ' + errorMsg)

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
    message = []
    for field, errors in form.errors.items():
        for error in errors:
            message.append(f"{field}: {error}")
    flash('Please fix the following errors: ' + ', '.join(message))
  else:
    try:
      artist = Artist()
      artist.name = form.name.data
      artist.city = form.city.data
      artist.state = form.state.data
      artist.phone = form.phone.data
      artist.facebook_link = form.facebook_link.data
      artist.image_link = form.image_link.data
      artist.website = form.website_link.data
      artist.seeking_venue = form.seeking_venue.data
      artist.seeking_description = form.seeking_description.data

      genres = request.form.getlist('genres')
      artist.genres = ','.join(genres)

      exists = db.session.query(Artist.query.filter(Artist.name == artist.name).exists()).scalar()
      if exists:
        errorMsg = "Artist's existed already!"
        error = False
        raise Exception(errorMsg)

      db.session.add(artist)
      db.session.commit()
    except:
        db.session.rollback()
        error = True
        errorMsg = str(sys.exc_info())
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
    data.append({
      "venue_id": show.venue_id,
      "venue_name": show.venue.name,
      "artist_id": show.artist_id,
      "artist_name": show.artist.name,
      "artist_image_link": show.artist.image_link,
      "start_time": show.start_time.strftime('%Y-%m-%d %H:%M:%S')
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
  form = ShowForm(request.form, meta={'csrf': False})
  if not form.validate():
    error = True
    errorMsg = "Form fomat error."
    message = []
    for field, errors in form.errors.items():
        for error in errors:
            message.append(f"{field}: {error}")
    flash('Please fix the following errors: ' + ', '.join(message))
  else:
    try:
      if Venue.query.get(form.venue_id.data) is None:
        errorMsg = "Venue is not found"
        raise Exception(errorMsg)
      if Artist.query.get(form.artist_id.data) is None:
        errorMsg = "Artist is not found"
        raise Exception(errorMsg)

      show = Show()
      show.venue_id = form.venue_id.data
      show.artist_id = form.artist_id.data
      show.start_time = form.start_time.data
      db.session.add(show)
      db.session.commit()
    except:
      db.session.rollback()
      error = True
      errorMsg = str(sys.exc_info())
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

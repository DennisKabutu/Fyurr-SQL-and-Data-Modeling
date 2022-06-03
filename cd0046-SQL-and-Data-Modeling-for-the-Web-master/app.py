#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

from distutils.log import error
from email.policy import default
import json
from unicodedata import name
import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from forms import *
from flask_migrate import Migrate
import sys
from models import *
#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
db = SQLAlchemy(app)
migrate = Migrate(app=app,db=db)
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
  locations = Venue.query.distinct('city','state').order_by('state').all()
  
  ## Data is an empty list will be soon populate by the results from the db
  data = []
  for location in locations:
        local_venues = Venue.query.filter_by(city = location.city,state = location.state).all()
        local_venue_list = []
        for venue in local_venues:
              local_venue_list.append({
                "id":venue.id,
                "name":venue.name
                ## TODO add the upcoming_show key value
              })
        data.append({"city": location.city,"state":location.state,"venues":local_venue_list})                         
  return render_template('pages/venues.html', areas=data);

@app.route('/venues/search', methods=['POST'])
def search_venues():
  # TODO: implement search on artists with partial string search. Ensure it is case-insensitive.
  # seach for Hop should return "The Musical Hop".
  # search for "Music" should return "The Musical Hop" and "Park Square Live Music & Coffee"
  
  ##Get the search_term from the Form's user input
  user_input_search_term = request.form.get('search_term','')
  
  venues_search_results = Venue.query.filter(Venue.name.ilike('%'+user_input_search_term + '%')).all()
  data = []
  
  for search_result in venues_search_results:
        data.append({
          "id":search_result.id,
          "name":search_result.name,
          "num_upcoming_shows":Show.query.filter(Show.venue_id==search_result.id,
                                                 Show.start_time > datetime.now()).count()
        })
        
  response={
    "count": len(venues_search_results),
    "data":data
  }
  
  return render_template('pages/search_venues.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
  # shows the venue page with the given venue_id
  # TODO: replace with real venue data from the venues table, using venue_id
  venue = Venue.query.filter_by(id=venue_id).all()[0]
  past_shows_list = []
  upcoming_shows_list = []
  
  shows = Show.query.filter_by(venue_id=venue_id).join(Artist, Show.artist_id == Artist.id).all()
  for show in shows:
        show_venue = {
          "artist_id":show.artist_id,
          "artist_name":show.artist_name,
          "artist_image_link":show.artist.image_link,
          "start_time":str(show.start_time)
        }
        
        current_time = datetime.now()
        
        if(current_time > show.start_time):
              past_shows_list.append(show_venue)
        else:
              upcoming_shows_list.append(show_venue)
        
  data={
    "id": venue.id,
    "name": venue.name,
    "genres": venue.genres,
    "address": venue.address,
    "city": venue.city,
    "state": venue.state,
    "phone": venue.phone,
    "website": venue.website,
    "facebook_link": venue.facebook_link,
    "seeking_talent": venue.seeking_talent,
    "seeking_description": venue.seeking_description,
    "image_link": venue.image_link,
    "past_shows": past_shows_list,
    "upcoming_shows": upcoming_shows_list,
    "past_shows_count": len(past_shows_list),
    "upcoming_shows_count": len(upcoming_shows_list),
  }
 
  
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
  
  try:
    form = VenueForm(request.form)
    
    venue = Venue(
      name = form.name.data,
      city = form.city.data,
      state = form.state.data,
      address = form.address.data,
      genres = form.genres.data,
      facebook_link = form.facebook_link.data,
      image_link = form.image_link.data,
      phone = form.phone.data,
      website = form.website_link.data,
      seeking_talent=form.seeking_talent.data,
      seeking_description = form.seeking_description.data
    )
    db.session.add(venue)
    db.session.commit()
  except:
    error = True
    db.session.rollback()
    print(sys.exc_info())
  finally:
    db.session.close()
  
 
  if error:
    flash('Venue ' + request.form['name'] + ' was not added!')
  else:
     flash('Venue ' + request.form['name'] + ' was successfully listed!')

  return render_template('pages/home.html')

@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
  try:
    Venue.query.filter_by(id=venue_id).delete()
    db.session.commit()
  except:
    db.session.rollback()
    print(sys.exc_info)
  finally:
    db.session.close()


  # TODO: Complete this endpoint for taking a venue_id, and using
  # SQLAlchemy ORM to delete a record. Handle cases where the session commit could fail.

  # BONUS CHALLENGE: Implement a button to delete a Venue on a Venue Page, have it so that
  # clicking that button delete it from the db then redirect the user to the homepage
  return None

#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
  # TODO: replace with real data returned from querying the database
  artists_data = []
  artist_results = Artist.query.all()
  for artist in artist_results:
    artists_data.append({"id": artist.id,"name": artist.name,})
  return render_template('pages/artists.html', artists=artists_data)

@app.route('/artists/search', methods=['POST'])
def search_artists():
  # TODO: implement search on artists with partial string search. Ensure it is case-insensitive.
  # seach for "A" should return "Guns N Petals", "Matt Quevado", and "The Wild Sax Band".
  # search for "band" should return "The Wild Sax Band".

    artist_search_term = request.form.get('search_term','')
  
    artist_search_results = Venue.query.filter(Venue.name.ilike('%'+artist_search_term + '%')).all()
    data = []
  
    for search_result in artist_search_results:
        data.append({
          "id":search_result.id,
          "name":search_result.name,
          "num_upcoming_shows":Show.query.filter(Show.artist_id==search_result.id,
                                                 Show.start_time > datetime.now()).count()
        })
        
    response={
    "count": len(artist_search_results),
    "data":data
    }
    return render_template('pages/search_artists.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
  # shows the artist page with the given artist_id
  # TODO: replace with real artist data from the artist table, using artist_id

  artist_results = Artist.query.filter_by(id=artist_id).first()
  artist_past_show = []
  artist_upcoming_show = []
  artist_shows = Show.query.filter_by(artist_id = artist_id).join(Venue, Show.venue_id == Venue.id).all()

  for show in artist_shows:
    artist_show = {
      "venue_id":show.venue_id,
      "venue_name":show.venue.name,
      "venue_image_link":show.venue.image_link,
      "start_time":str(show.start_time)
    }

    now_date = datetime.now()

    if now_date > show.start_time:
      artist_past_show.append(artist_show)
    else:
      artist_upcoming_show.append(artist_show)


  data={
    "id":artist_results.id ,
    "name": artist_results.name,
    "genres": artist_results.genres,
    "city": artist_results.city,
    "state": artist_results.state,
    "phone": artist_results.phone,
    "website": artist_results.website,
    "facebook_link": artist_results.facebook_link,
    "seeking_venue": artist_results.seeking_venue,
    "seeking_description": artist_results.seeking_description,
    "image_link":artist_results.image_link,
    "past_shows": artist_past_show,
    "upcoming_shows": artist_upcoming_show,
    "past_shows_count": len(artist_past_show),
    "upcoming_shows_count": len(artist_upcoming_show),
  }
  return render_template('pages/show_artist.html', artist=data)

#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
  form = ArtistForm()
  artist_to_display = Artist.query.filter_by(id=artist_id).first()
  artist={
    "id": artist_to_display.id,
    "name": artist_to_display.name,
    "genres": artist_to_display.genres,
    "city": artist_to_display.city,
    "state": artist_to_display.state,
    "phone": artist_to_display.phone,
    "website": artist_to_display.website,
    "facebook_link": artist_to_display.facebook_link,
    "seeking_venue": artist_to_display.seeking_venue,
    "seeking_description": artist_to_display.description,
    "image_link": artist_to_display.image_link
  }
  # TODO: populate form with fields from artist with ID <artist_id>
  return render_template('forms/edit_artist.html', form=form, artist=artist)

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
  # TODO: take values from the form submitted, and update existing
  # artist record with ID <artist_id> using the new attributes
  error = False
  artist_to_edit = Artist.query.filter_by(id = artist_id).first()

  try:
    form = ArtistForm()
    artist_to_edit.name = form.name.data
    artist_to_edit.city = form.city.data
    artist_to_edit.phone = form.phone.data
    artist_to_edit.genres = form.genres.data
    artist_to_edit.facebook_link = form.facebook_link.data
    artist_to_edit.image_link = form.image_link.data

    db.session.commit()
  except:
    db.session.rollback()
    error = True
    print(sys.exc_info())
  finally:
    db.session.close()

  if error:
    flash('Artist ' + request.form['name'] + ' was not editted!')
  else:
     flash('Artist ' + request.form['name'] + ' was successfully edited!')

  return redirect(url_for('show_artist', artist_id=artist_id))

@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
  form = VenueForm()
  venue_to_display = Venue.query.get(venue_id)
  
  venue={
    "id": venue_to_display.id,
    "name": venue_to_display.name,
    "genres": venue_to_display.genres,
    "address": venue_to_display.address,
    "city": venue_to_display.city,
    "state": venue_to_display.state,
    "phone": venue_to_display.phone,
    "website": venue_to_display.website,
    "facebook_link": venue_to_display.facebook_link,
    "seeking_talent": venue_to_display.seeking_talent,
    "seeking_description": venue_to_display.seeking_description,
    "image_link": venue_to_display.image_link
  }
  # TODO: populate form with values from venue with ID <venue_id>
  return render_template('forms/edit_venue.html', form=form, venue=venue)

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):


  # TODO: take values from the form submitted, and update existing
  # venue record with ID <venue_id> using the new attributes
   error = False
   venue_to_edit = Venue.query.get(venue_id)

   try:
    form = VenueForm()
    venue_to_edit.name = form.name.data
    venue_to_edit.city = form.city.data
    venue_to_edit.phone = form.phone.data
    venue_to_edit.genres = form.genres.data
    venue_to_edit.facebook_link = form.facebook_link.data
    venue_to_edit.image_link = form.image_link.data

    db.session.commit()
   except:
    db.session.rollback()
    error = True
    print(sys.exc_info())
   finally:
    db.session.close()

   if error:
    flash('Venue ' + request.form['name'] + ' was not editted!')
   else:
     flash('Venue ' + request.form['name'] + ' was successfully edited!')

 
   return redirect(url_for('show_venue', venue_id=venue_id))

#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
  form = ArtistForm()
  return render_template('forms/new_artist.html', form=form)

@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
  # called upon submitting the new artist listing form
  # TODO: insert form data as a new Venue record in the db, instead
  # TODO: modify data to be the data object returned from db insertion
  error = False
  try:
    form = ArtistForm()
    artist_to_add = Artist(
      name = form.name.data,
      city = form.city.data,
      state = form.state.data,
      phone = form.phone.data,
      genres = form.genres.data,
      facebook_link = form.facebook_link.data,
      image_link = form.image_link.data,
      website = form.website_link.data,
      seeking_venue = form.seeking_venue.data,
      seeking_description = form.seeking_description.data
    )
    db.session.add(artist_to_add)
    db.session.commit()
  except:
    db.session.rollback()
    print(sys.exc_info())
    error = True
  finally:
    db.session.close()

  if not error:
  # on successful db insert, flash success
    flash('Artist ' + request.form['name'] + ' was successfully listed!')
  # TODO: on unsuccessful db insert, flash an error instead.
  else:
   flash('An error occurred. Artist ' + request.form['name'] + ' could not be listed.')


  return render_template('pages/home.html')


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
  # displays list of shows at /shows
  # TODO: replace with real venues data.
  all_shows = shows=Show.query.join(Venue, Show.venue_id == Venue.id).join(Artist, Show.artist_id == Artist.id).all()
  data = []
  for show in all_shows:
    data.append({
      "venue_id": show.venue_id,
      "venue_name": show.venue.name,
      "artist_id": show.artist_id,
      "artist_name": show.artist.name,
      "artist_image_link": show.artist.image_link,
      "start_time":  show.start_time.strftime('%Y-%m-%d %H:%M:%S')
    })
  
  return render_template('pages/shows.html', shows=data)

@app.route('/shows/create')
def create_shows():
  # renders form. do not touch.
  form = ShowForm()
  return render_template('forms/new_show.html', form=form)

@app.route('/shows/create', methods=['POST'])
def create_show_submission():
  # called to create new shows in the db, upon submitting new show listing form
  # TODO: insert form data as a new Show record in the db, instead
  error = False
  try:
    show_form = ShowForm()
    show_to_add = Show(
      venue_id = show_form.venue_id.data,
      artist_id = show_form.artist_id.data,
      start_time = show_form.start_time.data
    )

    db.session.add(show_to_add)
    db.session.commit()

  except:
    db.session.rollback()
    error = True
    print(sys.exc_info())
  finally:
    db.session.close()
  if not error:
  # on successful db insert, flash success
    flash('Show was successfully listed!')
  else:
  # TODO: on unsuccessful db insert, flash an error instead.
   flash('An error occurred. Show could not be listed.')
  # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/

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
if __name__ == '__main__':
    app.run()

# Or specify port manually:

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)


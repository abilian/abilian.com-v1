#!/usr/bin/env python
# coding=utf-8

from StringIO import StringIO
import locale
import mimetypes
from os.path import join
import re
import datetime
from PIL import Image

from flask import Flask, render_template, redirect, url_for, make_response, \
    abort, request, g
from flask.ext.frozen import Freezer
from flask.ext.markdown import Markdown
from flask.ext.assets import Environment as AssetManager

from .config import Config
from .models import pages, get_pages
from .views import bp, feed


app = Flask(__name__)
asset_manager = AssetManager()
freezer = Freezer()


def setup_app(app):
  app.config.from_object(Config)
  app.register_blueprint(bp)
  asset_manager.init_app(app)
  pages.init_app(app)
  freezer.init_app(app)
  markdown_manager = Markdown(app)



###############################################################################
# Filters

@app.template_filter()
def to_rfc2822(dt):
  if not dt:
    return
  current_locale = locale.getlocale(locale.LC_TIME)
  locale.setlocale(locale.LC_TIME, "en_US")
  formatted = dt.strftime("%a, %d %b %Y %H:%M:%S +0000")
  locale.setlocale(locale.LC_TIME, current_locale)
  return formatted


@app.context_processor
def inject_context_variables():
  return dict(BASE_URL=Config.BASE_URL, menu=Config.MAIN_MENU)


@app.url_defaults
def add_language_code(endpoint, values):
  values.setdefault('lang_code', g.lang_code)


@app.url_value_preprocessor
def pull_lang_code(endpoint, values):
  m = re.match("/(..)/", request.path)
  if m:
    g.lang_code = m.group(1)
  else:
    g.lang_code = 'fr'
  if not g.lang_code in Config.ALLOWED_LANGS:
    abort(404)


@app.before_request
def prepare_metadata():
  g.metadata = {
    'DC.title': "Abilian",
    'DC.publisher': "Abilian SAS, proud french tech company",
    'og:type': 'website',
    'og:site_name': 'Abilian',

    'twitter:site': '@abilianhq',
    'twitter:card': 'summary',
  }


###############################################################################
# Freezer helper

@freezer.register_generator
def url_generator():
  # URLs as strings
  yield '/fr/'


###############################################################################
# Global (app-level) routes

@app.route('/')
def index():
  return redirect(url_for("mod.home", lang_code='fr'))


@app.route('/<path:path>')
def catch_all(path):
  if path.endswith('.php') or '.php/' in path:
    return redirect(url_for("index"), code=301)
  elif path.startswith('a/') or path.startswith('info/'):
    return redirect(url_for("index"), code=301)
  elif re.match(r'.*\.html/', path) or re.match(r'.*\.html$', path):
    return redirect(url_for("index"), code=301)
  elif path.startswith('robots.txt'):
    return redirect(url_for("robots_txt"))
  else:
    abort(404)


@app.route('/robots.txt')
def robots_txt():
  return ""


@app.route('/image/<path:path>')
def image(path):
  if '..' in path:
    abort(500)
  fd = open(join(app.root_path, "images", path))
  data = fd.read()

  hsize = int(request.args.get("h", 0))
  vsize = int(request.args.get("v", 0))
  if hsize > 1000 or vsize > 1000:
    abort(500)

  if hsize:
    image = Image.open(StringIO(data))
    x, y = image.size

    x1 = hsize
    y1 = int(1.0 * y * hsize / x)
    image.thumbnail((x1, y1), Image.ANTIALIAS)
    output = StringIO()
    image.save(output, "PNG")
    data = output.getvalue()
  if vsize:
    image = Image.open(StringIO(data))
    x, y = image.size

    x1 = int(1.0 * x * vsize / y)
    y1 = vsize
    image.thumbnail((x1, y1), Image.ANTIALIAS)
    output = StringIO()
    image.save(output, "PNG")
    data = output.getvalue()

  response = make_response(data)
  response.headers['content-type'] = mimetypes.guess_type(path)
  return response


@app.route('/feed/')
def global_feed():
  return feed()


@app.route('/sitemap.xml')
def sitemap():
  today = datetime.date.today()
  recently = datetime.date(year=today.year, month=today.month, day=1)
  response = make_response(render_template('sitemap.xml', pages=get_pages(),
                           today=today, recently=recently))
  response.headers['Content-Type'] = 'text/xml'
  return response


@app.route('/favicon.ico')
def favicon():
  return ''


@app.route('/403.html')
def error403():
  return render_template('403.html', page=dict(title="Fordidden"))


@app.route('/404.html')
def error404():
  return render_template('404.html', page=dict(title="Not found"))


@app.route('/500.html')
def error500():
  return render_template('500.html')


@app.errorhandler(404)
def page_not_found(error):
  page = {'title': "Page not found"}
  return render_template('404.html', page=page), 404



#!/usr/bin/env python
# coding=utf-8

from StringIO import StringIO
import locale
from logging import FileHandler
import mimetypes
from os.path import join
import re
from unicodedata import normalize
import datetime
from PIL import Image
import bleach
from fabric.api import local
from argh import *

from flask import Flask, render_template, redirect, url_for, make_response, \
    abort, request, Blueprint, g
from flask.ext.frozen import Freezer
from flask.ext.flatpages import FlatPages, Page
from flask.ext.markdown import Markdown
from flask.ext.assets import Environment as AssetManager
from markdown import markdown
from markupsafe import Markup


def renderer(text):
  html = markdown(text)
  while True:
    m = re.search(r'\[\[block "(.*)"\]\]', html)
    if not m:
      break
    block = get_blocks(g.lang_code)[m.group(1)]
    html = html[0:m.start(0)] + unicode(block) + html[m.end(0):]
  return html


# Configuration
class Config:
  BASE_URL = 'http://abilian.com'
  DEBUG = True
  ASSETS_DEBUG = DEBUG
  # FIXME later
  #ASSETS_DEBUG = True
  FLATPAGES_AUTO_RELOAD = True
  FLATPAGES_EXTENSION = '.md'
  FLATPAGES_ROOT = 'pages'
  FLATPAGES_HTML_RENDERER = staticmethod(renderer)

  # App configuration
  FEED_MAX_LINKS = 25
  SECTION_MAX_LINKS = 12

  ALLOWED_LANGS = ['fr']

  MAIN_MENU = [
    ('solutions/', u'Solutions'),
    ('technologies/', u'Plateforme'),
    ('services/', u'Services'),
    ('news/', u'Actualité'),
    ('a-propos/', u'A propos'),
  ]


app = Flask(__name__)
mod = Blueprint('mod', __name__, url_prefix='/<string(length=2):lang_code>')
asset_manager = AssetManager()
pages = FlatPages()
freezer = Freezer()


def setup_app(app):
  app.config.from_object(Config)
  app.register_blueprint(mod)
  asset_manager.init_app(app)
  pages.init_app(app)
  freezer.init_app(app)
  markdown_manager = Markdown(app)


###############################################################################
# Model helpers
###############################################################################

# Monkey patch
Page__init__orig = Page.__init__

def Page__init__(self, path, meta_yaml, body, html_renderer):
  Page__init__orig(self, path, meta_yaml, body, html_renderer)
  date = self.meta.get('date')

  if not date:
    self.meta['date'] = datetime.date.today()
  elif isinstance(date, str):
    year = int(date[0:4])
    month = int(date[5:7])
    day = int(date[8:10])
    date = datetime.date(year, month, day)
    self.meta['date'] = date

  if not self.meta.get('slug'):
    self.meta['slug'] = self.path.split('/')[-1]

  # Autogenerates abstract if needed
  if not self.meta.get('abstract'):
    abstract = bleach.clean(self.html, tags=[], strip=True)
    if len(abstract) > 250:
      abstract = abstract[0:250] + " [...]"
    self.meta['abstract'] = abstract

Page.__init__ = Page__init__


def get_pages(offset=None, limit=None):
  """
  Retrieves pages matching passed criterias.
  """
  articles = list(pages)
  # assign section value if none was provided in the metas
  for article in articles:
    if not article.meta.get('section'):
      article.meta['section'] = article.path.split('/')[0]

  # filter unpublished article
  if not app.debug:
    articles = [p for p in articles if p.meta.get('published') is True]

  # sort by date
  articles = sorted(articles, reverse=True,
                    key=lambda p: p.meta.get('date', datetime.date.today()))

  if offset and limit:
    return articles[offset:limit]
  elif limit:
    return articles[:limit]
  elif offset:
    return articles[offset:]
  else:
    return articles


def get_years(pages):
  years = list(set([page.meta.get('date').year for page in pages]))
  years.reverse()
  return years


def slugify(text, delim=u'-'):
  """Generates an slightly worse ASCII-only slug."""
  _punct_re = re.compile(r'[\t !"#$%&\'()*\-/<=>?@\[\\\]^_`{|},.]+')
  result = []
  for word in _punct_re.split(text.lower()):
    word = normalize('NFKD', word).encode('ascii', 'ignore')
    if word:
      result.append(word)
  return unicode(delim.join(result))


def get_news(offset=None, limit=None):
  all_pages = get_pages()
  all_news = [ page for page in all_pages if page.path.startswith("fr/news/") ]
  if offset and len(all_news) > offset:
    all_news = all_news[offset:]
  if limit and len(all_news) > limit:
    all_news = all_news[:limit]
  return all_news


#
# Blocks
#
class Blocks(object):
  def __init__(self, lang):
    self.lang = lang

  def __getitem__(self, key):
    fn = join(app.root_path, 'blocks', self.lang, key)
    src = open(fn).read()
    return Markup(markdown(unicode(src, 'utf8')))


def get_blocks(lang):
  return Blocks(lang)


def render_page():
  blocks = get_blocks(g.lang_code)


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


###############################################################################
# Preprocessing

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


@mod.url_defaults
def add_language_code(endpoint, values):
  values.setdefault('lang_code', g.lang_code)


@mod.url_value_preprocessor
def pull_lang_code(endpoint, values):
  g.lang_code = values.pop('lang_code')


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
  print path
  if path.endswith('.php') or '.php/' in path:
    return redirect(url_for("index"))
  elif path.startswith('a/') or path.startswith('info/'):
    return redirect(url_for("index"))
  elif re.match(r'.*\.html/', path) or re.match(r'.*\.html$', path):
    return redirect(url_for("index"))
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


###############################################################################
# Localized (mod-level) routes

@mod.route('/')
def home():
  template = "index.html"
  page = {'title': 'Abilian: connected we work'}
  news = get_news(limit=4)
  return render_template(template, page=page, news=news)


@mod.route('/<path:path>/')
def page(path=""):
  page = pages.get_or_404(g.lang_code + "/" + path + "/index")
  template = page.meta.get('template', '_page.html')
  jumbotron = page.meta.get('jumbotron')
  if jumbotron:
    jumbotron = get_blocks(g.lang_code)[jumbotron]
  print jumbotron
  return render_template(template, page=page, jumbotron=jumbotron)


@mod.route('/news/')
def news():
  all_news = get_news()
  recent_news = get_news(limit=5)
  page = {'title': u'Actualités pour Abilian'}
  return render_template('news.html', page=page, news=all_news,
                         recent_news=recent_news)


@mod.route('/news/<slug>')
def news_item(slug):
  page = pages.get_or_404(g.lang_code + "/news/" + slug)
  recent_news = get_news(limit=5)
  return render_template('news_item.html', page=page,
                         recent_news=recent_news)


@mod.route('/feed/')
def feed():
  articles = get_pages(limit=Config.FEED_MAX_LINKS)
  now = datetime.datetime.now()

  response = make_response(render_template('base.rss',
                                           pages=articles, build_date=now))
  response.headers['Content-Type'] = 'text/xml'
  return response


###############################################################################
# Commands

def build():
  """ Builds this site.
  """
  print("Building website...")
  app.debug = False
  asset_manager.config['ASSETS_DEBUG'] = False
  freezer.freeze()
  local("cp ./static/*.ico ./build/")
  local("cp ./static/*.txt ./build/")
  local("cp ./static/*.xml ./build/")
  print("Done.")


def serve(server='127.0.0.1', port=5001, debug=Config.DEBUG):
  """ Serves this site.
  """
  if not debug:
    import logging
    file_handler = FileHandler("error.log")
    file_handler.setLevel(logging.WARNING)
    app.logger.addHandler(file_handler)

  #asset_manager.config['ASSETS_DEBUG'] = debug
  app.debug = debug
  app.run(host=server, port=port, debug=debug)


def prod():
  serve(debug=False)


if __name__ == '__main__':
  setup_app(app)
  parser = ArghParser()
  parser.add_commands([build, serve, prod])
  parser.dispatch()

else:
  # App will be called from a WSGI server.
  setup_app(app)
  import logging
  file_handler = FileHandler("error.log")
  file_handler.setLevel(logging.WARNING)
  app.logger.addHandler(file_handler)
  #app.debug = True

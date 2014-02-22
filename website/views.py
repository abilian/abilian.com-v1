# coding=utf-8
"""
Localized (mod-level) routes
"""

import datetime
from flask import Blueprint, render_template, make_response, current_app, g
from website.models import get_news, pages, get_blocks, get_pages


bp = Blueprint('mod', __name__, url_prefix='/<string(length=2):lang_code>')
route = bp.route


@bp.url_defaults
def add_language_code(endpoint, values):
  values.setdefault('lang_code', g.lang_code)


@bp.url_value_preprocessor
def pull_lang_code(endpoint, values):
  g.lang_code = values.pop('lang_code')


@route('/')
def home():
  template = "index.html"
  page = {'title': 'Abilian: connected we work'}
  news = get_news(limit=4)
  return render_template(template, page=page, news=news)


@route('/<path:path>/')
def page(path=""):
  page = pages.get_or_404(g.lang_code + "/" + path + "/index")
  template = page.meta.get('template', '_page.html')
  jumbotron = page.meta.get('jumbotron')
  if jumbotron:
    jumbotron = get_blocks(g.lang_code)[jumbotron]
  print jumbotron
  return render_template(template, page=page, jumbotron=jumbotron)


@route('/news/')
def news():
  all_news = get_news()
  recent_news = get_news(limit=5)
  page = {'title': u'Actualités pour Abilian'}
  return render_template('news.html', page=page, news=all_news,
                         recent_news=recent_news)


@route('/news/<slug>/')
def news_item(slug):
  page = pages.get_or_404(g.lang_code + "/news/" + slug)
  recent_news = get_news(limit=5)
  return render_template('news_item.html', page=page,
                         recent_news=recent_news)


@route('/feed/')
def feed():
  config = current_app.config
  articles = get_pages(limit=config['FEED_MAX_LINKS'])
  now = datetime.datetime.now()

  response = make_response(render_template('base.rss',
                                           pages=articles, build_date=now))
  response.headers['Content-Type'] = 'text/xml'
  return response

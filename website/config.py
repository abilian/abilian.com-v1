# coding=utf-8
from flask import g
from markdown import markdown
import re


def renderer(text):
  from .models import get_blocks

  html = markdown(text)
  while True:
    m = re.search(r'\[\[block "(.*)"\]\]', html)
    if not m:
      break
    block = get_blocks(g.lang_code)[m.group(1)]
    html = html[0:m.start(0)] + unicode(block) + html[m.end(0):]
  return html


class Config:
  BASE_URL = 'http://abilian.com'
  DEBUG = True
  ASSETS_DEBUG = DEBUG
  # FIXME later
  #ASSETS_DEBUG = True
  FLATPAGES_AUTO_RELOAD = True
  FLATPAGES_EXTENSION = '.md'
  FLATPAGES_ROOT = '../pages'
  FLATPAGES_HTML_RENDERER = staticmethod(renderer)

  # App configuration
  FEED_MAX_LINKS = 25
  SECTION_MAX_LINKS = 12

  ALLOWED_LANGS = ['fr', 'en']

  MAIN_MENU = [
    ('solutions/', u'Solutions'),
    ('technologies/', u'Plateforme'),
    ('services/', u'Services'),
    ('news/', u'Actualité'),
    ('a-propos/', u'A propos'),
  ]

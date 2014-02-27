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
    block = get_blocks(g.lang)[m.group(1)]
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
  #ALLOWED_LANGS = ['fr']

  MAIN_MENU = {
    'fr': [('/fr/solutions/', u'Solutions'),
           ('/fr/technologies/', u'Plateforme'),
           ('/fr/services/', u'Services'),
           ('/fr/news/', u'Actualité'),
          ],
    'en': [],
          # [#('solutions/', u'Solutions'),
          #  ('/en/technologies/', u'Platform'),
          #  ('/en/services/', u'Services'),
          #  ('/en/news/', u'News'),
          #  ('/en/about/', u'About'), ],
  }

  SECONDARY_MENU = {
    'fr': [('/fr/a-propos/contact/', u"Nous contacter"),
           ('/fr/a-propos/', u"A propos d'Abilian?"),
           ('/fr/a-propos/jobs/', u"Offres d'emplois"),
          ],
    'en': [],
          # [('/en/why/', u"Why Abilian?"),
          #  ('/en/about/jobs/', u"Join our team"),
          #  ('/en/about/contact/', u"Contact us"),
          #  ],
  }

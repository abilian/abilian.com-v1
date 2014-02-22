from flask import request
from werkzeug.routing import RequestRedirect


REDIRECTS = [
  ('/2010/', '/fr/'),
  ('/Articles/', '/fr/news/'),
  ('/attend/', '/fr/lieu/'),
  ('/awards/', '/'),
  ('/Conferences/', '/fr/programme/'),
  ('/Conferences/', '/fr/programme/'),
  ('/connect/', '/'),
  ('/en/News', '/en/news/'),
  ('/en/News/', '/en/news/'),
  ('/en/program/', '/en/schedule/'),
  ('/en/register/', '/registration/'),
  ('/en/Schedule', '/en/schedule/'),
  ('/en/Sponsors/', '/en/partners/'),
  ('/en/sponsors/', '/en/partners/'),
  ('/en/Users/', '/en/'),
  ('/eng/', '/en/'),
  ('/eng/Univers/Code', '/en/code/'),
  ('/fr/about/', '/fr/a-propos/'),
  ('/fr/accueil', '/fr/'),
  ('/fr/inscription/', '/fr/registration/'),
  ('/fr/News/', '/fr/news/'),
  ('/fr/press/', '/fr/presse/'),
  ('/fr/venue/', '/fr/lieu/'),
  ('/fr/sponsors/', '/fr/partners/'),
  ('/fre', '/fr/'),
  ('/fre/', '/fr/'),
  ('/index.php/', '/fr/'),
  ('/join_form', '/registration/'),
  ('/News', '/fr/news/'),
  ('/News/', '/fr/news/'),
  ('/News/', '/fr/news/'),
  ('/open-innovation-summit-fr', '/'),
  ('/Partenaires-presse/', '/fr/presse/'),
  ('/press/', '/fr/presse/'),
  ('/programme/', '/fr/programme/'),
  ('/Programme/', '/fr/programme/'),
  ('/Register', '/registration/'),
  ('/rss/feed/news', '/en/feed/'),
  ('/rss/RSS', '/en/feed/'),
  ('/Sponsors/', '/fr/sponsors/'),
  ('/Tracks/', '/fr/programme/'),
  ('/Univers/', '/fr/'),
  ('/Univers/Code/', '/fr/code/'),
  ('/Univers/Experiment/', '/fr/experiment/'),
  ('/Univers/Schedule/', '/fr/programme/'),
  ('/Univers/Think/', '/fr/think/'),
  ('/Users/', '/fr/'),
]


def check_redirect():
  path = request.path
  for source, target in REDIRECTS:
    if path.startswith(source):
      url = "http://{}{}".format(request.host, target)
      raise RequestRedirect(url)


def register(app):
  app.before_request(check_redirect)

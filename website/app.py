#!/usr/bin/env python
# coding=utf-8

import datetime
import locale
import mimetypes
import re
from io import BytesIO
from os.path import join, split

from flask import Flask, abort, current_app, g, make_response, redirect, \
    render_template, request, session, url_for
from flask_flatpages import Page
from flaskext.markdown import Markdown
from PIL import Image

from .config import Config
from .extensions import asset_manager, babel
from .models import get_pages, pages
from .views import bp, feed

app = Flask(__name__)


def setup_app(app):
    app.config.from_object(Config)
    app.register_blueprint(bp)

    asset_manager.init_app(app)
    pages.init_app(app)
    Markdown(app)
    setup_babel(app)


def setup_babel(app):
    """
    Setup custom Babel config.
    """
    babel.init_app(app)

    def get_locale():
        lang = getattr(g, "lang")
        if not lang:
            lang = session.get("lang")
        if not lang:
            lang = preferred_language()
        return lang

    # TODO
    # babel.add_translations("website")
    babel.localeselector(get_locale)
    # babel.timezoneselector(get_timezone)


def preferred_language():
    langs = request.headers.get("Accept-Language", "").split(",")
    langs = [lang.strip() for lang in langs]
    langs = [lang.split(";")[0] for lang in langs]
    langs = [lang.strip() for lang in langs]
    for lang in langs:
        if len(lang) > 2:
            lang = lang[0:2]
        if lang in current_app.config["ALLOWED_LANGS"]:
            return lang
    return "en"


###############################################################################
# Filters


@app.template_filter()
def to_rfc2822(dt):
    if not dt:
        return
    current_locale = locale.getlocale(locale.LC_TIME)
    locale.setlocale(locale.LC_TIME, "C")
    formatted = dt.strftime("%a, %d %b %Y %H:%M:%S +0000")
    locale.setlocale(locale.LC_TIME, current_locale)
    return formatted


@app.context_processor
def inject_context_variables():
    def url_for(obj, **values):
        if isinstance(obj, Page):
            path = obj.path
            return request.url_root + join(*split(path)[0:-1]) + "/"
        else:
            from flask import url_for as url_for_orig

            return url_for_orig(obj, **values)

    config = app.config
    return dict(BASE_URL=config["BASE_URL"], url_for=url_for)


@app.url_defaults
def add_language_code(endpoint, values):
    values.setdefault("lang", g.lang)


@app.url_value_preprocessor
def pull_lang(endpoint, values):
    m = re.match("/(..)/", request.path)
    if m:
        g.lang = m.group(1)
    else:
        g.lang = "fr"
    if not g.lang in app.config["ALLOWED_LANGS"]:
        abort(404)


@app.before_request
def prepare_metadata():
    g.metadata = {
        "DC.title": "Abilian",
        "DC.publisher": "Abilian SAS, proud french tech company",
        "og:type": "website",
        "og:site_name": "Abilian",
        "twitter:site": "@abilianhq",
        "twitter:card": "summary",
    }


#
# Global (app-level) routes
#
@app.route("/")
def index():
    lang = session.get("lang")
    if not lang:
        lang = preferred_language()
    return redirect(url_for("mod.home", lang=lang))


@app.route("/<path:path>")
def redirects(path):
    if path.endswith(".php") or ".php/" in path:
        return redirect(url_for("index"), code=301)
    elif path.startswith("a/") or path.startswith("info/"):
        return redirect(url_for("index"), code=301)
    elif re.match(r".*\.html/", path) or re.match(r".*\.html$", path):
        return redirect(url_for("index"), code=301)
    elif path.startswith("robots.txt"):
        return redirect(url_for("robots_txt"))
    else:
        abort(404)


@app.route("/robots.txt")
def robots_txt():
    return ""


@app.route("/image/<path:path>")
def image(path):
    if ".." in path:
        abort(500)
    fd = open(join(app.root_path, "images", path), "rb")
    data = fd.read()

    hsize = int(request.args.get("h", 0))
    vsize = int(request.args.get("v", 0))
    if hsize > 1000 or vsize > 1000:
        abort(500)

    if hsize:
        image = Image.open(BytesIO(data))
        x, y = image.size

        x1 = hsize
        y1 = int(1.0 * y * hsize / x)
        image.thumbnail((x1, y1), Image.ANTIALIAS)
        output = BytesIO()
        image.save(output, "PNG")
        data = output.getvalue()
    if vsize:
        image = Image.open(BytesIO(data))
        x, y = image.size

        x1 = int(1.0 * x * vsize / y)
        y1 = vsize
        image.thumbnail((x1, y1), Image.ANTIALIAS)
        output = BytesIO()
        image.save(output, "PNG")
        data = output.getvalue()

    response = make_response(data)
    response.headers["content-type"] = mimetypes.guess_type(path)
    return response


@app.route("/feed/")
def global_feed():
    return feed()


@app.route("/sitemap.xml")
def sitemap():
    today = datetime.date.today()
    recently = datetime.date(year=today.year, month=today.month, day=1)
    response = make_response(
        render_template(
            "sitemap.xml", pages=get_pages(), today=today, recently=recently
        )
    )
    response.headers["Content-Type"] = "text/xml"
    return response


@app.route("/favicon.ico")
def favicon():
    return ""


@app.route("/403.html")
def error403():
    return render_template("403.html", page=dict(title="Fordidden"))


@app.route("/404.html")
def error404():
    return render_template("404.html", page=dict(title="Not found"))


@app.route("/500.html")
def error500():
    return render_template("500.html")


@app.errorhandler(404)
def page_not_found(error):
    page = {"title": "Page not found"}
    return render_template("404.html", page=page), 404

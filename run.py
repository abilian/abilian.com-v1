#!/usr/bin/env python
# coding=utf-8

from argh import ArghParser
from website.app import app, setup_app

setup_app(app)


def serve(server="127.0.0.1", port=5000, debug=True):
    """ Serves this site.
  """
    if not debug:
        import logging

        file_handler = logging.FileHandler("error.log")
        file_handler.setLevel(logging.WARNING)
        app.logger.addHandler(file_handler)

    # asset_manager.config['ASSETS_DEBUG'] = debug
    app.debug = debug
    app.run(host=server, port=port, debug=debug)


def prod():
    serve(debug=False)


if __name__ == "__main__":
    parser = ArghParser()
    parser.add_commands([serve, prod])
    parser.dispatch()

else:
    # App has been called from a WSGI server.
    import logging

    file_handler = logging.FileHandler("error.log")
    file_handler.setLevel(logging.WARNING)
    app.logger.addHandler(file_handler)
    # app.debug = True

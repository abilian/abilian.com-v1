# -*- coding: utf-8 -*-
"""Create an application instance."""

# from app.main import create_app
#
# app = create_app()


from website.app import app, setup_app

setup_app(app)

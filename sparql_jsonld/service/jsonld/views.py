from flask import Blueprint, request, render_template_string, abort, send_file, redirect, current_app, send_from_directory, Response, stream_with_context
import logging,collections
import requests
from io import StringIO
import os

prefix = 'agraph_service_jsonld'

logger = logging.getLogger('webapp')

ui = Blueprint(prefix+'_ui',__name__)

@ui.route('/')
def index():
   pass

assets = Blueprint(prefix+'_assets',__name__)
@assets.route('/<path:path>')
def send_asset(path):
   dir = current_app.config.get('ASSETS')
   if dir is None:
      dir = __file__[:__file__.rfind('/')] + '/assets/'
   return send_from_directory(dir, path)

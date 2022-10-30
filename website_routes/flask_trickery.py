from flask import wrappers

from utils.variables import Global

app = Global.app

@app.after_request
def add_header(response: wrappers.Response):
    # only cache static files (js/css)
    # otherwise chrome doesn't like it.
    # max-age = 1 day (60*60*24)
    ct = response.content_type
    if "javascript" in ct or "css" in ct:
        response.headers['Cache-Control'] = 'public, max-age=86400'

    return response
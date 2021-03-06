import os
from flask import Flask, render_template, request
import requests
from flask_wtf import Form
import wtforms as wtf
from wtforms import validators as val
import re
import sys
import urllib

IS_PROD = os.environ.get('DYNO') != None # signals Heroku environment

app = Flask(__name__)
app.debug = not IS_PROD

GEO_IP_CACHE = {}

def get_geo():
    ip = request.access_route[0]
    result = GEO_IP_CACHE.get(ip)
    if not result:
        if IS_PROD:
            try:
                result = requests.get('http://ipinfo.io/%s/json' % ip).json()
            except Exception as e:
                result = dict(postal=94110)
        else:
            result = dict(postal=94110)
        GEO_IP_CACHE[ip] = result
    return result


ZIP_RX = re.compile(r'^\d{5}(?:[-\s]\d{4})?$')
def validate_zip(form, field):
    v = (unicode(field.data) or '').strip()
    if not ZIP_RX.match(v):
        raise val.ValidationError('Please enter a valid zip code (e.g., 90210)')


class SearchForm(Form):
    make = wtf.StringField()
    zip = wtf.StringField(validators=[val.DataRequired(), validate_zip])
    distance = wtf.SelectField(choices=[
                                        ('5', '5 miles'),
                                        ('25', '25 miles'),
                                        ('50', '50 miles'),
                                        ('100', '100 miles'),
                                        ],
                               default='25')

@app.route('/')
def index_view():
    form = SearchForm(request.args, csrf_enabled=False)
    if not form.zip.data:
        form.zip.data = get_geo().get('postal')
    valid_form = form.validate()
    return render_template('index.html', form=form, valid_form=valid_form)


@app.template_filter()
def url_encode(url):
    return urllib.quote_plus(url)


if __name__ == '__main__':
    if len(sys.argv) >= 2 and sys.argv[1] == 'shell':
        import code
        code.interact("\n>>> %s shell. Try dir()" % ('PRODUCTION' if IS_PROD else 'localdev'), local=locals())
    else:
        app.run(port=8080)

from flask import Flask, request, make_response, jsonify
from flask_restful import reqparse, abort, Api, Resource
from flask_wtf import FlaskForm
from flask import redirect
from flask_wtf.csrf import CsrfProtect
from meme_resources import *


app = Flask(__name__)
app.config['SECRET_KEY'] = 'butterfly'
csfr = CsrfProtect()
api = Api(app)
# url_api = 'https://iosif-rest-api.herokuapp.com/api'

if __name__ == '__main__':
    api.add_resource(TranslateImageResource, '/api/v1/translate_image')
    app.run(host='0.0.0.0', port=os.environ.get("PORT", 5000))
    # app.run(port=8080, host='127.0.0.1')

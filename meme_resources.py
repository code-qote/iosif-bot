from flask_restful import reqparse, abort, Api, Resource
from flask import jsonify
import cv2
import csv
import pytesseract
from pytesseract.pytesseract import Output
import asyncio
import aiohttp
from requests import get
from random import randint
from googletrans import Translator
import os
import numpy as np
import string

# pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
pytesseract.pytesseract.tesseract_cmd = "/app/vendor/tesseract-ocr/bin/tesseract"

parser_image = reqparse.RequestParser()
parser_image.add_argument('image_url', required=True)
parser_image.add_argument('language', required=True)

parser_text = reqparse.RequestParser()
parser_text.add_argument('text', required=True)
parser_text.add_argument('language', required=True)

def get_text_from_image(image_path):
    image = cv2.imread(image_path)
    gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    image = cv2.threshold(
        gray_image, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)[1]
    kernel = np.ones((2, 2), np.uint8)
    dilated_image = cv2.dilate(image, kernel, iterations=2)
    dilated_image = cv2.morphologyEx(dilated_image, cv2.MORPH_OPEN, kernel)
    h, w = image.shape
    parse_text = []
    word_list = []
    last_word = ''
    dilated_details = pytesseract.image_to_data(dilated_image, output_type=Output.DICT, lang='eng')
    default_details = pytesseract.image_to_data(
        image, output_type=Output.DICT, lang='eng')
    if len(dilated_details) > len(default_details):
        details = dilated_details
    else:
        details = default_details
    for word in details['text']:
        if word != '':
            parse_text.append(word)
    for i in range(len(parse_text)):
        if parse_text[i][0] in string.ascii_uppercase and i != 0 and parse_text[i - 1][-1] not in '.:?!':
            parse_text[i - 1] += '.'
    # print(parse_text)
    return parse_text

class TranslateImageResource(Resource):
    def get(self):
        args = parser_image.parse_args()
        image_url = args['image_url']
        language = args['language']
        response = get(image_url)
        if response.status_code == 200:
            filename = str(randint(10000, 99999)) + '.jpg'
            with open(filename, 'wb') as file:
                file.write(response.content)
            text = ' '.join(get_text_from_image(filename))
            translator = Translator(service_urls=[
                                    'translate.google.ru',
                                    'translate.google.com',
                                ])
            translation = translator.translate(text, dest=language)
            os.remove(filename)
            return translation.text
        else:
            return 'There was a problem, try again.'

class TranslateText(Resource):
    def get(self):
        args = parser_image.parse_args()
        text = args['text']
        language = args['language']
        translator = Translator(service_urls=[
            'translate.google.ru',
            'translate.google.com',
        ])
        translation = translator.translate(text, dest=language)
        return translation.text

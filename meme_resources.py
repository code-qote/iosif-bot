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

# pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
pytesseract.pytesseract.tesseract_cmd = ".apt/usr/include/tesseract"

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
    image = cv2.dilate(image, kernel, iterations=2)
    image = cv2.morphologyEx(image, cv2.MORPH_OPEN, kernel)
    h, w = image.shape
    cv2.rectangle(image, (0, h - 30), (round(w * 0.25), h), (0, 0, 0), -1)
    parse_text = []
    word_list = []
    last_word = ''
    details = pytesseract.image_to_data(image, output_type=Output.DICT, lang='eng')
    for word in details['text']:
        if word != '':
            word_list.append(word)
            last_word = word
        if (last_word != '' and word == '') or (word == details['text'][-1]):
            parse_text.append(word_list)
            word_list = []
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
            text = ' '.join([' '.join(i) for i in get_text_from_image(filename)])
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

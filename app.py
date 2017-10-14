# -*- coding: utf-8 -*-
"""
Start video conversations from Twist by just typing `/appear room-name`
"""
import os

from googletrans import Translator
from flask import Flask
from flask import jsonify
from flask import request
from PIL import Image
from io import BytesIO
import requests
import json
import http.client, urllib.request, urllib.parse, urllib.error, base64, requests, time


app = Flask(__name__)

def translation(message,langCode):
    if(langCode != "en"):
        try:
            trans = Translator()
            message = trans.translate(message, dest=langCode).text
        except Exception:
            message+=("\n The language code is not recognised!")

    return message


def ms_integration_tr(data):

    ms_subscription_key = '6d70c2eb9d0e466ba6b5275932e7e70f' #Microsoft Api
    ms_uri_base = 'https://westcentralus.api.cognitive.microsoft.com'
    ms_requestHeaders = {
    # Request headers.
    # Another valid content type is "application/octet-stream".
    'Content-Type': 'application/octet-stream',
    'Ocp-Apim-Subscription-Key': ms_subscription_key,
    }

    message =""

    try:

        img_data = thumbnail(data['comment']['attachments'][0]['image'], (3200, 3200))

        try:
            # This operation requrires two REST API calls. One to submit the image for processing,
            # the other to retrieve the text found in the image. 
            #
            # This executes the first REST API call and gets the response.
            response = requests.request('POST', ms_uri_base + '/vision/v1.0/RecognizeText', data=img_data, headers=ms_requestHeaders, params={'handwriting' : 'false'})

            # Success is indicated by a status of 202.
            if response.status_code != 202:
                # if the first REST API call was not successful, display JSON data and exit.
                parsed = json.loads(response.text)
                print ("Error:")
                print (json.dumps(parsed, sort_keys=True, indent=2))
                if parsed['error']['code'] == 'InvalidImageDimension':
                    exit()

            # The 'Operation-Location' in the response contains the URI to retrieve the recognized text.
            operationLocation = response.headers['Operation-Location']

            # Note: The response may not be immediately available. Handwriting recognition is an
            # async operation that can take a variable amount of time depending on the length
            # of the text you want to recognize. You may need to wait or retry this GET operation.

            #print('\nHandwritten text submitted. Waiting 10 seconds to retrieve the recognized text.\n')
            time.sleep(10)

            # Execute the second REST API call and get the response.
            response = requests.request('GET', operationLocation, json=None, data=None, headers=ms_requestHeaders, params=None)

            # 'data' contains the JSON data. The following formats the JSON data for display.
            parsed = json.loads(response.text)

            # Generate the text of the message
            for line in parsed['recognitionResult']['lines']:
                message = message + line['text'] + "\n"
            # If empty message, can't read
            if message == "":
                message = "Image can't be read"


        except Exception as e:
            print('Error:')
            print(e)

    except IndexError:
        message = " No image"


    return message


def ms_integration_ocr(data):

    ms_subscription_key = 'd36ad8a50c0943bbbe839ff5ca6eb1bb' #Microsoft Api
    ms_requestHeaders = {
    # Request headers.
    # Another valid content type is "application/octet-stream".
    'Content-Type': 'application/octet-stream',
    'Ocp-Apim-Subscription-Key': ms_subscription_key,
    }
    ms_params = urllib.parse.urlencode({
    # Request parameters. The language setting "unk" means automatically detect the language.
    'language': 'unk',
    'detectOrientation ': 'true',
    })

    message = ""

    try:

        img_data = thumbnail(data['comment']['attachments'][0]['image'], (3200, 3200))

        try:
            # This operation requrires two REST API calls. One to submit the image for processing,
            # the other to retrieve the text found in the image. 
            #
            # This executes the first REST API call and gets the response.

            conn = http.client.HTTPSConnection('westcentralus.api.cognitive.microsoft.com')
            conn.request("POST", '/vision/v1.0/ocr?%s' % ms_params, img_data, ms_requestHeaders)
            response = conn.getresponse()
            
            data = response.read()
            parsed = json.loads(data)
            
            print ("Response:")
            print (json.dumps(parsed, sort_keys=True, indent=2))

            # Generate the text of the message
            for region in parsed['regions']:
                for line in region['lines']:
                    for word in line['words']:
                        message = message + word['text'] + " "
                    message = message + "\n"
                message = message + "\n\n"

            # If empty message, can't read
            if message == "":
                message = "Image can't be read"

            conn.close()
        except Exception as e:
            print('Error:')
            print(e)

    except IndexError:
        message = " No image"


    return message

def thumbnail(image_url, size):
    img = Image.open(BytesIO(requests.get(image_url).content))
    img.thumbnail(size)
    img.save('tmp', "JPEG")
    with open('tmp', 'rb') as f:
        img_data = f.read()
    return img_data

@app.route('/transcribe/incoming', methods=['POST'])
def transcribe():

    event_type = request.form['event_type']

    if event_type == 'ping':
        return jsonify({'content': 'pong'})
    else:
        command_argument = request.form['command_argument']
        message = ms_integration_tr(requests.get('https://api.twistapp.com/api/v2/comments/getone', 
            headers={'Authorization': 'Bearer oauth2:4754b6fb12f8557221b9975701ca2f7b0432a23d'}, 
            params={'id': request.form['comment_id']}).json(), {'handwriting' : 'true'})  # obtenir el missatge per extreure la img i transcripció

    message = translation(message,command_argument)

    return jsonify({
        'content': message,
    })


@app.route('/ocr/incoming', methods = ['POST'])
def ocr():
    event_type = request.form['event_type']

    if event_type == 'ping':
        return jsonify({'content': 'pong'})
    else:
        command_argument = request.form['command_argument']
        message = ms_integration_ocr(requests.get('https://api.twistapp.com/api/v2/comments/getone', 
            headers={'Authorization': 'Bearer oauth2:4754b6fb12f8557221b9975701ca2f7b0432a23d'},
            params={'id': request.form['comment_id']}).json())  # obtenir el missatge per extreure la img i OCR

    message = translation(message, command_argument)

    return jsonify({
        'content': message,
    })


@app.route('/transcribe/config')
def transcribe_conf():
    """
    URL d'inici = https://twist-transcribe.herokuapp.com/?install_id=30078&user_id=57010&post_data_url=https%3A%2F%2Ftwistapp.com%2Fapi%2Fv2%2Fintegration_incoming%2Fpost_data%3Finstall_id%3D30078%26install_token%3D30078_40c17672a965cca1dae424de0baac187&user_name=Pau+C.

    """
    user_name = request.args.get('user_name')
    return "<h1>Welcome to this integration</h1>" + "<p>"+ user_name +"</p>"

@app.route('/ocr/config')
def ocr_conf():
    """
    URL d'inici = https://twist-transcribe.herokuapp.com/?install_id=30078&user_id=57010&post_data_url=https%3A%2F%2Ftwistapp.com%2Fapi%2Fv2%2Fintegration_incoming%2Fpost_data%3Finstall_id%3D30078%26install_token%3D30078_40c17672a965cca1dae424de0baac187&user_name=Pau+C.

    """
    user_name = request.args.get('user_name')
    return "<h1>Welcome to this integration</h1>" + "<p>"+ user_name +"</p>"

@app.route('/', methods=['GET'])
def index():
    return "<h1>Welcome to this integration</h1>"


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)

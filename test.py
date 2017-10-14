# -*- coding: utf-8 -*-
"""
Start video conversations from Twist by just typing `/appear room-name`
"""
import os

from flask import Flask
from flask import jsonify
from flask import request
import requests
import json
import http.client, urllib.request, urllib.parse, urllib.error, base64, requests, time

app = Flask(__name__)

subscription_key = '6d70c2eb9d0e466ba6b5275932e7e70f' #Microsoft
uri_base = 'https://westcentralus.api.cognitive.microsoft.com'
requestHeaders = {
    # Request headers.
    # Another valid content type is "application/octet-stream".
    'Content-Type': 'application/json',
    'Ocp-Apim-Subscription-Key': subscription_key,
}



@app.route('/transcribe/incoming', methods=['POST'])
def incoming():
    # For printed text, set "handwriting" to false.
    params = {'handwriting' : 'true'}

    event_type = request.form['event_type']

    if event_type == 'ping':
        return jsonify({'content': 'pong'})
    else:
        content = request.form['content']
        command = request.form['command']
        command_argument = request.form['command_argument']

        print("comment_id:" + request.form['comment_id'])

        #if (len(request.form['attachments'])>0):
        #image_url = image_url + "hi ha algo"
        appear_url =  'https://appear.in/%s' % command_argument

        header = {'Authorization': 'Bearer oauth2:4754b6fb12f8557221b9975701ca2f7b0432a23d'} 
        url = 'https://api.twistapp.com/api/v2/comments/getone'
        comment_id = {'id': request.form['comment_id']}

        r = requests.get(url, headers=header, params=comment_id)

        message = "Transcribed text"
        data = r.json()
        print(r.text)
        image_url = data['comment']['attachments'][0]['image']
        print(image_url)
        
        # The URL of a JPEG image containing handwritten text.
        body = {'url' : image_url}

        try:
            # This operation requrires two REST API calls. One to submit the image for processing,
            # the other to retrieve the text found in the image. 
            #
            # This executes the first REST API call and gets the response.
            response = requests.request('POST', uri_base + '/vision/v1.0/RecognizeText', json=body, data=None, headers=requestHeaders, params=params)

            # Success is indicated by a status of 202.
            if response.status_code != 202:
                # if the first REST API call was not successful, display JSON data and exit.
                parsed = json.loads(response.text)
                print ("Error:")
                print (json.dumps(parsed, sort_keys=True, indent=2))
                exit()

            # The 'Operation-Location' in the response contains the URI to retrieve the recognized text.
            operationLocation = response.headers['Operation-Location']

            # Note: The response may not be immediately available. Handwriting recognition is an
            # async operation that can take a variable amount of time depending on the length
            # of the text you want to recognize. You may need to wait or retry this GET operation.

            print('\nHandwritten text submitted. Waiting 10 seconds to retrieve the recognized text.\n')
            time.sleep(10)

            # Execute the second REST API call and get the response.
            response = requests.request('GET', operationLocation, json=None, data=None, headers=requestHeaders, params=None)

            # 'data' contains the JSON data. The following formats the JSON data for display.
            parsed = json.loads(response.text)
            print ("Response:")
            message = json.dumps(parsed, sort_keys=True, indent=2)
            content = content.replace(u'%s %s' % (command, command_argument),
                                  u'%s %s' % (message, image_url))
            print (message)

            return jsonify({
            'content': content,
            })

        except Exception as e:
            print('Error:')
            print(e)
        

        return jsonify({
            'content': content,
        })

@app.route('/config/')
def conf():
    """
    URL d'inici = https://twist-transcribe.herokuapp.com/?install_id=30078&user_id=57010&post_data_url=https%3A%2F%2Ftwistapp.com%2Fapi%2Fv2%2Fintegration_incoming%2Fpost_data%3Finstall_id%3D30078%26install_token%3D30078_40c17672a965cca1dae424de0baac187&user_name=Pau+C.

    """

    install = request.args.get('install_id')
    user_id = request.args.get('user_id')
    user_name = request.args.get('user_name')
    return "<h1>Welcome to this integration</h1>" + "<p>"+ install +"</p>"

@app.route('/', methods=['GET'])
def index():
    return "<h1>Welcome to this integration</h1>"


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)

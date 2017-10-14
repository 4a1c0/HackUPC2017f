# -*- coding: utf-8 -*-
"""
Start video conversations from Twist by just typing `/appear room-name`
"""
import os

from flask import Flask
from flask import jsonify
from flask import request

app = Flask(__name__)


@app.route('/applet_appear/incoming', methods=['POST'])
def incoming():
    event_type = request.form['event_type']

    if event_type == 'ping':
        return jsonify({'content': 'pong'})
    else:
        content = request.form['content']
        command = request.form['command']
        command_argument = request.form['command_argument']

        appear_url =  'https://appear.in/%s' % command_argument

        content = content.replace(u'%s %s' % (command, command_argument),
                                  u'📹 [%s](%s)' % (command_argument, appear_url))

        return jsonify({
            'content': content,
        })
@app.route('/', methods=['GET'])
def conf():
    return "<h1>Welcome to this integration<h1>"

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
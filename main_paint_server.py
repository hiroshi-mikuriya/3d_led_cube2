# coding: UTF-8
import os.path
import time
import threading
import json
from Queue import Queue
from libled.led_run_loop import LedRunLoop
from flask import Flask, render_template
from flask import request
from os import listdir
from os.path import isfile, join
from libled.util.common_util import *
from werkzeug import ImmutableDict
from libled.led_cube import *
from libled.util.color import Color
from libled.util.paint_manager import PaintManager

class FlaskWithHamlish(Flask):
    jinja_options = ImmutableDict(
        extensions=['jinja2.ext.autoescape', 'jinja2.ext.with_', 'hamlish_jinja.HamlishExtension']
    )
app = FlaskWithHamlish(__name__)

q = Queue()
q.put('show:' + json.dumps({'orders': [{'id':'object-painting', 'lifetime':0}]}))

@app.route('/')
def index():
    return render_template('index.haml')

@app.route('/api/filter')
def api_filter():
    orders = {'orders': [
        {'id':'filter-wakame'},
        {'id':'object-painting', 'lifetime':0}
    ]}
    q.put('show:' + json.dumps(orders))


@app.route('/api/led', methods=['POST'])
def api_led():
    x = request.form.get('x')
    if x is None:
        for x in range(16):
            datalist_id = "led[{0}][]".format(x)
            datalist = request.form.getlist(datalist_id)
            for y in range(32):
                PaintManager.get_instance().set_color(x, y, Color.int_to_color(int(datalist[y], 16)))
    else:
        y = request.form.get('y')
        color = request.form.get('color')
        PaintManager.get_instance().set_color(int(x), int(y), Color.int_to_color(int(color, 16)))
    return ""


@app.route('/api/abort', methods=['POST'])
def abort():
    q.put('abort')
    return ""

class LedPaintHttpServer(LedRunLoop):

    def __init__(self):
        super(LedPaintHttpServer, self).__init__()

    def on_exception_at_runloop(self, exception):
        return LedRunLoop.EXIT

    def read_data(self):
        print("waiting data.")
        while True:
            if self.aborted:
                break

            if q.empty():
                time.sleep(0.1)
            else:
                return q.get()


class FlaskThread(threading.Thread):

    def __init__(self, app, host='0.0.0.0', port=5301):
        super(FlaskThread, self).__init__()
        self.app = app
        self.host = host
        self.port = port
    
    def run(self):
        self.app.run(
            debug=False,
            host=self.host,
            port=int(self.port)
        )
        

flask = FlaskThread(app)
flask.daemon = True
flask.start()

LedPaintHttpServer().run()

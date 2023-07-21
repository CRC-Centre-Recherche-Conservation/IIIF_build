import http.server
import os

class MyHttpRequestHandler(http.server.SimpleHTTPRequestHandler):
    def _set_headers(self):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()

    def do_HEAD(self):
        self._set_headers()

    def do_GET(self):
        # self._set_headers()

        if self.path == '/':
            self.path = 'output/'

        for file in os.listdir('output/'):
            if self.path == f'/{file}':
                self.path = f'output/{file}'

        return http.server.SimpleHTTPRequestHandler.do_GET(self)
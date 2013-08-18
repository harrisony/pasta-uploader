import requests
from bs4 import BeautifulSoup
import re

class PASTA(object):

    def __init__(self):
        self.s = requests.Session()
        self.u = 'http://pasta.ug.it.usyd.edu.au:9080/~%s/'
        self.logged_in = False

    def _strip_submit(self, text):
        return re.match(r"submitAssessment\('(.*?)'\);", text).groups()[0]

    def login(self, unikey, password, course):
        self.u = self.u % course
        payload = {'unikey': unikey,
                   'password': password,
                   'Submit': ''}
        r = self.s.post(self.u + '/login/', data=payload)
        if r.url.endswith('/login'):
            raise Exception('login failed')
        self.logged_in = True

    def list_tasks(self):
        if not self.logged_in:
            raise Exception('you need to be logged in')
        r = self.s.get(self.u + '/home/')
        soup = BeautifulSoup(r.text)
        return [(task.a.string, self._strip_submit(task.button['onclick'])) for task in soup.findAll('tr')]

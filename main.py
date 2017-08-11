#!/usr/bin/env python3
import code

import os
import requests
from bs4 import BeautifulSoup
import re
import getpass
import argparse


# props to https://gist.github.com/brantfaircloth/1443543
class FullPaths(argparse.Action):
    """Expand user- and relative-paths"""
    def __call__(self, parser, namespace, values, option_string=None):
        setattr(namespace, self.dest, os.path.abspath(os.path.expanduser(values)))



class PASTA(object):
    # since every ~man~ course and their dog has it's own instance
    INFO3504 = 'http://soit-app-pro-9.ucc.usyd.edu.au:8080/PASTA/'
    def __init__(self, **kwargs):
        self.s = requests.Session()
        self.base_url = kwargs['site']
        self.logged_in = False
        # for debuggging onyl
        self._soup = None

        self.login(kwargs['username'], kwargs['password'])

    def _strip_submit(self, text):
        return re.match(r"submitAssessment\('(.*?)'\);", text).groups()[0]

    def login(self, unikey=None, password=None):
        payload = {'unikey': unikey,
                   'password': password,
                   'Submit': ''}
        r = self.s.post(self.base_url + '/login/', data=payload)
        if r.url.endswith('/login'):
            raise Exception('login failed')
        self.logged_in = True



    def retrieve_tasks(self):
        ##TODO: something something, ensure you're logged in
        r = self.s.get(self.base_url + '/home/')
        self._soup = BeautifulSoup(r.text)
        sections_soup = self._soup.findAll('div', class_='section')
        tasks = []

        for section in sections_soup:
            for task in section.findAll('div', class_='assessment-box'):
                task_dict = {'section': section.h2.text, 'name': task.a.text, 'url': task.a['href'], '_html': task}

                ## Infoboxes
                for iboxitem in task.find_all(class_='ip-item'):
                    # the infobox text has all this junk like \t\t\t\t\\t\t\t\t\\t\t\\n\n\n\n\n\n, remove it without
                    #  the use of a regular expression with something equally ugly,
                    k,v = tuple(" ".join(splitted) for splitted in (map(str.split, iboxitem.stripped_strings)))
                    task_dict[k.lower().strip(':')] = v

                ## submitAssessment
                submit_assessment_details = re.match(r"submitAssessment\('(.*)', '(.*)',.*\);", task.find(class_='button-panel').button['onclick']).groups()
                task_dict.update(dict(zip(('p_id', 'p_due'), submit_assessment_details)))


                tasks.append(task_dict)


        return tasks


    def submit_submission(self, task_id, path="pasta_submission.zip"):
        r = self.s.post(self.base_url + '/home/', files={"file": open(path, 'rb')}, data={'assessment' : task_id, '_groupSubmission': 'on'})
        print("Submitting {} as {}".format(path, task_id))


def shell(args):
    ed = PASTA(**vars(args))
    code.interact(local=locals())

def tasks(args):
    pasta = PASTA(**vars(args))
    for task in pasta.retrieve_tasks():
        print("{p_id:<3} {name:} (Due: {due:})".format(**task))  ## div.part-title.a

def submit(args):
    pasta = PASTA(**vars(args))
    pasta.submit_submission(args.task_id, args.path)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(prog='pasta-uploader')
    parser.add_argument("-u", "--username", default=None)
    parser.add_argument("-p", "--password", default=None)
    parser.add_argument("-s", "--site", default=PASTA.INFO3504)


    subparsers = parser.add_subparsers(dest="command", help="commands")
    subparsers.required = True

    p_shell = subparsers.add_parser("shell", help="Drop to a shell")
    p_shell.set_defaults(func=shell)


    a_shell = subparsers.add_parser("list", help="View assignments")
    a_shell.set_defaults(func=tasks)

    s = subparsers.add_parser("submit", help="Are you crazy?")
    s.set_defaults(func=submit)
    s.add_argument('task_id' , action='store')
    s.add_argument('--path' , action=FullPaths, default=os.path.join(os.getcwd(), 'pasta_submission.zip'))

    args = parser.parse_args()

    netrc = requests.utils.get_netrc_auth(args.site)

    if netrc:
        args.username, args.password = netrc
    elif args.username is None and args.password is None:
        args.username = input("Unikey: ")
        args.password = getpass.getpass("Password: ")
    elif args.username and args.password is None:
        args.password = getpass.getpass("Password: ")
    elif args.username is None and args.password:
        parser.error("if you're going to give me a password, you'll need to give me a username")

    args.func(args)


# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4

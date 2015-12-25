#!/usr/bin/env python
#encoding:utf-8
#author:jhat
#email:cpf624@126.com
#date:2012-11-13
#vim: tabstop=4 shiftwidth=4 softtabstop=4
#describe:

import os,threading
from urllib2 import urlopen,HTTPError,URLError
import json

REPO = 'http://repo1.maven.org/maven2/'
PID = '47'

def download_file(f):
    if os.system('wget -xcNnH ' + REPO + f) == 0:    
        success.write(f + '\n')
        success.flush()
    else:
        fail.write(f + '\n')
        fail.flush()

def download(pid,start=0,rows=1000):
    try:
        u = urlopen('http://search.maven.org/solrsearch/select?q=parentId:"%s"&start=%d&rows=%d&core=filelisting&wt=json' % (pid,start,rows))
        j = json.load(u)
        u.close()
        response = j['response']

        numFound = response['numFound']
        if numFound > rows:
            download(pid, rows + 1, rows)

        docs = response['docs']
        dt = ft = []
        for d in docs:
            t = d['type']
            if t == 1:
                ft.append(threading.Thread(target = download_file, args = (d['path'],)))
            elif t == 0:
                dt.append(threading.Thread(target = download, args = (d['id'], start, rows)))
        
        for t in ft:
            t.ident or t.start()
        for t in ft:
            t.join()
        
        for t in dt:
            t.ident or t.start()
        for t in dt:
            t.join()
    except:
        fail.write(pid + ' %s\n' % e.code or e.reson or e.message or 'E')
        fail.flush()


if __name__ == '__main__':
    success = open('success.log', 'w')
    fail = open('fail.log', 'w')
    download(PID)
    success.close()
    fail.close()

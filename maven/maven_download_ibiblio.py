#!/usr/bin/env python
#encoding:utf-8
#author:jhat
#email:cpf624@126.com
#date:2012-11-13
#vim: tabstop=4 shiftwidth=4 softtabstop=4
#describe:

import os,threading
from sgmllib import SGMLParser
from urllib2 import urlopen

class IndexParser(SGMLParser):
   
    def reset(self):
        SGMLParser.reset(self)
        self.directory_list = False
        self.directories = []
        self.files = []

    def start_div(self,attrs):
        if not self.directory_list:
            for k,v in attrs:
                if k == 'id' and v == 'directory-list':
                    self.directory_list = True
                    break

    def start_a(self,attrs):
        if self.directory_list:
            for href,url in attrs:
                if url != '../':
                    if url[len(url)-1] == '/':
                        self.directories.append(url)
                    else:
                        self.files.append(url)

def download_file(f):
    if os.system('wget -xcNnH ' + f) == 0:    
        success.write(f + '\n')
        success.flush()
    else:
        fail.write(f + '\n')
        fail.flush()

def download(murl,iurl):
    p = IndexParser()
    try:
        u = urlopen(iurl)
        p.feed(u.read())
        u.close()
        p.close()
        
        ts = []
        for f in p.files:
            ts.append(threading.Thread(target = download_file, args = (murl + f,)))
        for t in ts:
            t.start()
        for t in ts:
            t.join()
        
        ts = []
        for d in p.directories:
            ts.append(threading.Thread(target = download, args = (murl + d, iurl + d)))
        for t in ts:
            t.start()
        for t in ts:
            t.join()
    except:
        fail.write('F ' + iurl + '\n')
        fail.flush()


if __name__ == '__main__':
    success = open('success.log','w')
    fail = open('fail.log','w')
    download('http://repo1.maven.org/maven2/','http://mirrors.ibiblio.org/maven2/')
    success.close()
    fail.close()

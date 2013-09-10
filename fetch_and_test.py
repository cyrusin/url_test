#!/usr/bin/env python
# -*- coding:utf-8 -*-
# filename: fetch_and_test.py
# @author: lishuai
# @time: 2013-08-26
"""
Using multi-threading to fetch and test 'm.sohu.com'

"""
import Queue
import threading
import urllib2
from urlparse import urlparse, urljoin
from time import time, strftime, gmtime, timezone
import logging

from bs4 import BeautifulSoup

import settings # hosts will be fetched

# config of log
logging.basicConfig(level=logging.DEBUG,
        format="%(asctime)s %(filename)s %(message)s",
        datefmt="%a, %d %b %Y %H:%M:%S",
        filename="url.log",
        filemode='a')

# hosts=["m.sohu.com",...]
hosts = settings.hosts

# queue contains url name
url_queue = Queue.Queue()
# queue contains page chunk
chunk_queue = Queue.Queue()

# add url:1 to this dict{url:1|0} if it is accessed
url_done = dict()


class GrabThread(threading.Thread):
    """This is used to grab url."""
    def __init__(self, url_queue, chunk_queue):
        threading.Thread.__init__(self)
        self.url_queue = url_queue
        self.chunk_queue = chunk_queue

    def run(self):
        while True:
            #get host from queue
            url = self.url_queue.get()

            #grabs urls of hosts and the grabs chunk of webpage
            if not url_done.get(url, 0) and "sohu.com" in url:
                try:
                    response = urllib2.urlopen(url, timeout=5)
                except urllib2.HTTPError, e:
                    print strftime("%Y-%m-%d, %T", gmtime(time()-timezone)), \
                            url, \
                            e.code
                    logging.info(''.join([url, ' ', str(e.code)]))
                except urllib2.URLError, e:
                    print strftime("%Y-%m-%d, %T", gmtime(time()-timezone)), \
                            url, \
                            "url error"
                    logging.info(''.join([url, ' ', "url error"]))
                except Exception, e:
                    print strftime("%Y-%m-%d, %T", gmtime(time()-timezone)), \
                            url,  \
                            "timeout"
                    logging.info(''.join([url, ' ', "timeout"]))
                else:
                    print strftime("%Y-%m-%d, %T", gmtime(time()-timezone)), \
                            url, \
                            "200", \
                            "ok"
                    url_done[url] = 1
                    try:
                        chunk = response.read()
                    except Exception, e:
                        print strftime("%Y-%m-%d, %T", gmtime(time()-timezone)), \
                                url, \
                                "timeout"
                    else:
                        self.chunk_queue.put(chunk)

            self.url_queue.task_done


class ChunkThread(threading.Thread):
    """This is used to analysize web page."""
    def __init__(self, url_queue, chunk_queue):
        threading.Thread.__init__(self)
        self.url_queue = url_queue
        self.chunk_queue = chunk_queue

    def run(self):
        while True:
            chunk = self.chunk_queue.get()

            soup = BeautifulSoup(chunk)
            links = soup.findAll('a')
            for link in links:
                if 'href' in dict(link.attrs):
                    url = urljoin(hosts[0], link["href"])
                    if url.find("'") != -1:
                        continue
                    url = url.split('#')[0]
                    url = url.split('"')[0]
                    self.url_queue.put(url)

            self.chunk_queue.task_done()


#start = time.time()
def main():
    for i in range(5):
        t = GrabThread(url_queue, chunk_queue)
        t.setDaemon(True)
        t.start()

    for host in hosts:
        url_queue.put(host)

    for i in range(5):
        dt = ChunkThread(url_queue, chunk_queue)
        dt.setDaemon(True)
        dt.start()

    url_queue.join()
    chunk_queue.join()

if __name__ == "__main__":
    main()

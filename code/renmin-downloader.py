import queue
import sys
import os
import argparse
import time
import math
from urllib.request import urlopen, FancyURLopener
import re
import threading
import urllib.error
import urllib3
import requests
from urllib.request import urlretrieve

'''
Download pdfs required for HLTCOE Renmin OCR/NER Collection

2020-03-13
Run with -h flag for usage information.
'''

DEFAULT_NUM_THREADS = 2
DEFAULT_OUTPUT_DIR = '.'
DEFAULT_MAX_NUM_PAGES = 30
DEFAULT_THROTTLE = 5
DEFAULT_URL_TRIES = 3

class ThreadedDownload():
    
    class Downloader(threading.Thread):
        def __init__(self, queue, report):
            threading.Thread.__init__(self)
            self.queue = queue
            self.report = report
        
        def run(self):
            while not self.queue.empty():
                url = self.queue.get()
                
                response = url.download()
                if response == False and url.url_tried < url.url_tries:
                    self.queue.put(url)
                elif response == False and url.url_tried == url.url_tries:
                    self.report['failure'].append(url)
                elif response == True:
                    self.report['success'].append(url)
                
                self.queue.task_done()
    
    
    class URLTarget():
        def __init__(self, url, destination, url_tries, throttle):
            self.url = url
            self.destination = destination
            self.url_tries = url_tries
            self.throttle = throttle
            self.url_tried = 0
            self.success = False
            self.error = None
        
        def download(self):
            self.url_tried += 1
            
            try:
                # Has this file already been downloaded?
                if os.path.exists(self.destination):
                    print(f'...{self.destination} exists, skipping')
                    self.success = True
                    return self.success
                else:
                    print(f'download try {self.url_tried},  {self.url} to {self.destination}')

                parentdir = os.path.dirname(self.destination)
                if not os.path.exists(parentdir):
                    os.makedirs(parentdir)

                urlretrieve(self.url, filename=self.destination)
                self.success = True
                
                time.sleep(self.throttle)
                
            except urllib.error.URLError as error:
                self.error = "DOWNLOAD ERROR: " + str(error.reason)
                
            return self.success
        
        def __str__(self):
            return f'URLTarget (URL: {self.url}, Success: {self.success}, Error: {self.error})'
    
    
    def __init__(self, urls, descs, destination, thread_count, url_tries, throttle):       
        self.queue = queue.Queue(0) # Infinite sized queue
        self.report = {'success': [], 'failure': []}
        self.threads = []
        
        self.destination = destination
        self.thread_count = thread_count
        self.url_tries = url_tries
        self.throttle = throttle
        
        for idx, url in enumerate(urls):
            outUrlPath = os.path.join(self.destination, descs[idx])
            self.queue.put(ThreadedDownload.URLTarget(url, outUrlPath, url_tries, throttle))
  
    
    def run(self):
        for i in range(self.thread_count):
            thread = ThreadedDownload.Downloader(self.queue, self.report)
            thread.start()
            self.threads.append(thread)
        if self.queue.qsize() > 0:
            self.queue.join()

                   
def main(args):
    startTime = time.clock()

    years = [2018]
    months = [6]
    days = [1,2,3,4]
    max_num_pages = {'2018_6_1': 24,
                     '2018_6_2': 12,
                     '2018_6_3': 12,
                     '2018_6_4': 24}
    
    urls=['http://paper.people.com.cn/rmrb/page/{:04d}-{:02d}/{:02d}/{:02d}/rmrb{:04d}{:02d}{:02d}{:02d}.pdf']

    '''
    Renmin - http://paper.people.com.cn/rmrb/page/{YEAR}-{MONTH}/{DAY}/{PAGE}/rmrb{YEAR}{MONTH}{DAY}{PAGE}.pdf   
    '''
    
    urllist = []
    desclist = []
    for year in years:
        for month in months:
            for day in days:
                # If we know the number of pages in this issue, use that; otherwise, use max possible
                num_pages = max_num_pages["_".join([str(x) for x in (year, month, day)])] or DEFAULT_MAX_NUM_PAGES
                for page in [x + 1 for x in range(num_pages)]:   
                    urllist.append(urls[0].format(year,month,day,page,year,month,day,page))
                    desclist.append('Renmin/{:04d}/{:02d}/{:02d}-{:02d}.pdf'.format(year,month,day,page))

     
    print(f'Downloading {len(urllist)} files')
   
    downloader = ThreadedDownload(urllist, desclist, args.output, args.threads, args.tries, args.throttle)
    downloader.run()

    if len(downloader.report['failure']) > 0:
        print('\nFailed urls:')
        for url in downloader.report['failure']:
            print(url)
 
    print(f'...complete, time {(time.clock() - startTime)}')
            
if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=str, help=f'Output directory (default = {DEFAULT_OUTPUT_DIR})', default=DEFAULT_OUTPUT_DIR) 
    parser.add_argument('--threads', type=int, help=f'Number of threads (default = {DEFAULT_NUM_THREADS})', default=DEFAULT_NUM_THREADS) 
    parser.add_argument('--throttle', type=int, help=f'Number of seconds to wait between downloads (default = {DEFAULT_THROTTLE})', default=DEFAULT_THROTTLE)
    parser.add_argument('--tries', type=int, help=f"Number of times to try downloading a given URL before giving up (default = {DEFAULT_URL_TRIES})", default=DEFAULT_URL_TRIES)
    main(parser.parse_args())

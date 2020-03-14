import sys
import os
import argparse
import time
import urllib.error
from urllib.request import urlretrieve

'''
Download pdfs required for HLTCOE Renmin OCR/NER Collection

2020-03-13
Run with -h flag for usage information.
'''

DEFAULT_OUTPUT_DIR = '.'
DEFAULT_MAX_TRIES = 3
DEFAULT_THROTTLE = 5
MAX_PAGES_PER_ISSUE = 30

class Downloader:    
    
    class URLTarget():
        def __init__(self, pair, max_tries, throttle):
            self.url = pair['URL']
            self.destination = pair['FILENAME']
            self.max_tries = max_tries
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
                    print(f'download try {self.url_tried}, {self.url} to {self.destination}')

                urlretrieve(self.url, filename=self.destination)
                self.success = True
                
            except urllib.error.URLError as error:
                self.error = "DOWNLOAD ERROR: " + str(error.reason)
            
            time.sleep(self.throttle)    
            return self.success
        
        def __str__(self):
            return f'URLTarget (URL: {self.url}, Success: {self.success}, Error: {self.error})'
    
    def __init__(self, download_pairs, max_tries, throttle):       
        self.report = {'success': [], 'failure': []}        
        self.max_tries = max_tries
        self.throttle = throttle
        self.download_requests = []
        for pair in download_pairs:
            self.download_requests.append(Downloader.URLTarget(pair, max_tries, throttle))
  
    
    def run(self):
        while self.download_requests:
            request = self.download_requests.pop()
            response = request.download()
            if response == False and request.url_tried < request.max_tries:
                self.download_requests.insert(0, request)
            elif response == False and request.url_tried == request.max_tries:
                self.report['failure'].append(request)
            elif response == True:
                self.report['success'].append(request)
                   
def main(args):
    startTime = time.clock()

    years = [2018]
    months = [6]
    days = [1,2,3,4]
    days = [1]
    pages_per_issue = {'2018_6_1': 24,
                       '2018_6_2': 12,
                       '2018_6_3': 12,
                       '2018_6_4': 24}
    
    url_format = 'http://paper.people.com.cn/rmrb/page/{:04d}-{:02d}/{:02d}/{:02d}/rmrb{:04d}{:02d}{:02d}{:02d}.pdf'
    '''
    Renmin - http://paper.people.com.cn/rmrb/page/{YEAR}-{MONTH}/{DAY}/{PAGE}/rmrb{YEAR}{MONTH}{DAY}{PAGE}.pdf   
    '''
    download_pairs = []
    for year in years:
        for month in months:
            for day in days:
                # If we know the number of pages in this issue, use that; otherwise, use max possible
                num_pages = pages_per_issue["_".join([str(x) for x in (year, month, day)])] or MAX_PAGES_PER_ISSUE
                for page in [x + 1 for x in range(num_pages)]:
                    directory = os.path.join(args.output, 'pdf', f'{year:04d}', f'{month:02d}')
                    if not os.path.exists(directory):
                        os.makedirs(directory)
                    download_pairs.append({'URL': url_format.format(year, month, day, page, year, month, day, page),
                                           'FILENAME': os.path.join(directory, f'{day:02d}-{page:02d}.pdf')})
     
    print(f'Downloading {len(download_pairs)} files')
   
    downloader = Downloader(download_pairs, args.tries, args.throttle)
    downloader.run()

    if len(downloader.report['failure']) > 0:
        print('\nFailed urls:')
        for url in downloader.report['failure']:
            print(url)
        sys.exit(-1)
    print(f'...complete, time {(time.clock() - startTime)}')
            
if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=str, help=f'Output directory (default = {DEFAULT_OUTPUT_DIR})', default=DEFAULT_OUTPUT_DIR) 
    parser.add_argument('--throttle', type=int, help=f'Number of seconds to wait between downloads (default = {DEFAULT_THROTTLE})', default=DEFAULT_THROTTLE)
    parser.add_argument('--tries', type=int, help=f"Number of times to try downloading a given URL before giving up (default = {DEFAULT_MAX_TRIES})", default=DEFAULT_MAX_TRIES)
    main(parser.parse_args())

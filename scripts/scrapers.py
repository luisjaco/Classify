# setup
import requests
import pandas as pd
from collections import defaultdict
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import time
from functools import reduce
import argparse

# -------- #
# DEFAULTS - FROM HOME DIRECTORY

# GREENHOUSE
# python ./scripts/scrapers.py greenhouse --csv-in ./data/companies/greenhouse.csv --csv-out ./data/jobs/greenhouse_jobs.csv

# SMARTRECRUITERS
# python ./scripts/scrapers.py smartrecruiters --csv-in ./data/companies/smartrecruiters.csv --csv-out ./data/jobs/smartrecruiters_jobs.csv

# ASHBY
# python ./scripts/scrapers.py ashby --csv-in ./data/companies/ashby.csv --csv-out ./data/jobs/ashby_jobs.csv
# ----

class Scraper():
    '''Base scraper class.'''
    def __init__(self, csv_in: str, csv_out: str):
            '''Intialize a scraper instance.

            Params:
                csv_in: 
                    str - Filepath to a company-data csv for the corresponding ATS system.
    
                csv_out:
                    str - Filepath to desired results location.
            '''
            self.df = pd.read_csv(csv_in)
            self.csv_out = csv_out
            self.session = requests.Session()
            retries = Retry(total=3, backoff_factor=1, status_forcelist=[429, 500, 502, 503, 504])
            self.session.mount('https://', HTTPAdapter(max_retries=retries))

    def fetch():
        # fetch single companies job postings.
        raise NotImplementedError

    def get_jobs(
            self,
            limit: int= -1
        ) -> dict:
        '''Scrape platform for jobs using the defined inputs. Override function if not using slug 
        format.

        Params:
            limit:
                int=-1 - Limit of companies to check. -1 to search all possible companies.
            
        Returns:
            dict - A dictionary of results. results[company_identifier] = job list | error code
        '''

        # --- create variables
        self.INVALID = set() # invalid company identifiers
        results = defaultdict()
        i = 0
        # stats
        valid = 0
        has_jobs = 0
        total_jobs = 0

        # --- begin scrape
        start_time = time.time()
        print('id   slug                                               response           total/error')
        for slug in self.df.slug:
            if i == limit: break
            # - fetch
            res = self.fetch(slug) # should return a list of jobs, or an int with an error code

            # - validate
            if isinstance(res, list):
                valid += 1
                if len(res) > 0:
                    has_jobs += 1
                    total_jobs += len(res)
                print(f'{i:<4} {slug:<40}           valid              total: {len(res)}')
            else:
                self.INVALID.add(slug)
                print(f'{i:<4} {slug:<40}           invalid            error: {res}')

            # - update
            results[slug] = res
            i += 1

            # respect rate limit
            time.sleep(self.DELAY) # inherited from child
        end_time = time.time()

        self.SCRAPE_TIME = end_time - start_time


        # --- print stats
        print('-'*103)
        if i > 0:
            print(f'''scrape results:
    scraping time:        {end_time-start_time:.1f}s ({(end_time-start_time) / 60:.2f}m)
    scraped slugs:        {i}
    total jobs:           {total_jobs}
    -
    valid slugs:          {valid} ({(valid/i)*100:.1f}%)
    valid with jobs:      {has_jobs} 
    invalid:              {len(self.INVALID)} ({(len(self.INVALID)/i)*100:.1f}%)
''')
        else:
            print('no jobs scraped.')

        return results

    def process():
        # process jobs into a single-row format.
        raise NotImplementedError

    def run(
            self,
            limit: int=-1,
        ) -> pd.DataFrame:
        '''Will perform the entire scraping and processing loop. Saves results to *self.csv_out*.
        
        Params:
            limit:
                int=-1 - Limit of company slugs to check. -1 to search all possible slugs.

        Returns:
                    pd.DataFrame - DataFrame containing processed scrape information. DataFrame will contain
                    the following columns: [slug, company_name, title, board_id, url, date_posted, 
                    date_scraped]
        '''
        unprocessed = self.get_jobs(limit)
        processed = self.process(unprocessed)

        # save as csv
        print(f'saving results to "{self.csv_out}"...')
        processed.to_csv(self.csv_out)
        print(f'results saved to "{self.csv_out}".')
        return processed   

    def get_invalid(self) -> set[str]:
        return self.INVALID

    def get_scrape_time(self) -> tuple[int, int] | None:
        '''Returns scrape time in seconds, scrape time in minutes, or None.'''
        if self.SCRAPE_TIME:
            return self.SCRAPE_TIME, self.SCRAPE_TIME / 60
        else:
            return None

class Greenhouse(Scraper):
    '''Greenhouse (*greenhouse.io*) scraper.
            
        ### Rate limit: 
            Greenhouse defines no rate limit on their job board API, however they define a 
            50-per-10-second limit on their audit log API, so to respect this we will use a 
            **.2s** delay.
    '''
    DELAY=0.2 
    
    def __init__(self, csv_in: str, csv_out: str):
        super().__init__(csv_in, csv_out)

    def fetch(self, slug: str) -> list | int:
        '''Will fetch a companies job listings using the Greenhouse Job Board API.
        
        Params:
            slug:
                str - The slug to request.
        
        Returns:
            list | str - A list of all jobs; if an error occurs, the int status code will be returned.
        '''
        try:
            # retrieve
            res = self.session.get(f'https://boards-api.greenhouse.io/v1/boards/{slug}/jobs')

            # detect error
            if not res.ok: raise Exception(res.status_code)

            # return jobs
            res_json = res.json()
            return res_json['jobs']
            
        except Exception as e:
            return int(str(e))

    def process(
            self,
            results: dict, 
        ) -> pd.DataFrame:
        '''Will process a given input of job results.
        
        Params:
            results: 
                dict - Unprocessed scrape results.
        
        Returns:
            pd.DataFrame - DataFrame containing processed scrape information. DataFrame will contain
            the following columns: [slug, company_name, title, board_id, url, date_posted, 
            date_scraped]
        '''
        df = pd.DataFrame(columns=['slug', 'company_name', 'title', 'board_id', 'url', 'date_posted', '_company_key'])

        # iterate through all slugs, and extract information from all valid job listings
        for slug in results.keys():
            jobs = results[slug]
            # process jobs
            if isinstance(jobs, list) and len(jobs) > 0:
                rows = []
                for job in jobs:
                    data = {
                        'slug':             slug,
                        'company_name':     str(job['company_name']).strip(),
                        'title':            str(job['title']).strip().lower(), 
                        'board_id':         job['id'],  
                        'url':              job['absolute_url'],
                        'date_posted':      pd.to_datetime(job['first_published'], utc=True), 
                        '_company_key':     str(job['company_name']).strip().lower()
                    }
                    rows.append(data)
                rows_df = pd.DataFrame(rows)
                df = pd.concat([df, rows_df], ignore_index=True)

        # add timestamp
        df['date_scraped'] = pd.Timestamp.now(tz='UTC')
        # remove duplicates
        #   duplicates may occur in instances where we have two slugs with different capitilzation 
        #   within our company slug file.
        df = df.drop_duplicates(subset=['_company_key', 'board_id'], keep='first')
        df = df.drop(columns=['_company_key'])
        return df

class SmartRecruiters(Scraper):
    '''SmartRecruiters (*smartrecruiters.com*) scraper.

    Rate limit:
    ---
        Smart recruiters lists an allowed 10 requests per second. We will use a **0.1s** delay.
    '''
    DELAY=0.1
    def __init__(self, csv_in: str, csv_out: str):
        super().__init__(csv_in, csv_out)

    def fetch(self, slug: str) -> list | int:
        '''Will fetch a companies job listings.
        
        Params:
            slug:
                str - The slug to request.
        
        Returns:
            list | str - A list of all jobs; if an error occurs, the int status code will be returned.
        '''
        # smartrecruiters will give a max of 100 jobs at once.
        # in the event a company has more than 100 jobs open, we must using a sliding window
        checked = 0
        total = None
        content = []
        try:
            while total is None or checked < total:
                # respect rate limit when sliding window
                if checked > 0: time.sleep(0.1) 
    
                # retrieve
                res = self.session.get(
                    f'https://api.smartrecruiters.com/v1/companies/{slug}/postings',
                    params={
                        'limit': 100,
                        'offset': checked
                        }
                    )
    
                # check 
                if not res.ok: raise Exception(res.status_code) # return error code
    
                # process            
                res_json = res.json()
                if total is None: total = res_json['totalFound'] # update total
                content += res_json['content']
    
                # slide window
                checked += 100
            return content   
        except Exception as e:
            return int(str(e))

    def process(
            self,
            results: dict, 
        ) -> pd.DataFrame:
        '''Will process a given input of job results.
        
        Params:
            results: 
                dict - Unprocessed scrape results.
        
        Returns:
            pd.DataFrame - DataFrame containing processed scrape information. DataFrame will contain
            the following columns: [slug, company_name, title, board_id, url, date_posted, 
            date_scraped]
        '''
        df = pd.DataFrame(columns=['slug', 'company_name', 'title', 'board_id', 'url', 'date_posted', '_company_key'])
        
        # iterate through all slugs, and extract information from all valid job listings
        for slug in results.keys():
            jobs = results[slug]
            # process jobs
            if isinstance(jobs, list) and len(jobs) > 0:
                rows = []
                for job in jobs:
                    data = {
                        'slug':             slug,
                        'company_name':     str(job['company']['name']).strip(),
                        'title':            str(job['name']).strip().lower(), 
                        'board_id':         job['id'],  
                        'url':              job['ref'],
                        'date_posted':      pd.to_datetime(job['releasedDate'], utc=True), 
                        '_company_key':     str(job['company']['name']).strip().lower()
                    }
                    rows.append(data)
                rows_df = pd.DataFrame(rows)
                df = pd.concat([df, rows_df], ignore_index=True)

        # add timestamp
        df['date_scraped'] = pd.Timestamp.now(tz='UTC')
        # remove duplicates
        #   duplicates may occur in instances where we have two slugs with different capitilzation 
        #   within our company slug file.
        df = df.drop_duplicates(subset=['_company_key', 'board_id'], keep='first')
        df = df.drop(columns=['_company_key'])
        return df

class Ashby(Scraper):
    '''Ashby (*ashbyhq.com*) scraper.
    
    Rate limit
    ---
    Ashby does not define a rate limit on their API website, we will use a **.2s** delay.
    '''
    DELAY=0.2
    def __init__(self, csv_in: str, csv_out: str):
        super().__init__(csv_in, csv_out)

    def fetch(self, slug: str) -> list | int:
        '''Will fetch a companies job listings.
        
        Params:
            slug:
                str - The slug to request.
        
        Returns:
            list | str - A list of all jobs; if an error occurs, the int status code will be returned.
        '''
        try:
            # retrieve
            res = self.session.get(f'https://api.ashbyhq.com/posting-api/job-board/{slug}')

            # detect error
            if not res.ok: raise Exception(res.status_code)

            # return jobs
            res_json = res.json()
            return res_json['jobs']
            
        except Exception as e:
            return int(str(e))

    def process(
            self,
            results: dict, 
        ) -> pd.DataFrame:
        '''Will process a given input of job results.
        
        Params:
            results: 
                dict - Unprocessed scrape results.
        
        Returns:
            pd.DataFrame - DataFrame containing processed scrape information. DataFrame will contain
            the following columns: [slug, company_name, title, board_id, url, date_posted, 
            date_scraped]
        '''
        df = pd.DataFrame(columns=['slug', 'company_name', 'title', 'board_id', 'url', 'date_posted', '_company_key'])

        # iterate through all slugs, and extract information from all valid job listings
        for slug in results.keys():
            jobs = results[slug]
            # process jobs
            if isinstance(jobs, list) and len(jobs) > 0:
                rows = []
                for job in jobs:
                    data = {
                        'slug':             slug,
                        'company_name':     None, # not listed in ashby job api results
                        'title':            str(job['title']).strip().lower(), 
                        'board_id':         job['id'],  
                        'url':              job['jobUrl'],
                        'date_posted':      pd.to_datetime(job['publishedAt'], utc=True), 
                        '_company_key':     str(slug).lower()
                    }
                    rows.append(data)
                rows_df = pd.DataFrame(rows)
                df = pd.concat([df, rows_df], ignore_index=True)

        # add timestamp
        df['date_scraped'] = pd.Timestamp.now(tz='UTC')
        # remove duplicates
        #   duplicates may occur in instances where we have two slugs with different capitilzation 
        #   within our company slug file.
        df = df.drop_duplicates(subset=['_company_key', 'board_id'], keep='first')
        df = df.drop(columns=['_company_key'])
        return df


# -----

def main(ats, csv_in, csv_out, limit):
    scraper = None

    match ats:
        case 'greenhouse':
            scraper = Greenhouse(csv_in, csv_out)
        case 'smartrecruiters':
            scraper = SmartRecruiters(csv_in, csv_out)
        case 'ashby':
            scraper = Ashby(csv_in, csv_out)
        case _:
            print('Invalid ATS system.')
            return

    scraper.run(limit)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Fetch job postings for an ATS system.")

    parser.add_argument('ats', help='e.g. greenhouse')
    parser.add_argument('--csv-in', required=True, help='CSV file to get company information from.')
    parser.add_argument('--csv-out', required=True, help='CSV file to write results to.')
    parser.add_argument('--limit', type=int, default=-1, help='Maximum companies to scrape. -1 for all companies. Default=-1')

    args = parser.parse_args()

    main(args.ats, args.csv_in, args.csv_out, args.limit)
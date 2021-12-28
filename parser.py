from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor, as_completed
from requests import get
from datetime import date, datetime, timedelta
from locale import setlocale, LC_ALL
from event import Event

class Parser:
    """
    Parses events from url
    depending on location, tags and time interval
    """
    def __init__(self):
        self.__parse_url = 'https://dou.ua/calendar/'
        self.__headers = {'User-Agent' : 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:95.0) Gecko/20100101 Firefox/95.0'}

    def __parse_date(self, date_str):
        setlocale(LC_ALL,  'ru_RU.UTF-8')
        try:
            if '—' in date_str:
                dates = date_str.split(' — ')
                try:
                    end_date = datetime.strptime(dates[1], '%d %B %Y').date()
                except ValueError:
                    try:
                        end_date = datetime.strptime(dates[1]+f' {datetime.now().year}', '%d %B %Y').date()
                    except ValueError:
                        end_date = datetime.strptime(dates[1]+f' {datetime.now().month} {datetime.now().year}', '%d %B %Y').date()
                try:
                    start_date = datetime.strptime(dates[0]+f' {end_date.year}', '%d %B %Y').date()
                except ValueError:
                    start_date = datetime.strptime(dates[0]+f' {end_date.month} {end_date.year}', '%d %m %Y').date()
                return (start_date, end_date)
            else:
                return datetime.strptime(date_str, '%d %B %Y').date()
        except ValueError:
            return datetime.strptime(date_str+f' {datetime.now().year}', '%d %B %Y').date()

    def __pages_amount(self, main_page_url):    
        """
        returns amount of pages to parse from url
        """
        located_soup = BeautifulSoup(get(main_page_url, headers=self.__headers).text, 'html.parser')
        try:
            return int(located_soup.find('div', {'class':'b-paging'}).find_all('span', {'class':'page'})[-1].a.text)
        except AttributeError:
            return 1

    def parse_tags(self):
        soup = BeautifulSoup(get(self.__parse_url, headers=self.__headers).text, 'html.parser')
        return  [tag.text for tag in soup.find('select', {'name':'tag'}).find_all('option')][1:]

    def parse_locations(self):
        soup = BeautifulSoup(get(self.__parse_url, headers=self.__headers).text, 'html.parser')
        return [location.text for location in soup.find('select', {'name':'city'}).find_all('option')]

    def __parse_page(self, events_url, headers, preferred_tags, event_interval, location):
        """
        parses events from single page
        """
        events_data = BeautifulSoup(get(events_url, headers=headers).text, 'html.parser').find_all('article')
        events = []
        for event_data in events_data:
            event_date = self.__parse_date(str(event_data.div.span.text))
            if isinstance(event_date, tuple):
                start_date = event_date[0]
                end_date = event_date[1]
            else:
                start_date = end_date = event_date
            if start_date >= date.today() and end_date - date.today() >= timedelta(days=event_interval):
                return events
            tags = [tag.text for tag in event_data.find('div', {'class':'more'}).find_all('a')]
            if any(item in tags for item in preferred_tags):
                url = event_data.h2.a['href']
                name = event_data.h2.img['alt']
                img_url = event_data.h2.img['srcset'].replace(' 1.1x', '')
                price_info = event_data.div.find_all('span')
                price = None
                if len(price_info) > 1:
                    price = price_info[-1].text.strip()
                description = event_data.p.text.strip()
                events.append(Event(name, description, str(start_date), str(end_date), location, str(price), img_url, url, tags))
        return events

    def parse_events(self, location, tags, event_interval):
        """
        returns events list
        """
        events = []
        locations = BeautifulSoup(get(self.__parse_url, headers=self.__headers).text, 'html.parser').find('select', {'name':'city'})
        located_url = None
        for option in locations:
            if location in option:
                located_url = option['value']
        if self.__parse_url == located_url:
            urls_list = [located_url+'page-'+str(i) for i in range(1, self.__pages_amount(located_url)+1)]
        else:
            urls_list = [located_url+str(i) for i in range(1, self.__pages_amount(located_url)+1)]
        with ThreadPoolExecutor() as executor:
            futures = []
            for url in urls_list:
                futures.append(executor.submit(self.__parse_page, url, self.__headers, tags, event_interval, location))
            for future in as_completed(futures):
                for event in future.result():
                    events.append(event)
        return events

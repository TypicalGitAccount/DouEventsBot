class Event:
    """
    Holds event info
    """
    def __init__(self, name, description, start_date, end_date, location, price, img, link, tags):
        self.name = name
        self.description = description
        self.start_date = start_date
        self.end_date = end_date
        self.location = location
        self.price = price
        self.img = img
        self.link = link
        self.tags = tags

    @property
    def name(self):
        return self.__name

    @property
    def description(self):
        return self.__description

    @property
    def start_date(self):
        return self.__start_date

    
    @property
    def end_date(self):
        return self.__end_date

    @property
    def location(self):
        return self.__location

    @property
    def price(self):
        return self.__price

    @property
    def img(self):
        return self.__img
    
    @property
    def link(self):
        return self.__link

    @property
    def tags(self):
        return self.__tags

    @name.setter
    def name(self, val):
        if not isinstance(val, str):
            raise TypeError('val should be str instance')
        self.__name = val

    @description.setter
    def description(self, val):
        if not isinstance(val, str):
            raise TypeError('val should be str instance')
        self.__description = val

    @start_date.setter
    def start_date(self, val):
        if not isinstance(val, str):
            raise TypeError('val should be str instance')
        self.__start_date = val

    @end_date.setter
    def end_date(self, val):
        if not isinstance(val, str):
            raise TypeError('val should be str instance')
        self.__end_date = val

    @location.setter
    def location(self, val):
        if not isinstance(val, str):
            raise TypeError('val should be str instance')
        self.__location = val

    @price.setter
    def price(self, val):
        if not isinstance(val, str):
            raise TypeError('val should be str instance')
        self.__price = val

    @img.setter
    def img(self, val):
        if not isinstance(val, str):
            raise TypeError('val should be str instance')
        self.__img = val

    @link.setter
    def link(self, val):
        if not isinstance(val, str):
            raise TypeError('val should be str instance')
        self.__link = val

    @tags.setter
    def tags(self, val):
        if not isinstance(val, list) and not all(isinstance(el, str) for el in val):
            raise TypeError('val should be list of str instances')
        self.__tags = val

    def to_gcalendar(self):
        """
        returns event in a form GCalendar class accepts - json
        """
        start_date_time = str(self.start_date)+'T00:00:00'
        end_date_time = str(self.end_date)+'T23:59:59'
        return { 'summary': self.name,
                'location': self.location,
                'description': self.description,
                'start': {     
                'dateTime': start_date_time,
                'timeZone': 'Europe/Kiev',
            },
            'end': {
                'dateTime': end_date_time,
                'timeZone': 'Europe/Kiev',
            }
        }

    def to_user(self):
        """
        returns event in form that will be shown to user
        """
        tags = ', '.join(self.tags)
        if self.start_date == self.end_date:
            date = self.start_date
        else:
            date = f'{self.start_date} - {self.end_date}'
        return f'{self.name}\n{self.description}\n{date}\n{self.location}\n{self.price}\n{self.link}\ntags: {tags}\n\n'

    @staticmethod
    def from_text_to_gcalendar(event_string):
        event = event_string.split('\n')
        name = event[0]
        description = event[1]
        date = event[2]
        if ' - ' in  date:
            date = date.split(' - ')
            start_date_time = date[0]+'T00:00:00'
            end_date_time = date[1]+'T23:59:59'
        else:
            start_date_time = date+'T00:00:00'
            end_date_time = date+'T23:59:59'
        location = event[3]

        return { 'summary': name,
                'location': location,
                'description': description,
            'start': {     
                'dateTime': start_date_time,
                'timeZone': 'Europe/Kiev',
            },
            'end': {
                'dateTime': end_date_time,
                'timeZone': 'Europe/Kiev',
            }
        }

import time

import requests
from bs4 import BeautifulSoup

from selenium import webdriver
from enum import Enum


class Mode(Enum):
    """
    Scrapper work modes

    STATIC : gets static content from url
    DYNAMIC : gets dynamic content from url
    SOUP : pass existing soup and get static content
    """

    STATIC = 1  # get static content
    DYNAMIC = 2  # get dynamic content
    SOUP = 3    # pass soup and get content


class ContentWebScrapper():

    """
    Generic scrapper for parse dynamic/static content

    :param url: url to be retrieved
    :param mode: indicates work mode reffered to class 'Mode'
    :param soup: if html is already retrieved, scraper can be for purely data parsings
    :param page_load_checker: Tag which when available, we are sure that the page has loaded
        e.g. {
            'tag_identifiers': [('img', {'id': 'landingImage'}), ('img', {'id': 'main-image'})],
            'attr': 'src',
            'nullable': True}
    >> check below for explanation on the keys of this param
    :param targets: e.g. [{
                'key': 'image_url',
                'tag_identifiers': [('img', {'id': 'landingImage'}), ('img', {'id': 'main-image'})],
                'attr': 'src',
                'nullable': True,
                'all' : True},]

        1. `key` is used for creating a dictionary with the value
            retrieved and key `target[key]`
        2. `tag_identifiers` array of sets of tag_name (e.g. div)
            and dictionary with the identifier of the tag - the sets are
            searched for in the same order as they appear in the array
            and the search stops once the tag is found
        3. `attr` [optional] indicates that the data required is stored
            in the attribute `attr`
            e.g. <a href='http://i-am-important.com'>not important</a>
            if `attr` is set to href, the href is returned
        4. `nullable`  [optional] indicated whether this field is required or not
        5. `all` indicated how many same tags will be returned

    :param extra_functions: form: (key, function)
        `key` is used for creating a dictionary with the value
        retrieved and key `key`
        `function` function used to retrieve data that cannot be retrieved
        using the generic scraper

    returns dictionary of keys (supplied in `targets` as a param)
    and values that represent the data retrieved for
    the respective keys
    """

    def __init__(self, url=None, mode=Mode.STATIC, soup=None, page_load_checker=None, targets=None, extra_functions=None, driver=None):
        self.url = url
        self.mode = mode
        self.page_load_checker = page_load_checker
        self.targets = targets
        self.extra_functions = extra_functions
        self.driver = driver
        self.soup = soup

    @staticmethod
    def init_selenium_driver(*args, **kwargs):
        """
        Initiates and returns selenium webdriver
        """

        driver = webdriver.Chrome(*args, **kwargs)  # can be any other drivers

        return driver

    def check_page_loaded(self, max_delay=30):
        """
        Check page is loaded by confirming that a certain element
        loaded in the dom, the element can either be identified
        using `target` or `target_id`

        :param browser: browser

        :param target: Tag which when available, we are sure that the page has loaded
            e.g. {
                    'tag_identifiers': [('img', {'id': 'landingImage'}), ('img', {'id': 'main-image'})],
                    'attr': 'src',
                }
            1. `tag_identifiers` array of sets of tag_name (e.g. div)
                and dictionary with the identifier of the tag - the sets are
                searched for in the same order as they appear in the array
                and the search stops once the tag is found
            2. `attr` [optional] indicates that the data required is stored
                in the attribute `attr`
                e.g. <a href='http://i-am-important.com'>not important</a>
                if `attr` is set to href, the href is returned
        >> unlike other functions here, this function's target param does
        not take nullable, as it is always set to True for checking page
        loaded (otherwise, a tag without loaded data would evaluate this function to a false positive)

        :param max_delay: maximum delay before timeout - in seconds

        returns boolean indicating whether page loaded or timedout

        """

        found = False
        # force set nullable to true otherwise,
        # a tag without loaded data would evaluate
        # this function to a false positive
        self.page_load_checker['nullable'] = True
        # in seconds
        one_tick = 1
        while not found and max_delay:
            time.sleep(one_tick)

            html = self.driver.page_source
            soup = BeautifulSoup(html, 'lxml')

            confirmation_tag = self.get_target(self.page_load_checker, soup)
            if confirmation_tag:
                found = True
            max_delay -= one_tick

        return found

    def get_attr(self, tag, attr, nullable=False):
        """
        Gets attribute `attr` for `tag`

        :param tag: Tag
        :param attr: Attribute
        :param nullable: Is is possible that this
                    tag's attribute evaluates to Null
        """
        if nullable and not tag:
            return ''

        return [t.get(attr).strip() for t in tag]

    def get_text(self, tag, nullable=False):
        """
        Gets inner text for `tag`

        :param tag: Tag
        :param nullable: Is is possible that this
                    tag's inner text evaluate to Null
        """
        if nullable and not tag:
            return ''

        return [t.get_text().strip() for t in tag]

    def get_target(self, target, soup):
        """
        Retrieves `target` from `soup`

        :param target: a dictionary identifying the tag and its identifier
        e.g.
        {
            'tag_identifiers': [
                ('img', {'id': 'landingImage'}),
                ('img', {'id': 'main-image'})
            ],
            'attr': 'src',
            'nullable': True,
            'all': True
        }
            1. `tag_identifiers` array of sets of tag_name (e.g. div)
                and dictionary with the identifier of the tag - the sets are
                searched for in the same order as they appear in the array
                and the search stops once the tag is found
            2. `attr` [optional] indicates that the data required is stored
                in the attribute `attr`
                e.g. <a href='http://i-am-important.com'>not important</a>
                if `attr` is set to href, the href is returned
            3. `nullable` [optional] indicated whether this field is
                required or not
            4. `all` indicated how many same tags will be returned

        returns the value searched for by `target` in `soup`
        """

        for tag_name, tag_identifier in target['tag_identifiers']:

            if 'id' in tag_identifier.keys():
                if 'all' in target.keys():
                    if target['all'] is True:
                        tag = soup.find_all(id=tag_identifier['id'])
                    else:
                        tag = [soup.find(id=tag_identifier['id'])]
                else:
                    tag = [soup.find(id=tag_identifier['id'])]
            else:
                if 'all' in target.keys():
                    if target['all'] is True:
                        tag = soup.find_all(tag_name, tag_identifier)
                    else:
                        tag = [soup.find(tag_name, tag_identifier)]
                else:
                    tag = [soup.find(tag_name, tag_identifier)]

            if tag:
                break

        nullable = target.get('nullable')

        if 'attr' in target:
            return self.get_attr(
                tag, target['attr'], nullable=nullable)
        else:
            return self.get_text(tag, nullable=nullable)

    def run(self):
        """
        Start scrapping and return result [dict]
        """

        if self.url is None:
            raise ValueError('url cannot be empty')

        # create a new driver and get the soup as dynamic
        if self.mode is Mode.DYNAMIC:
            if not self.driver:
                self.driver = init_selenium_driver()

            self.driver.get(self.url)
            if self.page_load_checker:
                self.check_page_loaded()
            html = self.driver.page_source

            self.soup = BeautifulSoup(html, 'lxml')

        # get soup as static
        elif self.mode is Mode.STATIC:
            html = requests.get(self.url).content.decode('utf-8')
            self.soup = BeautifulSoup(html, 'lxml')
        else:
            if self.soup is None:
                raise ValueError('soup cannot be empty')

        # removing useless tags
        for script in self.soup(["script", "style"]):
            script.decompose()

        result = {}

        if self.targets:
            for target in self.targets:
                result[target['key']] = self.get_target(target, self.soup)

        if self.extra_functions:
            for key, function in self.extra_functions:
                result[key] = function(self.soup)

        return result

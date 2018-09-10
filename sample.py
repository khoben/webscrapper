from scrapper import ContentWebScrapper, Mode


def main():
    base_url = 'https://1xstavka.ru/line/Football/'

    targets = [
        {
            'key': 'link_ligas',  # key in output dict
            # defines html tag
            'tag_identifiers': [('a', {'class': 'c-events__liga'})],
            'nullable': True,  # can be nullable
            'attr': 'href',   # search for named attr in html tag
            'all': True       # fetch all similary tags
        }
    ]

    driver = ContentWebScrapper.init_selenium_driver(  # init chrome driver for selenium
        './driver/chromedriver.exe')

    betscrapper = ContentWebScrapper(
        driver=driver,  # driver for selenium
        mode=Mode.DYNAMIC,  # get a dynamic content
        url=base_url,    # source url
        targets=targets  # dict of targets
    )

    results = betscrapper.run()  # start the scrapper

    print(results)


if __name__ == '__main__':
    main()

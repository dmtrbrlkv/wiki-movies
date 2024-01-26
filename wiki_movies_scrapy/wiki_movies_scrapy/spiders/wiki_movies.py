import scrapy
import re
import requests



class WikiMoviesSpider(scrapy.Spider):
    name = "wiki_movies"
    allowed_domains = ['wikipedia.org', 'imdb.com']
    start_urls = ['https://ru.wikipedia.org/wiki/Категория:Фильмы_по_годам']

    def parse(self, response):
        years = response.css('#mw-subcategories > div > div > div:nth-child(3) > ul > li > div > div.CategoryTreeItem > a::attr(href)')
        yield from response.follow_all(years, callback=self.parse_year)

    def parse_year(self, response, from_next=False):
        movies_in_page = response.css('#mw-pages > div > div > div:nth-child(5) > ul > li > a::attr(href)')
        yield from response.follow_all(movies_in_page, callback=self.parse_movie)
        next_page = response.xpath('//a[text() = "Следующая страница"]')
        if next_page:
            yield response.follow(next_page[0], callback=self.parse_year)

    def parse_movie(self, response):
        title = response.css('#firstHeading > span::text').get()

        genre = response.xpath('//th/a[contains(text(), "Жанр")]/../..//span/a/text()').extract()
        if not genre:
            genre = response.xpath('//th/a[contains(text(), "Жанр")]/../../td//a/text()').extract()
        if not genre:
            genre = response.xpath('//th/a[contains(text(), "Жанр")]/../..//span/text()').extract()

        director = response.xpath('//th[contains(text(), "Режисс")]/..//a/span[not( contains(text(), "["))]/text()').extract()
        if not director:
            director = response.xpath('//th[contains(text(), "Режисс")]/..//a/text()').extract()
        if not director:
            director = response.xpath('//th[contains(text(), "Режисс")]/../td/span/text()').extract()

        country = response.xpath('//th[contains(text(), "Стран")]/..//a/span/text()').extract()
        if not country:
            country = response.xpath('//th[contains(text(), "Стран")]/..//a/text()').extract()
        if not country:
            country = response.xpath('//th[contains(text(), "Стран")]/..//a/span/text()').extract()
        if not country:
            country = response.xpath('//th[contains(text(), "Стран")]/..//span/text()').extract()

        year = response.xpath('//th[text()="Год"]/..//*[re:test(text(), "\d{4}")]/text()').get()
        if year and len(year) != 4:
            year = re.search('\d{4}', year)
            if year:
                year = year[0]

        imdb_id = response.xpath('//th/a[contains(text(), "IMDb")]/../..//span/a/text()').get()
        if imdb_id:
            imdb_id = imdb_id.split('ID ')[-1]
            if self.settings.get('PARSE_RATING'):
                rating = self.rating_from_tmdb_api(imdb_id, self.settings.get('PROXIES'), self.settings.get(('API_KEY')))
            else:
                rating = None
        else:
            rating = None


        yield {
            'title': title,
            'genre': genre,
            'director': director,
            'country': country,
            'year': year,
            'imdb_id': imdb_id,
            'rating': rating,
            'url': response.url
        }

    def rating_from_tmdb_api(self, imdb_id, proxies, api_key):
        params = {
            'api_key': api_key,
            'external_source': 'imdb_id'
        }
        url = f'https://api.themoviedb.org/3/find/tt{imdb_id}'
        try:
            resp = requests.get(url, proxies=proxies, params=params)
            json = resp.json()
            return json['movie_results'][0]['vote_average']
        except Exception as e:
            print(e)
            return None

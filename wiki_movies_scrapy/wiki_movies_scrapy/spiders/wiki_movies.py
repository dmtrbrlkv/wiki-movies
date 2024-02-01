import scrapy


class WikiMoviesSpider(scrapy.Spider):
    name = "wiki_movies"
    allowed_domains = ['wikipedia.org', 'api.themoviedb.org']
    start_urls = ['https://ru.wikipedia.org/wiki/Категория:Фильмы_по_годам']

    def parse(self, response):
        years = response.css(
            '#mw-subcategories > div > div > div:nth-child(3) > ul > li > div > div.CategoryTreeItem > a::attr(href)'
        )
        yield from response.follow_all(years, callback=self.parse_year)

    def parse_year(self, response):
        year = int(response.xpath('//*[@id="mw-content-text"]/div[1]/table/tbody/tr/th/text()').get().strip())
        movies_in_page = response.xpath('//*[@id="mw-pages"]/div/div/div/ul/li/a')
        yield from response.follow_all(movies_in_page, callback=self.parse_movie, cb_kwargs={'year': year})
        next_page = response.xpath('//a[text() = "Следующая страница"]')
        if next_page:
            yield response.follow(next_page[0], callback=self.parse_year)

    def parse_movie(self, response, year):
        title = response.css('#firstHeading > span::text').get()

        genre = response.xpath('//th/a[contains(text(), "Жанр")]/../..//span/a/text()').extract()
        if not genre:
            genre = response.xpath('//th/a[contains(text(), "Жанр")]/../../td//a/text()').extract()
        if not genre:
            genre = response.xpath('//th/a[contains(text(), "Жанр")]/../..//span/text()').extract()

        director = response.xpath(
            '//th[contains(text(), "Режисс")]/..//a/span[not( contains(text(), "["))]/text()'
        ).extract()
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

        imdb_id = response.xpath('//th/a[contains(text(), "IMDb")]/../..//span/a/text()').get()
        if imdb_id:
            imdb_id = imdb_id.split('ID ')[-1]

        data = {
            'title': title,
            'genre': genre,
            'director': director,
            'country': country,
            'year': year,
            'imdb_id': imdb_id,
            'url': response.url
        }

        parse_rating = self.settings.get('PARSE_RATING')
        if parse_rating:
            api_key = self.settings.get('API_KEY')
            proxy = self.settings.get('PROXY')
            external_source = 'imdb_id'

            rating_url = (f'https://api.themoviedb.org/3/find/tt{imdb_id}?'
                          f'api_key={api_key}&external_source={external_source}')
            yield scrapy.Request(
                rating_url,
                callback=self.parse_rating,
                cb_kwargs={'data': data, 'imdb_id': imdb_id},
                meta={'proxy': proxy}
            )
        else:
            yield data

    def parse_rating(self, response, data, imdb_id):
        if not imdb_id:
            data['rating'] = None
            yield data

        try:
            rating = response.json()['movie_results'][0]['vote_average']
        except Exception:
            rating = None

        data['rating'] = rating
        yield data

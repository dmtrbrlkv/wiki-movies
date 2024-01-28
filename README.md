# Парсер фильмов с Википедии и рейтинга с tmdb.org на фреймворке scrapy.

## Установка зависимостей
`pip install -r requirements.txt`
## Настройка для доступа к api tmdb
По умолчанию рейтинг не парсится из-за запрета доступа к tmdb.org и необходимости использовать ключ доступа. При наличии прокси и ключа можно в файле wiki_movies_scrapy/wiki_movies_scrapy/settings.py указать значения
```
PARSE_RATING = True
PROXY = '<Прокси для доступа к tmdb.org>'
API_KEY = '<Персональный апи ключ tmdb.org>'
```
## Запуск парсера
```
cd wiki_movies_scrapy
scrapy crawl -O movies.csv:csv wiki_movies
```
Результаты будут сохранены в файл movies.csv
build-force:
	docker build -t books_toscrape:14 . --no-cache --pull

build:
	docker build -t books_toscrape:14 .

up:
	docker run -e POSTGRES_HOST_AUTH_METHOD=trust -p 5432:5432 books_toscrape:14

run:
	pdm run python ./src/first_scraper_mod/scraper.py 

	
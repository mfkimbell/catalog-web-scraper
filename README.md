# bookstore-web-scraper

The purpose of this project was to practice webscraping. The goal was to scrape the entire catalogue from BooksToScrape.com and store all of the information in a postgreSQL database. Specifically, I wanted to navigate to each genre and collect all the books in each genre so that when the book are stored, they have a genre field, which they currently do not when accessing each book's page. 

**Tools Used:**

* `lxml`, HTTP requests, and Xpaths for extracting data/html elemtents from the book catalogue.
* yml file to hold connection information for sql database
* `docker` and `dockefile` to containerize the program
* `.sh` shell scripting to execute commands
* `.sql` files to execute queries
* `aiohttp` for initializing HTTP connection
* `RabbitPSQLMixin` class that creates objects for transferring messsages to `RabbitMQ` as well as PostgreSQL
* `asyncio` for sending concurrent requests to an event loop, which delivers them to be processed
* `.toml` for storing configuration data
* `makefile` for creating shortcuts for rerunning and rebuilding the docker container



In the shell script, I am creating the postgres database as well as inserting the main table by initializing the sql file. 

```
echo "Creating database: postgres"
psql -U postgres -c "CREATE DATABASE postgres";

echo "Running tables.sql"
psql -d postgres -U postgres -f ./tables.sql.init
```
Which runs the following sql file.

```
CREATE SCHEMA IF NOT EXISTS books_to_scrape;

DROP TABLE IF EXISTS books;
DROP TABLE IF EXISTS categories;
DROP TABLE IF EXISTS books_to_category;

CREATE TABLE IF NOT EXISTS categories
(
    id INT,
    category VARCHAR(25),
    PRIMARY KEY(id)
);

CREATE TABLE IF NOT EXISTS books
(
    upc BIGINT,
    name text,
    price DECIMAL(4,2),
    description text,
    product_type VARCHAR(30),
    availibility VARCHAR(25),
    reviews text,
    PRIMARY KEY(upc)
    
);

CREATE TABLE IF NOT EXISTS books_to_category 
(
    book_id BIGINT,
    category_id INT,
    PRIMARY KEY(book_id, category_id),
    FOREIGN KEY(category_id) REFERENCES categories(id),
    FOREIGN KEY(book_id) REFERENCES books(upc)
    
);
```

lxml is a parsing tool that, in conjunction with the requests module, allows us to collect specific data from webpages. In this example, the worker is selecting the list of genre's from the left side of the main page and collecting the url from each hyperlink. It then uses those hyperlinks to call work on the those pages. `sxpath()` helps create a path from the connection source to the desired element. `get_element_at_xpath()` takes in the source and the path, and returns the html element. Some of the paths are stored in a dictionary called XPATH_MAP.

```Python
def sxpath(self, context: HtmlElement, xpath: str):
        res = context.xpath(xpath, smart_strings=False)
        return res

def get_element_at_xpath(self, element, xpath):
        return sxpath(element, xpath)

XPATH_MAP = {
    "genres": ".//ul[@class='nav nav-list']/li/ul/li/a/@href",
    "link_to_genre_allbooks": ".//ul[@class='nav nav-list']/li/a",
    "listings": ".//li//h3/a",
}
```

I have a couple functions for creating urls from pieces of information collected in order to reach desired new connections.
``` Python
def normalize_book_url_from_gallery(self, url) -> str:
        """Adds the parent directory URL to the specific book URL endings"""
        tail_list = url.split("/")
        tail = tail_list[-2] + "/" + tail_list[-1]
        new_url = "https://books.toscrape.com/catalogue/" + tail
        print("normalized url", new_url)
        return new_url
```
And I have many many functions like `get_category()`, `get_price()`, `get_descriptino()`, etc, that aquire various content on the page.
```Python
def get_category(self, bookpage) -> str:
        """Gets the category from the book page"""
        category_str_xpath = ".//ul[@class='breadcrumb']/li/a/text()"
        return sxpath(bookpage, category_str_xpath)[2]
```

Here's a visual representation of the Scraper's path through the catalogue marked with a ```1```

<img width="480" alt="Screenshot 2023-01-23 at 6 46 38 PM" src="https://user-images.githubusercontent.com/107063397/214188598-87bce61b-8025-4de2-8476-89b153313691.png">

The next step is to gather information from specific books. In order to do that, we have to navigate to the individual book pages. Shown previously with the number ```2```. 

Another issue is that each book genre has multiple pages of books, so we have to continue to naviagate to the "next" button if the page has one while we sort through books. The way we solve this is by having the docker command queue the next object to be parsed. 

In other words, a worker who's job is to accept the "main_page" will request a "genre_page" worker for every genre on the main page. A genre worker will both call another "genre_page" worker for the next page (if there is a next page) as well as call a "book_page" worker for each book on the genre page. The "book_page" worker will collect the necessary information from the book and add that data to the postgres table that was created earlier. 

When we create the scraper class, we give it a function that allows it to queue on RabbitMQ with the correct connection data from the config.

```Python 
class Scraper(AsyncRabbitPSQLMixin):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.queue = self.config["amqp"]["consumer_queue"]["books_toscrape_test"]["parameters"]["name"]
        self.session = None
```

In the main function, we initialize the Scraper, queue work for "main_page" "genre_page" and "book_page" workers, and publish the main page to be recieved by a "main_page" worker.

```Python
def main2():

    config = load_yml_file("./local_config.yml")

    loop = asyncio.get_event_loop()
    scraper = Scraper(config=config, loop=loop)
    loop.run_until_complete(scraper.start())

    scraper.register("main_page", scraper.process_main_page)
    scraper.register("genre_page", scraper.process_genre_page)
    scraper.register("book_page", scraper.process_book_page)

    main_page_item = {}
    main_page_item["URL"] = URL

    asyncio.ensure_future(scraper.run(), loop=loop)
    try:
        loop.run_forever()
    except KeyboardInterrupt:
        sys.exit()
 ```

The following is for the "main_page" worker, which collects URLS and calls for "genre_page" workers.

```Python
async def process_main_page(self, main_item) -> Boolean:
        """Publishes work to be done on each genre and the full catalogue from the main page"""
        URL = main_item["URL"]
        mainPage = await self.get_page(URL)

        # proccess all books including those without genre
        generic_block = self.get_element_at_xpath(
            mainPage, XPATH_MAP["link_to_genre_allbooks"]
        )[0]
        intermediate = generic_block.attrib["href"]
        generic_URL = URL + intermediate
        genericdict = {}
        genericdict["genreURL"] = generic_URL
        await self.publish("genre_page", genericdict, self.queue)

        genre_block = self.get_element_at_xpath(mainPage, XPATH_MAP["genres"])

        for href in genre_block:
            genreURL = URL + href
            genredict = {}
            genredict["genreURL"] = genreURL

            await self.publish("genre_page", genredict, self.queue)

        return True
```

Here, the "genre_page" worker checks if there is a next page, and if so, calls for another "genre_page" worker. Additionally, collects all of the URLs for the book links, and calls a "book_page" worker for each one. 

``` Python
async def process_genre_page(self, genreURL):
        """Processes book links on page, as well as publishes with a "next" button recursively"""
        genreURL = genreURL["genreURL"]
        print(genreURL)

        initial_split = genreURL.split("_")
        id = initial_split[1].split("/")[0]
        category = initial_split[0].split("/")[-1].replace("-", " ").title()

        if self.db is not None:
            await self.db.execute(
                "INSERT INTO categories (id,category) VALUES ($1,$2) ON CONFLICT (id) DO NOTHING",
                int(id),
                category,
            )

        genre_gallery_page = await self.get_page(genreURL)
        next_page_tag = self.get_next_page_tag(genre_gallery_page)
        next_gallery_url = self.normalize_gallery_url(genreURL, next_page_tag)

        bookURLs = []
        row = self.get_product_row(genre_gallery_page)
        if row != None:
            listings = self.get_element_at_xpath(row, XPATH_MAP["listings"])
            for a in listings:
                bookURLs.append(a.attrib["href"])
            for bookURL in bookURLs:
                bookDict = {"bookURL": bookURL, "category_id": id}
                await self.publish("book_page", bookDict, self.queue)

        if next_page_tag:
            genredict = {}
            genredict["genreURL"] = next_gallery_url
            await self.publish("genre_page", genredict, self.queue)
        return True
 ```

Finally, the "book_page" worker collects all of the desired data from the book page's URL and then stores that data into an postgreSQL table.

```Python
async def process_book_page(self, bookDict):
        """Takes data from the book's page and stores it in a psql database"""
        global book_counter
        book_counter += 1
        LOG.warning("%s", book_counter)
        bookURL = bookDict["bookURL"]

        bookURL = self.normalize_book_url_from_gallery(bookURL)
        bookPage = await self.get_page(bookURL)
        name = self.get_name(bookPage)
        category_id = bookDict["category_id"]
        price = self.get_price(bookPage)
        description = self.get_description(bookPage)
        product_table = self.get_product_table(bookPage)
        upc = product_table["UPC"]
        upc = twos_complement(upc, 64)

        product_type = product_table["Product Type"]
        availability = product_table["Availability"]
        number_of_reviews = product_table["Number of reviews"]

        if self.db is not None:
            await self.db.execute(
                "INSERT INTO books (name, price, description, UPC, product_type, availibility, reviews) VALUES ($1, $2,  $3, $4, $5, $6, $7) ON CONFLICT (upc) DO NOTHING",
                name,
                price,
                description,
                upc,
                product_type,
                availability,
                number_of_reviews,
            )

            await self.db.execute(
                "INSERT INTO books_to_category (book_id, category_id) VALUES ($1,$2) ON CONFLICT (book_id, category_id) DO NOTHING",
                upc,
                int(category_id),
            )
        return True
 ```

This is a visual demonstration of the "book worker's" data:

<img width="380" alt="Screenshot 2023-01-23 at 6 55 50 PM" src="https://user-images.githubusercontent.com/107063397/214191115-f994f5a8-4f54-4fab-9f96-686023eae4f8.png">

And here are examples of the relational database data. 


This is an example of a book record:

<img width="853" alt="Screenshot 2023-02-03 at 12 24 13 PM" src="https://user-images.githubusercontent.com/107063397/216784549-3f7df12c-aa86-456c-8cac-a9d70846876c.png">

This is what the categories table looks like:

<img width="377" alt="Screenshot 2023-02-03 at 12 23 21 PM" src="https://user-images.githubusercontent.com/107063397/216784572-88ae8dd0-2efc-40de-afa2-cde91f566cab.png">

And here is the table relating those data:

<img width="344" alt="Screenshot 2023-02-03 at 12 22 52 PM" src="https://user-images.githubusercontent.com/107063397/216784574-66c01207-3616-4555-b348-b73197461767.png">

Here is proof the scraper works, producing all of the books and categories in the count for those tables:

![Screenshot 2023-02-03 at 11 03 56 AM](https://user-images.githubusercontent.com/107063397/216784656-3e2f3620-97f0-43db-abf6-9250dd9b69ce.png)

![Screenshot 2023-02-03 at 11 04 20 AM](https://user-images.githubusercontent.com/107063397/216784662-e79de939-8f18-4b4a-b15c-21628cb3c961.png)




# STL
import sys
import asyncio
import logging
from urllib.parse import urljoin
from xmlrpc.client import Boolean

# PDM
import aiohttp
from lxml.html import HtmlElement, fromstring
from toolset.FileIO import load_yml_file
from toolset.LogConfig import init_logger
from toolset.LxmlWrapper import sxpath

# logging
from toolset.BaseArgumentParser import base_argument_parser
from toolset.AsyncRabbitPSQLMixin import AsyncRabbitPSQLMixin

URL = "http://books.toscrape.com/"
book_counter = 0

XPATH_MAP = {
    "genres": ".//ul[@class='nav nav-list']/li/ul/li/a/@href",
    "link_to_genre_allbooks": ".//ul[@class='nav nav-list']/li/a",
    "listings": ".//li//h3/a",
}


def twos_complement(hexstr, bits):
    value = int(hexstr, 16)
    if value & (1 << (bits - 1)):
        value -= 1 << bits
    return value


class Scraper(AsyncRabbitPSQLMixin):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.queue = self.config["amqp"]["consumer_queue"]["books_toscrape_test"]["parameters"]["name"]
        self.session = None

    async def start(self, **kwargs):  # the parameters matter
        await super().start(**kwargs)  # initialize connections, network, so await
        self.session = aiohttp.ClientSession()
        # aiohttp doesn't offer a bare get() like requests does,
        # so we need to make a Session in order to access pages

    async def process_main_page(self, main_item)-> Boolean:
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

    def sxpath(self, context: HtmlElement, xpath: str):
        res = context.xpath(xpath, smart_strings=False)
        return res

    def get_element_at_xpath(self, element, xpath):
        return sxpath(element, xpath)

    async def get_page(self, url: str):
        """Wrapper method for turning page response into HTMLElement"""
        async with self.session.get(url) as response:
            text = await response.text()
        return fromstring(text)

    def normalize_book_url_from_gallery(self, url) -> str:
        """Adds the parent directory URL to the specific book URL endings"""
        # ../../../its-only-the-himalayas_981/index.html
        tail_list = url.split("/")
        tail = tail_list[-2] + "/" + tail_list[-1]
        new_url = "https://books.toscrape.com/catalogue/" + tail
        print("normalized url", new_url)
        return new_url

    def get_next_page_tag(self, url) -> str:
        """Collects the URL of the next page if there is one"""
        nextPage_element_xpath = ".//li[@class='next']/a"
        result = sxpath(url, nextPage_element_xpath)
        if result:  # and empty list would be considered falsy
            final_result = str(result[0].attrib["href"])
            return final_result
        else:
            return ""

    def normalize_gallery_url(self, head, tail) -> str:
        """Connects URL extension to main URL"""
        ending = head.split("/")[-1]

        head = head.replace(ending, tail)

        return head

    def get_product_row(self, page):
        """Collect the larger book catalogue from the page"""
        row_element_xpath = ".//section/div/ol[@class='row']"
        result = sxpath(page, row_element_xpath)
        if result:  # and empty list would be considered falsy
            final_result = sxpath(page, row_element_xpath)[0]
            return final_result
        else:
            return None

    def get_name(self, bookpage) -> str:
        """Gets the name from the book page"""
        name_str_xpath = ".//div[@class='col-sm-6 product_main']/h1/text()"
        return sxpath(bookpage, name_str_xpath)[0]

    def get_price(self, bookpage) -> str:
        """Gets the price from the book page"""
        price_str_xpath = (
            ".//div[@class='col-sm-6 product_main']/p[@class='price_color']/text()"
        )
        return sxpath(bookpage, price_str_xpath)[0][2:]

    def get_category(self, bookpage) -> str:
        """Gets the category from the book page"""
        category_str_xpath = ".//ul[@class='breadcrumb']/li/a/text()"
        return sxpath(bookpage, category_str_xpath)[2]

    def get_description(self, bookpage) -> str:
        """Gets the description from the book page"""
        description_str_xpath = ".//article[@class='product_page']/p/text()"
        result = sxpath(bookpage, description_str_xpath)
        if result:  # and empty list would be considered falsy
            final_result = sxpath(bookpage, description_str_xpath)[0]
            return final_result
        else:
            return ""

    def get_product_table(self, bookpage) -> dict:
        """Gets the data table from book page as a dictionary"""
        TABLE_str_xpath = ".//table[@class='table table-striped']"

        table_element = sxpath(bookpage, TABLE_str_xpath)[0]

        heading_str_xpath = "//tr/th/text()"
        result_str_xpath = "//tr/td/text()"

        dict = {}

        for i in range(len(sxpath(table_element, heading_str_xpath))):
            dict[sxpath(table_element, heading_str_xpath)[i]] = sxpath(
                table_element, result_str_xpath
            )[i]

        return dict


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


if __name__ == "__main__":
    parser = base_argument_parser()
    argv = parser.parse_args()
    init_logger(
        argv.log_level,
        argv.log_file,
        argv.log_file_level,
        argv.log_host,
        argv.log_port,
        argv.log_network_level,
    )

    LOG = logging.getLogger(__name__)
    LOG.debug("Logging something detailed you wouldn't normally see")
    LOG.info("Logging a normal thing that happens!")
    LOG.warning("Something might be wrong...")
    LOG.error("Something has gone wrong!")

    LOG.critical("Something has caused the program to fail!")
    main2()

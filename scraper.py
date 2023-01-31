# STL
import json

# PDM
import requests
from lxml.html import HtmlElement, fromstring

from toolset.LxmlWrapper import sxpath

from toolset.RabbitPSQLMixin import RabbitPSQLMixin

# first is module, second is object in module
from toolset.FileIO import load_yml_file

config = load_yml_file("./local_config.yml")
mixin = RabbitPSQLMixin(config=config)


URL = "http://books.toscrape.com/"


class Scraper(RabbitPSQLMixin):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.queue = self.config["amqp"]["consumer_queue"]["books_toscrape_test"][
            "parameters"
        ]["name"]

    def process_main_page(self, URLdict):
        URL = URLdict["URL"]
        mainPage = self.get_page(URL)

        genre_block = self.get_genres(mainPage)

        genre_URLs = []

        for a in genre_block:
            intermediate = a.attrib["href"]
            genre_URLs.append(URL + intermediate)

        for genreURL in genre_URLs:
            genredict = {}
            genredict["genreURL"] = genreURL

            self.publish("genre_page", genredict, self.queue)

        return True

    def process_genre_page(self, genreURL):
        genreURL = genreURL["genreURL"]

        # publish book pages
        # publish next gallery page
        genre_gallery_page = self.get_page(genreURL)
        next_page_tag = self.get_next_page_tag(genre_gallery_page)
        next_gallery_url = self.normalize_gallery_url(genreURL, next_page_tag)

        bookURLs = []
        row = self.get_product_row(genre_gallery_page)
        if row != None:
            listings = self.get_listings(row)
            for a in listings:
                bookURLs.append(a.attrib["href"])

            for bookURL in bookURLs:
                self.publish("book_page", bookURL, self.queue)

        if next_page_tag:
            genredict = {}
            genredict["genreURL"] = next_gallery_url
            self.publish("genre_page", genredict, self.queue)
        return True

    def process_book_page(self, bookURL):
        """Expects an item of the form:
        url: str of url from http://books.toscrape.com"""

        # bookURL = ../../../its-only-the-himalayas_981/index.html
        bookURL = self.normalize_book_url_from_gallery(bookURL)
        # normalized = https://books.toscrape.com/catalogue/its-only-the-himalayas_981/index.html
        bookPage = self.get_page(bookURL)

        name = self.get_name(bookPage)

        category = self.get_category(bookPage)

        price = self.get_price(bookPage)

        description = self.get_description(bookPage)

        product_table = self.get_product_table(bookPage)

        UPC = product_table["UPC"]
        product_type = product_table["Product Type"]
        availability = product_table["Availability"]
        number_of_reviews = product_table["Number of reviews"]

        constructed_book = {
            "name": name,
            "category": category,
            "price": price,
            "description": description,
            "UPC": UPC,
            "product_type": product_type,
            "availability": availability,
            "number_of_reviews": number_of_reviews,
        }
        if self.db is not None:
            with self.db.cursor() as cur:
                cur.execute(
                    "INSERT INTO books (name, category, price, description, UPC, product_type, availability, reviews) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
                    # we don't have to refer to `id` here because it is a serial
                    # serials are generated when you insert, so they're convenient
                    # for data like this
                    (
                        name,
                        category,
                        price,
                        description,
                        UPC,
                        product_type,
                        availability,
                        number_of_reviews,
                    ),
                )
                self.db.commit()

        print(name)
        return True

    def sxpath(self, context: HtmlElement, xpath: str):
        res = context.xpath(xpath, smart_strings=False)
        return res

    def get_page(self, url: str):
        """Wrapper method for turning page response into HtmlElement"""
        response = requests.get(url)
        return fromstring(response.text)

    def normalize_book_url_from_gallery(self, url) -> str:
        """Adds the main URL to the book URLs"""
        # ../../../its-only-the-himalayas_981/index.html
        new_url = url.replace("../../../", "https://books.toscrape.com/catalogue/")
        return new_url

    def get_next_page_tag(self, url) -> str:
        """collects the URL of the next page if there is one"""
        nextPage_element_xpath = ".//li[@class='next']/a"
        result = sxpath(url, nextPage_element_xpath)
        if result:  # and empty list would be considered falsy
            final_result = str(result[0].attrib["href"])
            return final_result
        else:
            return ""

    def normalize_gallery_url(self, head, tail) -> str:
        """Connects URL extension to main URL"""
        head = head.replace("index.html", "")
        return head + tail

    def get_genres(self, page) -> list:
        """collect the list of genres from the left of the main page"""
        genre_element_xpath = ".//ul[@class='nav nav-list']/li/ul/li/a"
        return sxpath(page, genre_element_xpath)

    def get_product_row(self, page):
        """Collect the larger book catalogue from the whole page"""
        row_element_xpath = ".//section/div/ol[@class='row']"
        result = sxpath(page, row_element_xpath)
        if result:  # and empty list would be considered falsy
            final_result = sxpath(page, row_element_xpath)[0]
            return final_result
        else:
            return None

    def get_listings(self, row) -> list:
        """Must recieve the book catalogue"""
        listing_str_xpath = ".//li//h3/a"
        return sxpath(row, listing_str_xpath)

    def get_name(self, bookpage) -> str:
        """gets the name from the book page"""
        name_str_xpath = ".//div[@class='col-sm-6 product_main']/h1/text()"
        return sxpath(bookpage, name_str_xpath)[0]

    def get_price(self, bookpage) -> str:
        """gets the price from the book page"""
        price_str_xpath = (
            ".//div[@class='col-sm-6 product_main']/p[@class='price_color']/text()"
        )
        return sxpath(bookpage, price_str_xpath)[0][2:]

    def get_category(self, bookpage) -> str:
        """gets the category from the book page"""
        category_str_xpath = ".//ul[@class='breadcrumb']/li/a/text()"
        return sxpath(bookpage, category_str_xpath)[2]

    def get_description(self, bookpage) -> str:
        """gets the description from the book page"""
        description_str_xpath = ".//article[@class='product_page']/p/text()"
        result = sxpath(bookpage, description_str_xpath)
        if result:  # and empty list would be considered falsy
            final_result = sxpath(bookpage, description_str_xpath)[0]
            return final_result
        else:
            return ""

    def get_product_table(self, bookpage) -> dict:
        """gets the data table from book page as a dictionary"""
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


class Book:
    def __init__(
        self,
        name,
        price,
        category,
        description,
        UPC,
        product_type,
        availability,
        reviews,
    ):
        self.name = name
        self.price = price
        self.category = category
        self.description = description
        self.UPC = UPC
        self.product_type = product_type
        self.availability = availability
        self.reviews = reviews


def main():

    config = load_yml_file("./local_config.yml")
    scraper = Scraper(config=config)

    scraper.start()

    URLdict = {}
    URLdict["URL"] = URL
    scraper.publish("main_page", URLdict, scraper.queue)

    scraper.register("main_page", scraper.process_main_page)

    scraper.register("genre_page", scraper.process_genre_page)

    scraper.register("book_page", scraper.process_book_page)

    scraper.run()


main()

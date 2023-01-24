# STL
import json

# PDM
import requests
from lxml.html import HtmlElement, fromstring


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


URL = "http://books.toscrape.com/"


def sxpath(context: HtmlElement, xpath: str):
    res = context.xpath(xpath, smart_strings=False)
    return res


def get_page(url: str):
    """Wrapper method for turning page response into HtmlElement"""
    response = requests.get(url)
    return fromstring(response.text)


def normalize_book_url_from_gallery(url) -> str:
    """Adds the main URL to the book URLs"""
    # ../../../its-only-the-himalayas_981/index.html
    new_url = url.replace("../../../", "https://books.toscrape.com/catalogue/")
    return new_url


def get_next_page_tag(url) -> str:
    """collects the URL of the next page if there is one"""
    nextPage_element_xpath = ".//li[@class='next']/a"
    result = sxpath(url, nextPage_element_xpath)
    if result:  # and empty list would be considered falsy
        final_result = str(result[0].attrib["href"])
        return final_result
    else:
        return ""


def normalize_gallery_url(head, tail) -> str:
    """Connects URL extension to main URL"""
    head = head.replace("index.html", "")
    return URL + head + tail


def get_genres(page) -> list:
    """collect the list of genres from the left of the main page"""
    genre_element_xpath = ".//ul[@class='nav nav-list']/li/ul/li/a"
    return sxpath(page, genre_element_xpath)


def get_product_row(page) -> str:
    """Collect the larger book catalogue from the whole page"""
    row_element_xpath = ".//section/div/ol[@class='row']"
    return sxpath(page, row_element_xpath)[0]


def get_listings(row) -> list:
    """Must recieve the book catalogue"""
    listing_str_xpath = ".//li//h3/a"
    return sxpath(row, listing_str_xpath)


def get_name(bookpage) -> str:
    """gets the name from the book page"""
    name_str_xpath = ".//div[@class='col-sm-6 product_main']/h1/text()"
    return sxpath(bookpage, name_str_xpath)[0]


def get_price(bookpage) -> str:
    """gets the price from the book page"""
    price_str_xpath = (
        ".//div[@class='col-sm-6 product_main']/p[@class='price_color']/text()"
    )
    return sxpath(bookpage, price_str_xpath)[0][2:]


def get_category(bookpage) -> str:
    """gets the category from the book page"""
    category_str_xpath = ".//ul[@class='breadcrumb']/li/a/text()"
    return sxpath(bookpage, category_str_xpath)[2]


def get_description(bookpage) -> str:
    """gets the description from the book page"""
    description_str_xpath = ".//article[@class='product_page']/p/text()"
    result = sxpath(bookpage, description_str_xpath)
    if result:  # and empty list would be considered falsy
        final_result = sxpath(bookpage, description_str_xpath)[0]
        return final_result
    else:
        return ""


def get_product_table(bookpage) -> dict:
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


def main():
    url = "http://books.toscrape.com/"
    page = get_page(url)

    genres_ul = get_genres(page)

    genre_urls = []
    for a in genres_ul:
        genre_urls.append(a.attrib["href"])

    data = {}

    bookURLs = []
    for genre_url in genre_urls:

        genre_gallery_page = get_page(url + genre_url)

        next_gallery_page_url_tag = get_next_page_tag(genre_gallery_page)
        next_gallery_url = normalize_gallery_url(genre_url, next_gallery_page_url_tag)

        print("first genre url: " + str(genre_url))

        row = get_product_row(genre_gallery_page)
        listings = get_listings(row)
        for a in listings:
            bookURLs.append(a.attrib["href"])

        while next_gallery_page_url_tag:
            print(next_gallery_url)
            current_page = get_page(next_gallery_url)
            row = get_product_row(current_page)
            listings = get_listings(row)
            for a in listings:
                bookURLs.append(a.attrib["href"])
            next_gallery_page_url_tag = get_next_page_tag(current_page)
            next_gallery_url = normalize_gallery_url(
                genre_url, next_gallery_page_url_tag
            )

    i = 0
    books = []
    for bookURL in bookURLs:
        # bookURL = ../../../its-only-the-himalayas_981/index.html
        bookURL = normalize_book_url_from_gallery(bookURL)
        # normalized = https://books.toscrape.com/catalogue/its-only-the-himalayas_981/index.html
        bookPage = get_page(bookURL)

        category = get_category(bookPage)

        name = get_name(bookPage)

        price = get_price(bookPage)

        description = get_description(bookPage)

        product_table = get_product_table(bookPage)

        book = Book(
            name,
            price,
            category,
            description,
            product_table["UPC"],
            product_table["Product Type"],
            product_table["Availability"],
            product_table["Number of reviews"],
        )

        books.append(book)

        print(i)
        i += 1

    total = 0
    for book in books:
        total += float(book.price)
    average = total / len(books)

    print("The average price is {}".format(average))


main()

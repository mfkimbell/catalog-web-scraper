from toolset.RabbitPSQLMixin import RabbitPSQLMixin
from scraper import Scraper
import asyncio
from urllib.parse import urljoin
from lxml.html import fromstring
from toolset.FileIO import load_yml_file
from toolset.LxmlWrapper import sxpath
from toolset.AsyncRabbitPSQLMixin import AsyncRabbitPSQLMixin
from toolset.BaseArgumentParser import base_argument_parser
from toolset.LogConfig import init_logger

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

# logging
from toolset.BaseArgumentParser import base_argument_parser
import logging
from toolset.LogConfig import init_logger

# first is module, second is object in module
from toolset.FileIO import load_yml_file

URL = "http://books.toscrape.com/"


def main():
    LOG.info("Start of kicker file")
    LOG = logging.getLogger(__name__)

    config = load_yml_file("./local_config.yml")

    loop = asyncio.get_event_loop()
    scraper = Scraper(config=config, loop=loop)
    loop.run_until_complete(scraper.start())

    URLdict = {}
    URLdict["URL"] = URL
    loop.run_until_complete(scraper.publish("main_page", URLdict, scraper.queue))
    LOG.info("End of kicker file")


if __name__ == "__main__":
    main()

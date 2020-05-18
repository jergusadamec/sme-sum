import argparse
from multiprocessing.pool import ThreadPool
from time import sleep

import numpy as np
import requests
from bs4 import BeautifulSoup
from requests import RequestException

from src import utils

LOGGER = utils.get_logger('sme-archive-downloader')


def parse_args ():
	arg_parser = argparse.ArgumentParser(description='Parser')

	arg_parser.add_argument('--output-file-archive-url', type=str, metavar='output_file_archive_url', default='sme-archive-urls.txt',
							help='Pass filename used for writing urls obtained from wayback archive of SME news portal.')

	arg_parser.add_argument('--sme-content-menu-url', type=str, metavar='sme_content_menu_url', default='https://www.sme.sk/najnovsie?page={}',
							help='Define a url for web scraping in news portal SME.')

	arg_parser.add_argument('--wayback-archive-api-url', type=str, metavar='wayback_archive_api_url', default='https://archive.org/wayback/available?url={}',
							help='Define an endpoint of Wayback archive, which is used for getting an archived URL linking to a particular SME article.')

	arg_parser.add_argument('--n-thread', type=int, metavar='n_thread', default=1,
							help='Number of concurent thread for making a request.')

	arg_parser.add_argument('--start-page-number', type=int, metavar='start_page_number', default=100,
							help='Start page number of query parameter in SME url.')

	arg_parser.add_argument('--end-page-number', type=int, metavar='end_page_number', default=12500,
							help='End page number.')

	return arg_parser.parse_args()


def is_wayback_archive_available (archive_json):
	try:
		closest = archive_json['archived_snapshots']['closest']
		return closest['available'], closest['url']
	except KeyError:
		return False, None


def extract_urls_from_sme_menu_content (html_page):
	sme_archive_urls = []
	soup = BeautifulSoup(html_page, 'html.parser')
	menu_content = soup.findAll("div", {"class": "media media-two-cols cf"})
	for ix in range(len(menu_content)):
		news = menu_content[ix]
		news_url = news.contents[1].attrs['href']
		archive_news_url = args.wayback_archive_api_url.format(news_url)
		try:
			sleep(np.random.randint(5, 10))  # sleep for # seconds to avoid exceeding the API limit

			archive_news_response = requests.get(archive_news_url, timeout=6)
			if not archive_news_response.ok:
				print('ERROR', archive_news_url)
				break
			is_available, url = is_wayback_archive_available(archive_news_response.json())
			if is_available:
				print(url)
				sme_archive_urls.append(url)

		except RequestException as e:
			message = 'RequestException extract_urls_from_sme_menu_content at ix: ' + str(ix)
			LOGGER.info(message + str(e.message)) if hasattr(e, 'message') else LOGGER.info(message + str(e))

	return sme_archive_urls


def download_urls (page_number):
	try:
		response = requests.get(args.sme_content_menu_url.format(page_number), timeout=6)
		html_page = response.text
		sme_archive_urls = extract_urls_from_sme_menu_content(html_page)

		utils.write_files(sme_archive_urls, out_filename=args.output_file_archive_url)
		print('Page number: {} DONE'.format(page_number))

		sleep(np.random.randint(5, 10))  # sleep for # seconds to avoid exceeding the API limit

	except RequestException as e:
		message = 'RequestException at page number: ' + str(page_number)
		LOGGER.info(message + str(e.message)) if hasattr(e, 'message') else LOGGER.info(message + str(e))


if __name__ == "__main__":
	args = parse_args()

	with ThreadPool(args.n_thread) as pool:
		list(pool.imap_unordered(
				download_urls,
				(t for t in range(args.start_page_number, args.end_page_number)),
				chunksize=1
		))

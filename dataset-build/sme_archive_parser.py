import argparse
import re
from multiprocessing.pool import ThreadPool
from time import sleep

import numpy as np
import requests
from bs4 import BeautifulSoup
from requests import RequestException

from src import config
from src import utils

LOGGER = utils.get_logger('sme-archive-parser')


def parse_args ():
	arg_parser = argparse.ArgumentParser(description='Parser')

	arg_parser.add_argument('--input-file-archive-url', type=str, metavar='input_file_archive_url', default='sme-archive-urls.txt',
							help='Filled file from predecessor step. Parser will try to extract content for each url from that file.')

	arg_parser.add_argument('--output-dir-extracted-raw-content', type=str, metavar='output_dir_extracted_raw_content', default='/sme-archive-extracted-raw-content',
							help='Under this dir parser create files with extracted content from SME sites.')

	arg_parser.add_argument('--output-file-archive-premium-url', type=str, metavar='output_file_archive_premium_url', default='sme-archive-urls-premium.txt',
							help='Pass filename used for writing premium urls obtained from wayback archive of SME news portal. This sites will be not used in next steps - just for informations purposes.')

	arg_parser.add_argument('--output-file-archive-failed-url', type=str, metavar='output_file_archive_failed_url', default='sme-archive-urls-failed.txt',
							help='Pass filename used for writing failed urls obtained from wayback archive of SME news portal.')

	arg_parser.add_argument('--n-thread', type=int, metavar='n_thread', default=1,
							help='Number of concurent thread for making a request.')

	return arg_parser.parse_args()


class PremiumSiteError (ValueError):
	def __init__ (self, message):
		super().__init__(message)


def is_premium_page (soup_html):
	return len(soup_html.findAll("div", {"class": "editorial-promo"})) != 0


def parse_html (beautiful_soup):
	if is_premium_page(beautiful_soup):
		raise PremiumSiteError('Premium site')
	title = beautiful_soup.findAll("div", {"class": "article-heading"})[0].text
	introduction = beautiful_soup.findAll("p", {"class": "perex"})[0].text
	menu_content = beautiful_soup.find("article")
	paragraphs = menu_content.findAll('p')
	document = ' '.join([p.text for p in paragraphs if p.attrs == {}])

	return {
		'title': 		title,
		'introduction': introduction,
		'document': 	document
	}


def preprocess_warchived_url (url):
	sleep(np.random.randint(5, 9)) # sleep for # seconds to avoid exceeding the API limit

	sme_index = re.search('c/(.+?)/', url)
	category_regex = re.search('/https://(.+?).sme', url)
	if sme_index and category_regex:
		sme_index = sme_index.group(1)
		category = category_regex.group(1)
	else:
		raise ValueError('SME article index or category not found')
	try:
		response = requests.get(url, timeout=10)
		if not response.ok:
			raise ValueError('Http status code error arise')
		results_json = parse_html(BeautifulSoup(response.text, 'html.parser'))
		results_json['category'] = category
		results_json['url'] = url

		print(url)
		utils.write_json(results_json, out_filename=sme_index + '.json', path=config.RESORCES_DIR + args.output_dir_extracted_raw_content)

	except RequestException as e:
		message = 'RequestException in file with index: ' + str(sme_index)
		LOGGER.info(message + str(e.message)) if hasattr(e, 'message') else LOGGER.info(message + str(e))
		utils.write_file(url, out_filename=args.output_file_archive_failed_url, mode='a', path=config.RESORCES_DIR)

	except PremiumSiteError as e:
		message = 'PremiumSiteError in file with index: ' + str(sme_index)
		LOGGER.info(message + str(e.message)) if hasattr(e, 'message') else LOGGER.info(message + str(e))
		utils.write_file(url, out_filename=args.output_file_archive_premium_url, mode='a', path=config.RESORCES_DIR)

	except ValueError as e:
		message = 'ValueError in file with index: ' + str(sme_index)
		LOGGER.info(message + str(e.message)) if hasattr(e, 'message') else LOGGER.info(message + str(e))

	except IndexError as e:
		message = 'IndexError in file with index - Title not found: ' + str(sme_index)
		LOGGER.info(message + str(e.message)) if hasattr(e, 'message') else LOGGER.info(message + str(e))

	except AttributeError as e:
		message = 'AttributeError in file with index - Title not found: ' + str(sme_index)
		LOGGER.info(message + str(e.message)) if hasattr(e, 'message') else LOGGER.info(message + str(e))


if __name__ == "__main__":
	args = parse_args()
	print('Number of urls: ', len(list(utils.load_sme_archives_urls_as_generator(filename=args.input_file_archive_url))))

	with ThreadPool(args.n_thread) as pool:
		list(pool.imap_unordered(
				preprocess_warchived_url,
				utils.load_sme_archives_urls_as_generator(filename=args.input_file_archive_url),
				chunksize=1
		))


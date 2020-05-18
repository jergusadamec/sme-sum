import argparse
import os
import re
from json import JSONDecodeError
from multiprocessing.pool import Pool

import pycld2
from polyglot.text import Text

from src import config
from src import lemmsk
from src import utils

'''
	lemmsk package borrowed from https://github.com/mrshu/lemm-sk

	stop words accesible at: https://github.com/SlovakNationalGallery/elasticsearch-slovencina/blob/master/stop-words/stop-words-slovak.txt
'''

LOGGER = utils.get_logger('sme-archive-postprocessing')


def parse_args ():
	arg_parser = argparse.ArgumentParser(description='Parser')

	arg_parser.add_argument('--input-dir-extracted-raw-content', type=str, metavar='input_dir_extracted_raw_content', default='/sme-archive-extracted-raw-content',
							help='Under this directory are files with extracted content of SME sites.')

	arg_parser.add_argument('--output-dir-preprocessed', type=str, metavar='output_dir_preprocessed', default='/sme-archive-preprocessed',
							help='Destination directory of preprocessed raw files.')

	arg_parser.add_argument('--stop_words_sk', type=str, metavar='stop_words_sk', default='stop-words-sk.txt',
							help='Stop words of Slovak language.')

	arg_parser.add_argument('--n-thread', type=int, metavar='n_thread', default=1,
							help='Number of concurent thread for making a request.')

	return arg_parser.parse_args()


def _remove_punctuation (content):
	return re.sub(r'[!"´#$%&\'()*+,./:;<=>?@[\]^`{|}~]', '', content)


def _remove_numbers (content):
	return re.sub(r'\d+', '', content)


def _preprocess (file):
	text = Text(file, hint_language_code='sk')
	res = []
	for sent in text.sentences:
		tokens = [_remove_punctuation(token) for token in sent.tokens if _remove_punctuation(token) != '']
		tokens = [token.lower() for token in tokens]
		tokens = [_remove_numbers(token) for token in tokens]
		tokens = [token for token in tokens if token not in STOP_WORDS]
		tokens = [token for token in tokens if len(token) > 1]
		res.extend(tokens)

	return ' '.join(res)


def _lemmatize (data):
	res = []
	sentences = _preprocess(data)
	for word in sentences.split(' '):
		stem = lemmsk.lemmatize(word)
		res.append(stem)

	return ' '.join(res)


def preprocess (filename):
	LOGGER.info('processing ' + filename)
	try:
		file = utils.read_json(filename, path=config.RESORCES_DIR + args.input_dir_extracted_raw_content)
		file['title'] = _preprocess(file['title'])
		file['introduction'] = _preprocess(file['introduction'])
		file['document'] = _preprocess(file['document'])
		file['document_lemma'] = _lemmatize(file['document'])

		utils.write_json(file, out_filename=filename, path=config.RESORCES_DIR + args.output_dir_preprocessed)

	except pycld2.error as e:
		message = 'pycld2.error with filename: ' + str(filename)
		LOGGER.info(message + str(e.message)) if hasattr(e, 'message') else LOGGER.info(message + str(e))

	except JSONDecodeError as e:
		message = 'JSONDecodeError with filename: ' + str(filename)
		LOGGER.info(message + str(e.message)) if hasattr(e, 'message') else LOGGER.info(message + str(e))

	except ValueError as e:
		message = 'ValueError in file with index: ' + str(filename)
		LOGGER.info(message + str(e.message)) if hasattr(e, 'message') else LOGGER.info(message + str(e))


if __name__ == "__main__":
	args = parse_args()

	if args.n_thread == -1:
		args.n_thread = os.cpu_count()

	STOP_WORDS = utils.read_file(args.stop_words_sk).split('\n')
	dir_scans = os.scandir(path=config.RESORCES_DIR + args.input_dir_extracted_raw_content)

	with Pool(args.n_thread) as pool:
		list(pool.imap_unordered(
				preprocess,
				(dir_scan.name for dir_scan in dir_scans),
				chunksize=1
		))






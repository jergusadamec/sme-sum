import logging
from pyparsing import basestring
from src import config
import csv
import os
import numpy as np
import json
import itertools


def get_logger (name, log_to_file=False, file_log_name='log.txt'):
	logger = logging.getLogger(name)
	if not logger.handlers:
		logger.setLevel(logging.INFO)
		formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
		ch = logging.StreamHandler()
		ch.setLevel(logging.INFO)
		ch.setFormatter(formatter)
		logger.addHandler(ch)

		if log_to_file:
			fh = logging.FileHandler(config.RESORCES_DIR + '/' + file_log_name, mode='w')
			fh.setLevel(logging.INFO)
			fh.setFormatter(formatter)
			logger.addHandler(fh)

	return logger


def load_sme_archives_urls_as_generator (filename, path=config.RESORCES_DIR):
	fullpath = os.path.join(path, filename)
	with open(fullpath, 'r') as f:
		line = f.readline()
		while line:
			yield line
			line = f.readline()


def read_file (filename, path=config.RESORCES_DIR, mode='r'):
	filename = os.path.join(path, filename)
	with open(filename, mode) as f:
		return f.read()


def write_files (contents, out_filename, path=config.RESORCES_DIR, mode='a'):
	if not os.path.isdir(path):
		os.mkdir(path)
	filename = os.path.join(path, out_filename)
	with open(filename, mode) as f:
		for content in contents:
			f.write(content + '\n')


def write_file (content, out_filename, path=config.RESORCES_DIR, mode='a'):
	if not os.path.isdir(path):
		os.mkdir(path)
	filename = os.path.join(path, out_filename)
	with open(filename, mode) as f:
		f.write(content)


def write_json (json_file, out_filename, path=config.RESORCES_DIR, mode='w'):
	if not os.path.isdir(path):
		os.mkdir(path)
	filename = os.path.join(path, out_filename)
	with open(filename, mode) as f:
		json.dump(json_file, f)


def read_json (json_file, path=config.RESORCES_DIR, mode='r'):
	json_file = os.path.join(path, json_file)
	with open(json_file, mode) as f:
		return json.load(f)


def to_flat_list (array):
	return list(itertools.chain(*array))


def to_json (o, level=0):
	INDENT = 3
	SPACE = " "
	NEWLINE = "\n"
	ret = ""
	if isinstance(o, dict):
		ret += "{" + NEWLINE
		comma = ""
		for k, v in o.items():
			ret += comma
			comma = ",\n"
			ret += SPACE * INDENT * (level + 1)
			ret += '"' + str(k) + '":' + SPACE
			ret += to_json(v, level + 1)

		ret += NEWLINE + SPACE * INDENT * level + "}"
	elif isinstance(o, basestring):
		ret += '"' + o + '"'
	elif isinstance(o, list):
		if isinstance(iter(o).__next__(), np.ndarray) or isinstance(iter(o).__next__(), list):
			ret += "[" + NEWLINE
			comma = ""
			for v in o:
				ret += comma
				comma = ",\n"
				ret += SPACE * INDENT * (level + 1)
				ret += to_json(v, level + 1)
			ret += NEWLINE + SPACE * INDENT * level + "]"
		else:
			ret += "[" + ",".join([to_json(e, level + 1) for e in o]) + "]"
	elif isinstance(o, bool):
		ret += "true" if o else "false"
	elif isinstance(o, int):
		ret += str(o)
	elif isinstance(o, float):
		ret += '%.7g' % o
	elif isinstance(o, np.ndarray) and np.issubdtype(o.dtype, np.integer):
		ret += "[" + ','.join(map(str, o.flatten().tolist())) + "]"
	elif isinstance(o, np.ndarray) and np.issubdtype(o.dtype, np.inexact):
		ret += "[" + ','.join(map(lambda x: '%.7g' % x, o.flatten().tolist())) + "]"
	elif o is None:
		ret += 'null'
	elif isinstance(o, tuple):
		ret += "[" + ",".join([to_json(e, level + 1) for e in o]) + "]"
	else:
		raise TypeError("Unknown type '%s' for json serialization" % str(type(o)))

	return ret

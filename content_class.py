#!/usr/bin/python3

import re
import numpy as np

import sys


RE_NUMBER = re.compile('^[\-]?([0-9]*,?)*[0-9]*\.?[0-9]*$')

RE_NO_NUMBER = re.compile('[a-z,A-Z]')

RE_ENGLISH = re.compile('^[a-z,A-Z,\-,\s,\'.]*$')

RE_GEO_COMLETE = re.compile('^(([a-z,A-Z,\-,\'.\,]*|[0-9]*)(\s|$)+)*$')

RE_NO_RUBBISH = re.compile('.*[a-z,A-Z,0-9].*')

VALID_TOP_LEVELS = ['en', 'us', 'au', 'de', 'at', 'ch', 'org', 'com', 'edu', 'net', 'gov']

class PreClass:
	UNVALID, VALID, NUMBER, GEO, NUMBER_TEXT, EMPTY = range(6) 

def pre_classify(elem):
	if (elem == '' or elem == '-'):
		return PreClass.EMPTY
	if elem.isdigit():
		return PreClass.NUMBER
	if (len(elem) < 2) or (not no_rubbish(elem)):
		return PreClass.UNVALID
	if number_text(elem):
		if number(elem):
			return PreClass.NUMBER
		else:
			return PreClass.NUMBER_TEXT
	if geo(elem):
		return PreClass.GEO
	return PreClass.VALID

def no_rubbish(elem):
	if RE_NO_RUBBISH.match(elem):
		return True
	else:
		return False

def number_text(elem):
	counts = np.bincount([x.isdigit() for x in elem])
	if len(counts) > 1:
		if counts[1] >= counts[0]:
			return True
	return False


def number(elem):
	if RE_NUMBER.match(elem):
		return True
	else:
		return False

def english_phrase(elem):
	if RE_ENGLISH.match(elem):
		return True
	return False

def geo(elem):
	if RE_GEO_COMLETE.match(elem):
		return True
	return False

def get_distribution(column):
	classes = [0]*5
	for cell in column:
		pre_class = pre_classify(cell)
		if pre_class != PreClass.EMPTY:
			classes[pre_class] += 1
	return classes

def main(argc, argv):
	print(get_distribution(['asdfa', 'asdf', '234', '2342-2asdf', 'a'])[PreClass.GEO]);

if __name__ == "__main__":
	main(len(sys.argv), sys.argv)

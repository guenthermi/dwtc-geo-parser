
import re
import numpy as np
from urllib.parse import urlparse

from reader import *
import sys

RE_NUMBER = re.compile('^[\-]?([0-9]*,?)*[0-9]*\.?[0-9]*$')

RE_NO_NUMBER = re.compile('[a-z,A-Z]')

RE_ENGLISH = re.compile('^[a-z,A-Z,\-,\s,\'.]*$')

RE_GEO_COMLETE = re.compile('^(([a-z,A-Z,\-,\'.\,]*|[0-9]*)(\s|$)+)*$')

RE_NO_RUBBISH = re.compile('.*[a-z,A-Z,0-9].*')

VALID_TOP_LEVELS = ['en', 'us', 'au', 'de', 'at', 'ch', 'org', 'com', 'edu', 'net', 'gov']

class PreClass:
	UNVALID, VALID, NUMBER, GEO = range(4) 

def pre_classify(elem):
	if elem.isdigit():
		return PreClass.NUMBER
	if (len(elem) < 2) or (not no_rubbish(elem)):
		return PreClass.UNVALID
	if number(elem):
		return PreClass.NUMBER
	if geo(elem):
		return PreClass.GEO
	return PreClass.VALID

def no_rubbish(elem):
	if RE_NO_RUBBISH:
		return True
	else:
		return False

def number(elem):
	if RE_NUMBER.match(elem):
		return True
	return False

def english_phrase(elem):
	if RE_ENGLISH.match(elem):
		return True
	return False

def geo(elem):
	if RE_GEO_COMLETE.match(elem):
		return True
	return False

def process(table, url):
	# possible geo columns
	result = {'columns': [], 'column_indices':[]}

	# TODO determine table direction
	quality = weight_quality(table, url)
	if not quality:
		return None, None, None

	# detect rubbish rows and columns
	rubbish_rows, rubbish_cols = detect_rubbish(table)

	# determine header, rubish rows
	headers = guess_header_positions(table, rubbish_rows, rubbish_cols)

	# remove rubbish rows and headers
	result = cleanup_table(table, rubbish_rows, rubbish_cols, headers)

	return result, headers, rubbish_rows

def weight_quality(table, url):
	if len(table[0]) <= 5:
		return False
	# check top level domain
	if urlparse(url).hostname.split('.')[-1] not in VALID_TOP_LEVELS:
		return False
	if measure_col_consistence(table) <= 0.5:
		return False
	return detect_table_direction(table)

def detect_table_direction(table):
	direction = 0
	horizontal_count = 0
	vertical_count = 0
	for col in table:
		classes = []
		for cell in col:
			classes.append(pre_classify(cell))
		horizontal_count += max(np.bincount(classes))
	transpose = [list(i) for i in zip(*table)]
	for row in transpose:
		classes = []
		for cell in row:
			classes.append(pre_classify(cell))
		vertical_count += max(np.bincount(classes))
	return (horizontal_count > vertical_count)

def measure_col_consistence(table):
	count = 0
	table_size = 0
	for col in table:
		classes = []
		for cell in col:
			classes.append(pre_classify(cell))
		bin_counts = np.bincount(classes)
		max_count = max(bin_counts)
		if list(bin_counts).index(max_count) != PreClass.UNVALID:
			if (max_count / len(col)) >= 0.7:
				count += 1
			table_size += 1
	if table_size == 0:
		return 0
	else:
		return count / table_size

def cleanup_table(table, rubbish_rows, rubbish_cols, headers):
	result = {'columns': [], 'column_indices': []}

	for i, col in enumerate(table):
		newcol =  ([],[])
		count = 0
		for j, cell in enumerate(col):
			if (not (j in rubbish_rows)) and (not (j in headers)):
				if pre_classify(cell) == PreClass.GEO:
					newcol[0].append(cell)
					newcol[1].append(j)
		if len(set(newcol[0])) > 1:
			result['columns'].append(newcol)
			result['column_indices'].append(i)
	return result

def guess_header_positions(table, rubbish_rows, rubbish_cols):
	interpretations = [] # col classification
	for i, col in enumerate(table):
		if not (i in rubbish_cols):
			classes = []
			for j, cell in enumerate(col):
				if not (j in rubbish_rows):
					classes.append(pre_classify(cell))
			counts = np.bincount(classes)
			if (len(counts))> 1:
				interpretations.append(np.argmax(counts[1:])+1)
			else:
				interpretations.append(0)
		else:
			interpretations.append(0)
	headers = determine_headers(table, interpretations)
	return headers

def detect_rubbish(table):
	rubbish_rows = set()
	rubbish_cols = set()
	# row-wise representation
	transpose = [list(i) for i in zip(*table)]

	# delete all rows that contain rubbish
	rubbish_rates = determine_rubbish_column_rates(table)
	rubbish_rows = set()
	for i, row in enumerate(transpose):
		row_classification = classify_line(row)
		counts = np.bincount(row_classification)
		unvalid = False
		if counts[PreClass.UNVALID] > (len(row) / 2):
			for j, elem in enumerate(row):
				if (row_classification[j] == PreClass.UNVALID) and (rubbish_rates[j] < 0.5): # TODO replace 0.5 with meridian value
					unvalid = True
		if unvalid:
			rubbish_rows.add(i)
	# remove rubbish rows -> new_transpose
	new_transpose = {'rows': [], 'indices': []}
	for i in range(len(transpose)):
		if not (i in rubbish_rows):
			new_transpose['rows'].append(transpose[i])
			new_transpose['indices'].append(i)
	# remove rubbish cols
	new_table = [list(i) for i in zip(*new_transpose['rows'])]
	for i, col in enumerate(new_table):
		classification = classify_line(col)
		if np.argmax(np.bincount(classification)) == PreClass.UNVALID:
			rubbish_cols.add(i)
	return rubbish_rows, rubbish_cols

def classify_line(line):
	result = []
	for i, elem in enumerate(line):
		result.append(pre_classify(elem))
	return result

def determine_headers(table, classes):
	result = dict()
	has_numbers = PreClass.NUMBER in classes
	transpose = [list(i) for i in zip(*table)]
	for i, row in enumerate(transpose):
		count = 0
		others = 0
		non_unvalid = False
		for j, cell in enumerate(row):
			if classes[j] != 0:
				cl = pre_classify(cell)
				if cl != PreClass.UNVALID:
					non_unvalid = True
				if classes[j] != cl:
					if (classes[j] == PreClass.NUMBER) and (cell != ''):
						count += 2
					else:
						if (cell == ''):
							count += 0.2
							others += 0.8
					if (cl == PreClass.GEO) and (classes[j] == PreClass.VALID):
						count += 0
					if (cl == PreClass.UNVALID) and (not has_numbers):
						count += 0.4
				else:
					others +=1
		if non_unvalid:
			if count > 2:
				result[i] = row
			else:
				if (count == 2) and (others > 0) and ((i / len(transpose)) > 0.9 or ((i / len(transpose)) < 0.1)):
					result[i] = row

	return result

def determine_rubbish_column_rates(table):
	result = []

	for col in table:
		rubishCount = 0
		for elem in col:
			if pre_classify(elem) == PreClass.UNVALID:
				rubishCount += 1
		result.append(rubishCount / len(col))
	return result

def main(argc, argv):
	reader = TableReader(argv[1])
	table = reader.get_next_table()
	while (table):
		line_count = reader.getLineCount()
		if line_count == int(argv[2]):
			print('get here')
			table['relation']
			print(process(table['relation']))
			break
		table = reader.get_next_table()

if __name__ == "__main__":
	main(len(sys.argv), sys.argv)

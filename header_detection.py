#!/usr/bin/python3

import re
import string
import numpy as np
from collections import Counter
import matplotlib.pyplot as plt

import sys

from reader import *
from databaseOutput import *

PATTERN_SIZE = 7

def _get_content_type(c):
	if c in [str(x) for x in range(10)]:
		return 'N'
	if c in string.ascii_letters:
		return 'A'
	if c in '.!;():?,\\-\'"':
		return 'P'
	return 'S'

def _get_content_pattern(text):
	clean_text = ''.join(text.split())
	pattern = ['X']*PATTERN_SIZE
	for i, c in enumerate(clean_text):
		if i >= PATTERN_SIZE:
			break
		pattern[i] = _get_content_type(c)
	return pattern

def _pattern_average(column):
	patterns = [_get_content_pattern(x) for x in column]
	counts = [Counter(list(i)).most_common() for i in zip(*patterns)]
	weights, sums = _weight_pattern_counts(counts)
	distribution = [dict([(x, y / sums[i]) for (x,y) in z]) for i, z in enumerate(weights)]
	return distribution

def _weight_pattern_counts(counts):
	weights = dict({
		'N': 8,
		'P': 4,
		'S': 4,
		'A': 2,
		'X': 1
		})
	new_counts = []
	sums = []
	for pattern in counts:
		new_pattern = []
		weights_sum = 0
		for (char, value) in pattern:
			new_pattern.append((char, weights[char]*value))
			weights_sum += weights[char]*value
		sums.append(weights_sum)
		new_counts.append(new_pattern)
	return new_counts, sums

def _similarity(row, average_patterns):
	count = 0
	for i, cell in enumerate(row):
		pattern = _get_content_pattern(cell)
		for j in range(PATTERN_SIZE):
			if pattern[j] in average_patterns[i][j]:
				count += average_patterns[i][j][pattern[j]]
	return count / (len(row) * PATTERN_SIZE)

def _get_row_similarities(table):
	average_patterns = [_pattern_average(col) for col in table]
	transpose = [list(i) for i in zip(*table)]
	result = dict()
	hist = []
	for i, row in enumerate(transpose):
		sim = _similarity(row, average_patterns)
		hist.append(sim)
		result[i] = sim
	return result, hist

def _k_means(sims):
	if len(sims.values()) == 0:
		return (dict(), dict()), (0,0)
	# init
	mean_1 = max(sims.values())
	mean_2 = min(sims.values())
	class_1 = []
	class_2 = []
	
	MAX_ITERATION = 10
	for i in range(MAX_ITERATION):
		# classify
		for row in sims:
			if abs(sims[row]-mean_1) < abs(sims[row]-mean_2):
				class_1.append((row, sims[row]))
			else:
				class_2.append((row, sims[row]))

		# udpate means
		mean_1 = 0
		mean_2 = 0
		for (k,v) in class_1:
			mean_1 += v / len(class_1)
		for (k,v) in class_2:
			mean_2 += v / len(class_2)

	# construct result
	result = (dict(), dict())
	for (k, v) in class_1:
		result[0][k] = v
	for (k, v) in class_2:
		result[1][k] = v
	return result, (mean_1, mean_2)

def _get_empty_cols(table):
	empty_cols = []
	for i, col in enumerate(table):
		is_empty = True
		for cell in col:
			if cell != '':
				is_empty = False
				break
		if is_empty:
			empty_cols.append(i)
	return set(empty_cols)

def _get_clear_table(table):
	empty_cols = _get_empty_cols(table)
	empty_rows = _get_empty_cols([list(i) for i in zip(*table)])
	clear_table = []
	col_indices = list(filter(lambda x: x not in empty_cols, range(len(table))))
	row_indices = list(filter(lambda x: x not in empty_rows, range(len(table[0]))))
	for i, col in enumerate(table):
		if i in empty_cols:
			continue
		new_col = []
		for j, cell in enumerate(col):
			if j in empty_rows:
				continue
			new_col.append(cell)
		clear_table.append(new_col)
	return clear_table, col_indices, row_indices, empty_rows

def detect_headers(table):
	clear_table, col_indices, row_indices, empty_rows = _get_clear_table(table)	
	sims, hist = _get_row_similarities(clear_table)
	# show_histogram(hist)
	result, means = _k_means(sims)

	# check if headers could be detected
	if (len(result[1]) > 5) and (len(result[1])*5 > len(result[0])):
		if means[1] > 0.8:
			return dict(),[], empty_rows
		else:
			return None, None, None
	size = len(result[0]) + len(result[1])
	headers = []
	rubbish = []
	last = True
	for i in range(size):
		if last:
			if i in result[1]:
				headers.append(row_indices[i])
			else:
				last = False
		else:
			if i in result[1]:
				rubbish.append(row_indices[i])
	headers_dict = dict()
	transpose = [list(i) for i in zip(*table)]
	for i in headers:
		headers_dict[i] = ' '.join(transpose[i])
	return headers_dict, rubbish, empty_rows


def _show_histogram(data):
	plt.hist(data, bins=100)
	fig = plt.gcf()
	plt.show()

def main(argc, argv):
	DB_OUTPUT = 'output.db'
	db_output = DatabaseOutput(DB_OUTPUT)
	
	targets = [0, float('inf')]
	if argv[1].isdigit():
		targets = [int(argv[1]), int(argv[1])]
	if re.match('^[0-9]+-[0-9]+$', argv[1]):
		targets = list(map(lambda x: int(x), argv[1].split('-')))

	reader = TableReader(argv[2])
	table = reader.get_next_table()
	while(table):
		line_count = reader.get_line_count()
		if (line_count >= targets[0]) and (line_count <= targets[1]):
			headers, rubbish = detect_headers(table['relation'])
			if headers == None:
				headers = dict()
			if rubbish == None:
				rubbish = []
			db_output.add_result(dict(), line_count, table['url'], dict(), headers, rubbish, 1, table['relation'])
		if line_count > targets[1]:
			break
		table = reader.get_next_table()
	return

if __name__ == "__main__":
	main(len(sys.argv), sys.argv)

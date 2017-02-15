#!/usr/bin/python3

import quality_assessment
import header_detection
import content_class

from reader import *
import sys

def process(table, url):
	# possible geo columns
	result = {'columns': [], 'column_indices':[]}

	# TODO determine table direction
	quality = quality_assessment.weight_quality(table, url)
	if not quality:
		return None, None, None

	# determine header, rubbish rows
	headers, rubbish_rows, empty_rows = header_detection.detect_headers(table)
	if (headers == None) or (len(rubbish_rows) > 1):
		return None, None, None # struture to unclear -> bad quality
	rubbish = set(rubbish_rows).union(set(empty_rows))

	# remove rubbish rows and headers
	result = cleanup_table(table, rubbish, set(), headers)

	return result, headers, rubbish

def cleanup_table(table, rubbish_rows, rubbish_cols, headers):
	result = {'columns': [], 'column_indices': []}

	for i, col in enumerate(table):
		newcol =  ([],[])
		count = 0
		for j, cell in enumerate(col):
			if (not (j in rubbish_rows)) and (not (j in headers)):
				if content_class.pre_classify(cell) == content_class.PreClass.GEO:
					newcol[0].append(cell)
					newcol[1].append(j)
		if len(set(newcol[0])) > 1:
			result['columns'].append(newcol)
			result['column_indices'].append(i)
	return result

def main(argc, argv):
	reader = TableReader(argv[1])
	table = reader.get_next_table()
	while (table):
		line_count = reader.get_line_count()
		if line_count == int(argv[2]):
			print('get here')
			# table['relation']
			process(table['relation'], table['url'])
			break
		table = reader.get_next_table()

if __name__ == "__main__":
	main(len(sys.argv), sys.argv)

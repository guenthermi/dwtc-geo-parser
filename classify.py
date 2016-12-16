#!/usr/bin/python3

from reader import *
from gazetteer import *
from coverageScores import *
from databaseOutput import *
import preprocessor as pre

import geopy
import ujson as json
import gzip
import sys
import re

HELP_TEXT = '\033[1mclassify.py\033[0m selector destination [dump]...'

LOG_LEVEL = 1

# MAX_LINE_COUNT = float('inf')
MAX_LINE_COUNT = 100

GEO_NAMES_LOCATION = 'allCountries.txt.gz'

GAZETTEER_INDEX_LOCATION = 'index.db'

COVERAGE_TREE_LOCATION = 'coverageTree.json'

DB_OUTPUT = 'output.db'


def post(table):
	return;

def gazetteer_test(columns, gazetteer):
	result = dict()
	MIN_NUM_FOUND_FACTOR = 0.7
	MIN_FEATURE_CLASS_FACTOR = 0.99

	tree = CoverageTree(COVERAGE_TREE_LOCATION)

	for i, col in enumerate(columns['columns']):
		res, cov = gazetteer.lookupColumn(col[0])

		nodes = [({}, tree.getOrigin(), len(set(col[0])))] # tuple of precondition, node, maxNumber
		while len(nodes) > 0:
			node = nodes[-1]
			nodes = nodes[:-1]
			maxNumber = node[2]
			maxFeatureCount = 0
			maxFeature = ''
			countsResponse, valueType = res.countFeatureValues(node[0], node[1]['feature'], node[1]['featureValues'], node[1]['featureValuesType'])
			if valueType == 'single':
				maxFeatureCount = countsResponse
			if valueType == 'complex':
				if countsResponse:
					maxFeature = max(countsResponse, key=countsResponse.get)
					maxFeatureCount = countsResponse[maxFeature]
			if (maxFeatureCount / maxNumber) >= node[1]['lower_bound']:
				if (len(node[1]['successors']) == 0):
					index = columns['column_indices'][i]
					if index in result:
						result[index].append(node[1]['name'])
					else:
						result[index] = [node[1]['name']]
				for newNode in node[1]['successors']:
					precondition = node[0]
					if node[1]['feature']:
						precondition[node[1]['feature']] = maxFeature
					nodes.append((precondition, newNode, maxFeatureCount))

	return result

def processTable(table, lookup, line_count, out=False):
	res, headers = pre.process(table['relation'])
	if len(res['columns']) > 0:
		res = gazetteer_test(res, lookup)
		return res, headers
	return dict(), headers

def print_table(table, full=False):
	for i, col in enumerate(table[0]):
		if full:
			print('column ', table[1][i], ' :', col[0], ' pos: ', col[1])
		else:
			print(col[0])

def createOutputFile(filename):
	f = gzip.open(filename, 'wb')
	f.write(bytes('{\n', encoding='utf-8'))
	return f 

def endOutputFile(file):
	file.write(bytes('}\n', encoding='utf-8'))
	file.close()
	return

def writeToOutput(file, result, id, url, headers):
	frame_beg = '"' + str(id) + '":{'
	frame_end = '},\n'
	table_str = '"geo_columns":' + json.dumps(result) + ',"url":"' + url + ',"headers":' + str(headers)
	# file.write(bytes(frame_beg, encoding='utf-8'))
	# file.write(bytes(table_str, encoding='utf-8'))
	# file.write(bytes(frame_end, encoding='utf-8'))
	file.write(frame_beg)
	file.write(table_str)
	file.write(frame_end)
	return


def main(argc, argv):
	if (argc < 3):
		print(HELP_TEXT)
	else:

		# determine target lines
		targets = [0, float('inf')]
		if argv[1].isdigit():
			targets = [int(argv[1]), int(argv[1])]
		if re.match('^[0-9]+-[0-9]+$', argv[1]):
			targets = list(map(lambda x: int(x), argv[1].split('-')))
		g = Gazetteer(GAZETTEER_INDEX_LOCATION)
		dbOutput = DatabaseOutput(DB_OUTPUT)
		for arg in argv[2:]:
			reader = TableReader(arg)
			table = reader.getNextTable()
			while (table):
				line_count = reader.getLineCount()
				if (line_count >= targets[0]) and (line_count <= targets[1]):
					print('Process Table', line_count, '...')
					res, headers = processTable(table, g, reader.getLineCount())
					# dbOutput.addResult(res, line_count, table['url'], headers, table['relation'])
					# writeToOutput(sys.stdout, res, reader.getLineCount(), table['url'], headers)

				table = reader.getNextTable()

if __name__ == "__main__":
	main(len(sys.argv), sys.argv)

#!/usr/bin/python3

from reader import *
from gazetteer import *
from coverageScores import *
import preprocessor as pre

import geopy
import ujson as json
import gzip
import sys
import re

HELP_TEXT = 'TODO create a useful help text'

LOG_LEVEL = 1

# MAX_LINE_COUNT = float('inf')
MAX_LINE_COUNT = 100

GEO_NAMES_LOCATION = 'allCountries.txt.gz'

GAZETTEER_INDEX_LOCATION = 'index.db'

COVERAGE_TREE_LOCATION = 'coverageTree.json'


def post(table):
	return;

def gazetteer_test(columns, gazetteer):
	result = []
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
			if node[1]['feature'] != "":
				counts = res.countFeatureValues(node[0], node[1]['feature']) # at the moment support only for a single feature
				if node[1]['featureValuesType'] == 'all':
					maxFeature = max(counts, key=counts.get)
					maxFeatureCount = counts[maxFeature]
				if node[1]['featureValuesType'] == 'array': 
					for key in counts:
						if key in node[1]['featureValues']:
							if counts[key] > maxFeatureCount:
								maxFeatureCount = counts[key]
								maxFeature = key
				if node[1]['featureValuesType'] == 'minimum':

					print(counts)
			else:
				maxFeatureCount = cov
			if (maxFeatureCount / maxNumber) >= node[1]['lower_bound']:
				if (len(node[1]['successors']) == 0):
					result.append(columns['column_indices'][i])
					break
				for newNode in node[1]['successors']:
					precondition = node[0]
					if node[1]['feature']:
						precondition[node[1]['feature']] = maxFeature
					nodes.append((precondition, newNode, maxFeatureCount))

		# numFound = res['numFound']
		# numColumn = res['numColumn']

		# minNumFoundRate = MIN_NUM_FOUND_FACTOR - (0.5 / numColumn)
		# minFeatureClassRate = MIN_FEATURE_CLASS_FACTOR #- (0.5 / numColumn)

		# numFoundRate = numFound / numColumn
		# if numFoundRate > minNumFoundRate:
		# 	featureClasses = res['counts']['featureClasses']
		# 	max_feature = max(featureClasses.keys(),key=lambda x: featureClasses[x])
		# 	featureClassRate = featureClasses[max_feature] / numFound
		# 	if (featureClassRate > minFeatureClassRate):
		# 		result.append(columns['column_indices'][i])

	return result

def processTable(table, lookup, line_count, out=False):
	res = pre.process(table['relation'])
	if len(res['columns']) > 0:
		res = gazetteer_test(res, lookup)
		print(res)

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

def writeToOutput(file, result, id, url):
	frame_beg = '"' + str(id) + '":{'
	frame_end = '},\n'
	table_str = '"geo_columns":' + str(result[1]).replace(' ', '') + ',"url":"' + url
	file.write(bytes(frame_beg, encoding='utf-8'))
	file.write(bytes(table_str, encoding='utf-8'))
	file.write(bytes(frame_end, encoding='utf-8'))
	return;

def endOutputFile(file):
	file.write(bytes('}\n', encoding='utf-8'))
	file.close()
	return;


def main(argc, argv):
	if (argc < 3):
		print(HELP_TEXT)
	else:
		g = Gazetteer(GAZETTEER_INDEX_LOCATION)
		for arg in argv[2:]:
			reader = TableReader(arg)
			table = reader.getNextTable()
			while (table):
				if reader.getLineCount() == int(argv[1]):
					print(table['url'])
					# print(table['relation'][1])
					processTable(table, g, reader.getLineCount())
				table = reader.getNextTable()

if __name__ == "__main__":
	main(len(sys.argv), sys.argv)

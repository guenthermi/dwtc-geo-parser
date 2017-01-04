#!/usr/bin/python3

from coverageScores import *

import gzip
import json
import sys

HELP_TEXT = '\033[1mcategoryCount\033[0m geo_names output'

COVERAGE_TREE_LOCATION = 'coverageTree.json'

GEO_NAMES_LOCATION = 'allCountries.txt.gz'

MAX_LINE_COUNT = float('inf')

def get_categories(coverage_tree):
	result = dict()
	origin = coverage_tree.get_origin()
	nodes = [origin]
	while nodes:
		node = nodes.pop(-1) # get last element
		if node['successors']:
			for new_node in node['successors']:
				# TODO add condition to new node
				new_node['conditions'] = []
				if 'conditions' in node:
					for condition in node['conditions']:
						new_node['conditions'].append(condition)
				new_node['conditions'].append((node['feature'], node['featureValues'], node['featureValuesType']))
				nodes.append(new_node)
		else:
			key = node['name']
			value = []
			if 'conditions' in node:
				value = node['conditions']
			value.append((node['feature'], node['featureValues'], node['featureValuesType']))
			result[key] = value
	return result

def check_conditions(conditions, entity):
	valid = True
	for condition in conditions:
		if condition[2] == 'specific':
			if not (entity[condition[0]] in condition[1]):
				valid = False
				break
		if condition[2] == 'minimum':
			if not (int(entity[condition[0]]) >= int(condition[1])):
				valid = False
				break
	return valid

def get_count_key(conditions, entity):
	# determine all conditions -> create tuple
	features = []
	for condition in conditions:
		if condition[2] == 'all':
			features.append(entity[condition[0]])
	return str(tuple(features))

def increment_counts(categories, counts, entity):
	for category in categories:
		conditions = categories[category]
		if check_conditions(conditions, entity):
			key = get_count_key(conditions, entity)
			if key in counts[category]:
				counts[category][key] = counts[category][key] + 1
			else:
				counts[category][key] = 1
	return


def parse_entity(line):
	splits = line.split(b'\t')
	entity = dict()
	entity['featureClass'] = splits[6].decode('utf-8')
	entity['featureCode'] = splits[7].decode('utf-8')
	entity['countryCode'] = splits[8].decode('utf-8')
	entity['population'] = splits[14].decode('utf-8')
	entity['timezone'] = splits[17].decode('utf-8')
	return entity

def process_geo_names(filename, categories):
	line_count = 0
	# init counts
	counts = dict()
	for category in categories:
		counts[category] = dict()
	file = gzip.open(filename, 'r')
	for line in file:
		entity = parse_entity(line)
		increment_counts(categories, counts, entity)
		line_count +=1
		if line_count % 100000 == 0:
			print(line_count)
		if line_count > MAX_LINE_COUNT:
			print(counts)
			return counts
	return counts

def print_counts(output_location, categories):
	file = open(output_location, 'w')
	file.write(json.dumps(categories))
	# TODO print counts
	return

def main(argc, argv):
	if (argc != 2):
		print(HELP_TEXT)
	output_location = argv[1]
	coverage_tree = CoverageTree(COVERAGE_TREE_LOCATION)
	counts = get_categories(coverage_tree)
	counts = process_geo_names(GEO_NAMES_LOCATION, counts)
	print_counts(output_location, counts)

if __name__ == "__main__":
	main(len(sys.argv), sys.argv)

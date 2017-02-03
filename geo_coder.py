#!/usr/bin/python3

from gazetteer import *

import sys
import math

INDICES = GazetteerResult.FEATURE_INDICES

def _get_only_best_interpreations(interpretations):
	best = dict()
	for key in interpretations:
		value = interpretations[key]
		for entry in value:
			if entry[3]:
				best[key] = entry
	return best

def _filter_by_best(best_interpretations, data, lookup):
	filtered = dict()
	for index in data:
		best = best_interpretations[index]
		feature = best[1]
		column = data[index]
		filtered[index] = dict()
		for entry in column:
			term = entry
			geo_entities = column[entry]
			for entity in geo_entities:
				is_valid = True
				for node in lookup[best[0]]:
					if node['featureValuesType'] == 'empty':
						continue
					elif node['featureValuesType'] == 'specific':
						if entity[INDICES[node['feature']]] in node['featureValues']:
							continue
						else:
							is_valid = False
							break
					elif node['featureValuesType'] == 'all':
						if entity[INDICES[node['feature']]] == best[1]:
							continue
						else:
							is_valid = False
							break
					elif node['featureValuesType'] == 'minimum':
						if entity[INDICES[node['feature']]] > node['featureValues']:
							continue
						else:
							is_valid = False
							break
					else:
						print('Error: Unknown featureValuesType: ', node.featureValuesType)
						is_valid = False
				if is_valid:
					if term in filtered[index]:
						filtered[index][term].add(entity)
					else:
						filtered[index][term] = set({entity})
	return filtered


def _filter_by_feature_code(data):
	for index in data:
		# determine feature code counts
		codes = dict()
		for term in data[index]:
			subject = data[index][term]
			subject_codes = set()
			for entry in subject:
				subject_codes.add(entry[INDICES['featureCode']])
			for code in subject_codes:
				if code in codes:
					codes[code] += 1
				else:
					codes[code] = 1
		# determine max feature code
		max_feature_code = None
		for code in codes:
			if not max_feature_code:
				max_feature_code = code
			if codes[code] > codes[max_feature_code]:
				max_feature_code = code
		# filter entrys that do not have the max feature code
		for term in data[index]:
			subject = data[index][term]
			if len(subject) > 1:
				new_subject = set()
				for entry in subject:
					if entry[INDICES['featureCode']] == max_feature_code:
						new_subject.add(entry)
				if len(new_subject) > 0:
					data[index][term] = new_subject
	return data

def _init_probabilities(data):
	probs = dict()
	for term in data:
		entities = data[term]
		for i, entity in enumerate(entities):
			probs[(term,i)] = 1 / len(entities)
	return probs

def project_3d(cooridinates):
	lat, long = cooridinates
	x = math.sin(long *(math.pi / 180) )
	y = math.cos(long *(math.pi / 180) )
	z = math.sin(lat *(math.pi / 180) )
	return (x,y,z)

def _calculate_centroid(data, probs):
	center = [0,0,0]
	for term in data:
		entities = data[term]
		x, y, z = 0.0, 0.0, 0.0
		for i, entity in enumerate(entities):
			location = (entity[4], entity[5])
			projection = project_3d(location)
			x += probs[(term,i)] * projection[0]
			y += probs[(term,i)] * projection[1]
			z += probs[(term,i)] * projection[2]
		center[0] += (float(x) / len(data))
		center[1] += (float(y) / len(data))
		center[2] += (float(z) / len(data))
	return (center[0], center[1], center[2])

def _distance(value1, value2):
	if len(value1) != len(value2):
		return None
	dist = 0
	for i in range(len(value1)):
		dist += (value1[i] - value2[i])**2
	return dist

def _update_probabilities(data, center, probs):
	# calculate distances
	for term in data:
		entities = data[term]
		summation = 0
		for entity in entities:
			location = (entity[4], entity[5])
			summation += 1.0 / (_distance(center, project_3d(location)))
		for i, entity in enumerate(entities):
			location = (entity[4], entity[5])
			probs[(term,i)] = 1.0 / ((_distance(center, project_3d(location))) * summation)

def _learn_assignment(data):
	INTERATIONS = 20
	# init
	probs = _init_probabilities(data)

	for i in range(INTERATIONS):
		# calculate center
		center = _calculate_centroid(data, probs)
		# update probs
		_update_probabilities(data, center, probs)

	return probs

def _choose_entities(data):
	result = dict()
	for index in data:
		column = data[index]

		# transform column
		for term in column:
			column[term] = list(column[term])
		
		# calculate probabilities
		probs = _learn_assignment(column)

		# choose best entity for every term
		choice = dict()
		for term in column:
			max_prob = 0
			max_elem = None
			for i, elem in enumerate(column[term]):
				if probs[(term,i)] > max_prob:
					max_prob = probs[(term,i)]
					max_elem = column[term][i]
			choice[term] = (max_elem[4], max_elem[5])
		
		result[index] = choice
	return result

def get_coordinates(interpretations, data, coverage_tree):
	# get best
	best = _get_only_best_interpreations(interpretations)
	# filter entities by the semantic of the interpretation
	filtered = dict()
	filtered = _filter_by_best(best, data, coverage_tree.get_lookup())
	filtered = _filter_by_feature_code(filtered)
	# choose entities if there are still multiple possibilities
	choice = _choose_entities(filtered)
	# choose entities if there are still multiple possibilities
	# choise = _learn_assignment(filtered)

	return choice

def main(argc, argv):
	print('Hello World')

if __name__ == "__main__":
	main(len(sys.argv), sys.argv)


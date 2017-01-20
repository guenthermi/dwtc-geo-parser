#!/usr/bin/python3

import sqlite3
import redis
import sys

# TODO implement function to determine if single entities in a column do not fit in

class GazetteerResult:

	# mapping of feature names to tuple positions 
	FEATURE_INDICES = {
		'featureClass': 0, 
		'featureCode': 1, 
		'countryCode': 2, 
		'timezone': 3,
		'population': 4
	}
	
	def __init__(self):
		self.result = dict()
	
	def add_result(self, name, featureClass, featureCode, countryCode, timezone, population):
		if name in self.result:
			self.result[name].add((featureClass, featureCode, countryCode, timezone, population))
		else:
			self.result[name] = set({(featureClass, featureCode, countryCode, timezone, population)})

	def get_result(self):
		return self.result

	def count_feature_values(self, precondition, feature, featureValues, type):
		if type == 'empty':
			return len(self.result), 'single'
		if type == 'all':
			return self._count_feature_values_all(precondition, feature), 'complex'
		if type == 'specific':
			return self._count_feature_values_specific(precondition, feature, featureValues), 'complex'
		if type == 'minimum':
			return self._count_feature_values_minimum(precondition, feature, featureValues), 'single'

	def _count_feature_values_all(self, precondition, feature):
		counts = dict();
		for name in self.result:
			posibilities = self._has_features(name, precondition)
			value_set = set()
			for entry in posibilities:
				value_set.add(entry[GazetteerResult.FEATURE_INDICES[feature]])
			for value in value_set:	
				if value in counts:
					counts[value] += 1
				else:
					counts[value] = 1
		return counts

	def _count_feature_values_specific(self, precondition, feature, legalValues):
		counts = dict();
		for name in self.result:
			posibilities = self._has_features(name, precondition)
			value_set = set()
			for entry in posibilities:
				if entry[GazetteerResult.FEATURE_INDICES[feature]] in legalValues:
					value_set.add(entry[GazetteerResult.FEATURE_INDICES[feature]])
			for value in value_set:	
				if value in counts:
					counts[value] += 1
				else:
					counts[value] = 1
		return counts		

	def _count_feature_values_minimum(self, precondition, feature, minimum):
		count = 0
		for name in self.result:
			posibilities = self._has_features(name, precondition)
			valid_exists = False
			for entry in posibilities:
				if entry[GazetteerResult.FEATURE_INDICES[feature]] > minimum:
					valid_exists = True
			if valid_exists:
				count += 1
		return count

	def _has_features(self, name, features):
		""" Returns possible geo entities for a given name that have all given features"""
		posibilities = set()
		feature_set = self.result[name]
		for feature_tuple in feature_set:
			valid = True
			for feature_name in features:
				if features[feature_name] != feature_tuple[GazetteerResult.FEATURE_INDICES[feature_name]]:
					valid = False
			if valid:
				posibilities.add(feature_tuple)
		return posibilities



class Gazetteer:
	def __init__(self, db):
		self.con = sqlite3.connect(db)
		self.cur = self.con.cursor()
		self.r = redis.StrictRedis()

	def lookup_name(self, name, g_result):
		self.cur.execute("SELECT GeoEntities.GeonameId, GeoEntities.name, GeoEntities.FeatureClass, GeoEntities.FeatureCode, GeoEntities.CountryCode, GeoEntities.Timezone, GeoEntities.Population FROM Aliases INNER JOIN GeoEntities ON Aliases.GeonameId=GeoEntities.GeonameId WHERE AlternateName = '" + name.replace('’','’’').replace("'","''") + "'") # inner join with GeoEntities
		rows = self.cur.fetchall()

		# check if response is empty
		if rows == []:
			return g_result
		
		# add to result
		for row in rows:
			g_result.add_result(name, row[2], row[3], row[4], row[5], row[6])

		return

	def lookup_name_redis(self, name, g_result):
		ids = self.r.get(name)
		if ids:
			ids = ids.split(b',')
			for id in ids:
				row = self.r.get(id).split(b'\t')
				if row[3]:
					row[3] = int(row[3])
				else:
					row[3] = 0
				g_result.add_result(name, row[0].decode('utf-8'), row[1].decode('utf-8'), row[2].decode('utf-8'), row[4].decode('utf-8'), row[3])
		return

	def lookup_column(self, column):
		""" Returns the GazetteerResult for a column of names and the general geo entities coverage """
		result = GazetteerResult()
		for entry in column:
			self.lookup_name(entry, result)
		return result, len(result.get_result())

	def lookup_column_fast(self, column):
		g_result = GazetteerResult()
		ids = dict()
		pipe = self.r.pipeline()
		for entry in column:
			pipe.get(entry)
		response = pipe.execute()
		for i, entry in enumerate(column):
			ids[entry] = response[i]
		for name in ids:
			id_set = ids[name]
			if id_set:
				id_set = id_set.split(b',')
				for id in id_set:
					row = self.r.get(id).split(b'\t')
					if row[3]:
						row[3] = int(row[3])
					else:
						row[3] = 0
					g_result.add_result(name, row[0].decode('utf-8'), row[1].decode('utf-8'), row[2].decode('utf-8'), row[4].decode('utf-8'), row[3])
		return g_result, len(g_result.get_result())


def main(argc, argv):
	g = Gazetteer('index.db')
	res, cov = g.lookup_column_fast(['Luga', 'Paris', 'Berlin', 'Dresden', 'Bautzen', 'Leipzig'])
	print('Coverage: ', cov)
	print('Result:', res.get_result())
	print(res.count_feature_values({}, 'featureClass'));
	print(res.count_feature_values({'featureClass': 'R'}, 'countryCode'));

if __name__ == "__main__":
	main(len(sys.argv), sys.argv)


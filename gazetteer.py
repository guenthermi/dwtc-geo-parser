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
	
	def addResult(self, name, featureClass, featureCode, countryCode, timezone, population):
		if name in self.result:
			self.result[name].add((featureClass, featureCode, countryCode, timezone, population))
		else:
			self.result[name] = set({(featureClass, featureCode, countryCode, timezone, population)})

	def getResult(self):
		return self.result

	def countFeatureValues(self, precondition, feature, featureValues, type):
		if type == 'empty':
			return len(self.result), 'single'
		if type == 'all':
			return self._countFeatureValuesAll(precondition, feature), 'complex'
		if type == 'specific':
			return self._countFeatureValuesSpecific(precondition, feature, featureValues), 'complex'
		if type == 'minimum':
			return self._countFeatureValuesMinimum(precondition, feature, featureValues), 'single'

	def _countFeatureValuesAll(self, precondition, feature):
		counts = dict();
		for name in self.result:
			posibilities = self._hasFeatures(name, precondition)
			valueSet = set()
			for entry in posibilities:
				valueSet.add(entry[GazetteerResult.FEATURE_INDICES[feature]])
			for value in valueSet:	
				if value in counts:
					counts[value] += 1
				else:
					counts[value] = 1
		return counts

	def _countFeatureValuesSpecific(self, precondition, feature, legalValues):
		counts = dict();
		for name in self.result:
			posibilities = self._hasFeatures(name, precondition)
			valueSet = set()
			for entry in posibilities:
				if entry[GazetteerResult.FEATURE_INDICES[feature]] in legalValues:
					valueSet.add(entry[GazetteerResult.FEATURE_INDICES[feature]])
			for value in valueSet:	
				if value in counts:
					counts[value] += 1
				else:
					counts[value] = 1
		return counts		

	def _countFeatureValuesMinimum(self, precondition, feature, minimum):
		count = 0
		for name in self.result:
			posibilities = self._hasFeatures(name, precondition)
			validExists = False
			for entry in posibilities:
				if entry[GazetteerResult.FEATURE_INDICES[feature]] > minimum:
					validExists = True
			if validExists:
				count += 1
		return count

	def _hasFeatures(self, name, features):
		""" Returns possible geo entities for a given name that have all given features"""
		posibilities = set()
		featureSet = self.result[name]
		for featureTuple in featureSet:
			valid = True
			for featureName in features:
				if features[featureName] != featureTuple[GazetteerResult.FEATURE_INDICES[featureName]]:
					valid = False
			if valid:
				posibilities.add(featureTuple)
		return posibilities



class Gazetteer:
	def __init__(self, db):
		self.con = sqlite3.connect(db)
		self.cur = self.con.cursor()
		self.r = redis.StrictRedis()

	def lookupName(self, name, gResult):
		self.cur.execute("SELECT GeoEntities.GeonameId, GeoEntities.name, GeoEntities.FeatureClass, GeoEntities.FeatureCode, GeoEntities.CountryCode, GeoEntities.Timezone, GeoEntities.Population FROM Aliases INNER JOIN GeoEntities ON Aliases.GeonameId=GeoEntities.GeonameId WHERE AlternateName = '" + name.replace('’','’’').replace("'","''") + "'") # inner join with GeoEntities
		rows = self.cur.fetchall()

		# check if response is empty
		if rows == []:
			return gResult
		
		# add to result
		for row in rows:
			gResult.addResult(name, row[2], row[3], row[4], row[5], row[6])

		return

	def lookupNameRedis(self, name, gResult):
		ids = self.r.get(name)
		if ids:
			ids = ids.split(b',')
			for id in ids:
				row = self.r.get(id).split(b'\t')
				if row[3]:
					row[3] = int(row[3])
				else:
					row[3] = 0
				gResult.addResult(name, row[0].decode('utf-8'), row[1].decode('utf-8'), row[2].decode('utf-8'), row[4].decode('utf-8'), row[3])
		return


	def lookupColumn(self, column):
		""" Returns the GazetteerResult for a column of names and the general geo entities coverage """
		result = GazetteerResult()
		for entry in column:
			self.lookupName(entry, result)
		return result, len(result.getResult())

	def lookupColumnFast(self, column):
		gResult = GazetteerResult()
		ids = dict()
		pipe = self.r.pipeline()
		for entry in column:
			pipe.get(entry)
		response = pipe.execute()
		for i, entry in enumerate(column):
			ids[entry] = response[i]
		for name in ids:
			idSet = ids[name]
			if idSet:
				idSet = idSet.split(b',')
				for id in idSet:
					row = self.r.get(id).split(b'\t')
					if row[3]:
						row[3] = int(row[3])
					else:
						row[3] = 0
					gResult.addResult(name, row[0].decode('utf-8'), row[1].decode('utf-8'), row[2].decode('utf-8'), row[4].decode('utf-8'), row[3])
		return gResult, len(gResult.getResult())


def main(argc, argv):
	g = Gazetteer('index.db')
	res, cov = g.lookupColumnFast(['Luga', 'Paris', 'Berlin', 'Dresden', 'Bautzen', 'Leipzig'])
	print('Coverage: ', cov)
	print('Result:', res.getResult())
	print(res.countFeatureValues({}, 'featureClass'));
	print(res.countFeatureValues({'featureClass': 'R'}, 'countryCode'));

if __name__ == "__main__":
	main(len(sys.argv), sys.argv)


#!/usr/bin/python3
#!/usr/bin/python3

import sqlite3
import sys

# TODO implement function to determine if single entities in a column do not fit in

class Gazetteer:
	def __init__(self, db):
		self.con = sqlite3.connect(db)
		self.cur = self.con.cursor()

	def lookupName(self, name):
		self.cur.execute("SELECT GeoEntities.GeonameId, GeoEntities.name, GeoEntities.FeatureClass, GeoEntities.FeatureCode, GeoEntities.CountryCode, GeoEntities.Timezone FROM Aliases INNER JOIN GeoEntities ON Aliases.GeonameId=GeoEntities.GeonameId WHERE AlternateName = '" + name.replace('’','’’').replace("'","''") + "'") # inner join with GeoEntities
		rows = self.cur.fetchall()

		featureClasses = set()
		featureCodes = set()
		countryCodes = set()
		timezones = set()
		entrySet = set()

		# check if response is empty
		if rows == []:
			return {}
		
		# create result
		for row in rows:
			if row[2]:
				featureClasses.add(row[2])
			if row[3]:
				featureCodes.add(row[3])
			if row[4]:
				countryCodes.add(row[4])
			if row[5]:
				timezones.add(row[5])
			entrySet.add((row[2], row[3], row[4], row[5]))

		return {'featureClasses': featureClasses, 'featureCodes': featureCodes, 'countryCodes': countryCodes, 'timezones': timezones, 'entrySet': entrySet}

	def lookupColumn(self, column):
		# return pair of counts array and result array (including also counts)
		featureClasses = dict()
		featureCodes = dict()
		countryCodes = dict()
		timezones = dict()
		entrySet = dict()
		counts = {'featureClasses': featureClasses, 'featureCodes': featureCodes, 'countryCodes': countryCodes, 'timezones': timezones, 'entrySet': entrySet}
		result = {'counts': counts, 'numFound': 0, 'numColumn': len(column)}
		for entry in column: # column should be a set not a list
			entryData = self.lookupName(entry)
			if len(entryData) > 0:
				result['numFound'] += 1
				for feature in entryData:
					for key in entryData[feature]:
						self._increaseFeatureCounts(key, counts[feature])
		return result

	def _increaseFeatureCounts(self, key, counts):
		if key:
			if key in counts:
				counts[key] += 1
			else:
				counts[key] = 1

def main(argc, argv):
	g = Gazetteer('index.db')
	res = g.lookupColumn(['Luga', 'Paris', 'Berlin', 'Dresden', 'Bautzen', 'Leipzig'])
	print(res['counts']['featureClasses'])
	print('')
	print(res['numFound'])
	print('')
	print(res['numColumn'])

if __name__ == "__main__":
	main(len(sys.argv), sys.argv)


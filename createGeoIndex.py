#!/usr/bin/python3

import sqlite3
import gzip
import sys
import os

HELP_TEXT = '\033[1mcreateGeoIndex\033[0m source destination'

MAX_COMMIT_SIZE = 1000000

# Contens of Geonames (copied from http://http://download.geonames.org/export/dump/)
#
# geonameid         : integer id of record in geonames database
# name              : name of geographical point (utf8) varchar(200)
# asciiname         : name of geographical point in plain ascii characters, varchar(200)
# alternatenames    : alternatenames, comma separated, ascii names automatically transliterated, convenience attribute from alternatename table, varchar(10000)
# latitude          : latitude in decimal degrees (wgs84)
# longitude         : longitude in decimal degrees (wgs84)
# feature class     : see http://www.geonames.org/export/codes.html, char(1)
# feature code      : see http://www.geonames.org/export/codes.html, varchar(10)
# country code      : ISO-3166 2-letter country code, 2 characters
# cc2               : alternate country codes, comma separated, ISO-3166 2-letter country code, 200 characters
# admin1 code       : fipscode (subject to change to iso code), see exceptions below, see file admin1Codes.txt for display names of this code; varchar(20)
# admin2 code       : code for the second administrative division, a county in the US, see file admin2Codes.txt; varchar(80) 
# admin3 code       : code for third level administrative division, varchar(20)
# admin4 code       : code for fourth level administrative division, varchar(20)
# population        : bigint (8 byte int) 
# elevation         : in meters, integer
# dem               : digital elevation model, srtm3 or gtopo30, average elevation of 3''x3'' (ca 90mx90m) or 30''x30'' (ca 900mx900m) area in meters, integer. srtm processed by cgiar/ciat.
# timezone          : the iana timezone id (see file timeZone.txt) varchar(40)
# modification date : date of last modification in yyyy-MM-dd format

# TODO include index creation
#	CREATE INDEX index_name ON table_name (column_name);

def constractInsertQuery(tableName, values):
	result = 'INSERT INTO ' + tableName + ' VALUES ('
	for index in range(len(values) - 1):
		result += values[index] + ', '
	result += values[-1] + ')'
	return result

def writeIndex(src, cur, con):
	count = 0

	for line in src:
		count += 1
		line = line.split(b'\t')
		geonameId = line[0].decode('utf-8').replace('’','’’').replace("'","''")
		name = "'" + line[1].decode('utf-8').replace('’','’’').replace("'","''") + "'"
		alternateNames = "'" + line[3].decode('utf-8').replace('’','’’').replace("'","''") + "'"
		latitude = line[4].decode('utf-8').replace('’','’’').replace("'","''") if line[4] else '-1.0'
		longitude = line[5].decode('utf-8').replace('’','’’').replace("'","''") if line[5] else '-1.0'
		featureClass = "'" + line[6].decode('utf-8').replace('’','’’').replace("'","''") + "'"
		featureCode = "'" + line[7].decode('utf-8').replace('’','’’').replace("'","''") + "'"
		countryCode = "'" + line[8].decode('utf-8').replace('’','’’').replace("'","''") + "'"
		population = line[14].decode('utf-8').replace('’','’’').replace("'","''") if line[14].isdigit() else '-1'
		elevation = line[15].decode('utf-8').replace('’','’’').replace("'","''") if line[15].isdigit() else '-1'
		timezone = "'" + line[17].decode('utf-8').replace('’','’’').replace("'","''") + "'"

		query =  constractInsertQuery('GeoEntities', [geonameId, name, alternateNames, latitude, longitude, featureClass, featureCode, countryCode, population, elevation, timezone])
		cur.execute(query)
		aliases = set(line[3].split(b','))
		aliases.add(line[1])
		for alias in aliases:
			if (alias):
				aliasQuery = 'INSERT INTO Aliases VALUES (' + geonameId + ", '" + alias.decode('utf-8').replace('’','’’').replace("'","''") + "')"
				cur.execute(aliasQuery)

		if (count % MAX_COMMIT_SIZE) == 0:
			con.commit()
			print('created ', count, ' rows')
	con.commit()
	print('Finsished creation of ', count, ' rows')
	print('Create indices...')
	cur.execute("CREATE INDEX index_geoEntities ON GeoEntities (GeonameId)")
	cur.execute("CREATE INDEX index_aliases ON Aliases (AlternateName)")
	con.commit()
	print('Finished creation of indices')

def createTables(cur):
	cur.execute("CREATE TABLE GeoEntities(GeonameId INT PRIMARY KEY, Name TEXT, AlternateNames TEXT, Latitude REAL, Longitude REAL, FeatureClass VARCHAR(1), FeatureCode VARCHAR(10), CountryCode VARCHAR(2), Population INT, Elevation INT, Timezone VARCHAR(40))")
	cur.execute("CREATE TABLE Aliases(GeonameId INT, AlternateName TEXT, FOREIGN KEY(GeonameId) REFERENCES GeoEntities(GeonameId))")

def main(argc, argv):
	if (argc != 3):
		print(HELP_TEXT)
		return
	src = gzip.open(argv[1], 'r')
	if os.path.isfile(argv[2]):
		os.remove(argv[2])
	dest = sqlite3.connect(argv[2])
	if dest:
		cur = dest.cursor()
		createTables(cur)
		writeIndex(src, cur, dest)
		dest.close()

if __name__ == "__main__":
	main(len(sys.argv), sys.argv)

#!/usr/bin/python3

import sqlite3
import sys


class WikidataLookup:

	dis_classes = {
		'name': (set({'Q12308941', 'Q11879590', 'Q3409032', 'Q101352', 'Q202444'}), 0.8), 
		'natural_number': (set({'Q21199'}), 0.7),
		'color': (set({'Q1075'}), 0.7),
		'sport_team': (set({'Q17156793'}), 0.7)
	}

	def __init__(self, db):
		self.con = sqlite3.connect(db)
		self.cur = self.con.cursor()

	def lookup_classes(self, column):
		query = "SELECT Term, ClassId FROM Meanings WHERE Term IN (" + '?, '*(len(column)-1) +  "?)"
		self.cur.execute(query, tuple([c.lower() for c in column]))
		query_results = self.cur.fetchall()
		# TODO determine classes
		classes = set([y for (x,y) in query_results])
		result_dict = dict()
		for entry in query_results:
			if entry[0] in result_dict:
				result_dict[entry[0]].append(entry[1])
			else:
				result_dict[entry[0]] = [entry[1]]
		if len(result_dict) < 2:
			return dict()
		# determine coverage for all classes
		covs = dict()
		for c in WikidataLookup.dis_classes:
			counter = 0
			for key in result_dict:
				for entry in WikidataLookup.dis_classes[c][0]:
					if entry in result_dict[key]:
						counter += 1
						break
			if (counter / len(result_dict)) > WikidataLookup.dis_classes[c][1]:
				covs[c] = counter / len(result_dict)
		return covs

def main(argc, argv):
	wl = WikidataLookup('wikidata_extractor/wikidata.db')
	print(wl.lookup_classes(['Michael', 'Martin', 'Anton', 'Mike', 'Paula', 'Alexander', 'Jenny']))

if __name__ == "__main__":
	main(len(sys.argv), sys.argv)



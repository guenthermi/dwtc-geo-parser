#!/usr/bin/python3

import json
import sys

RATE_FILE_LOCATION = 'categoryCounts.json'

class Ratings:
	def __init__(self, filename):
		raw = ''.join(open(filename).readlines())
		self.counts = json.loads(raw)

	def get_count(self, category_name, feature):
		count = self.counts[category_name]
		if '()' in count:
			return count['()']
		else:
			key = "('" + feature + "',)"
			if key in count:
				return count[key]
			else:
				return 0

def main(argc, argv):
	ratings = Ratings(RATE_FILE_LOCATION)
	print(ratings.get_count('local_city', 'US'))

if __name__ == "__main__":
	main(len(sys.argv), sys.argv)

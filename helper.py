#!/usr/bin/python3

from reader import *

import sys

def main(argc, argv):
	reader = TableReader(argv[1])
	table = reader.getNextTable()
	while (table):
		line_count = reader.getLineCount()
		if line_count == int(argv[2]):
			print(table['relation'][int(argv[3])])
		table = reader.getNextTable()

if __name__ == "__main__":
	main(len(sys.argv), sys.argv)
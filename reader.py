#!/usr/bin/python3

import ujson as json
import gzip
import sys


class TableReader:
	def __init__(self, filename):
		self.file = gzip.open(filename, 'r')
		self.line_count = 0
		self.current_table = ''
	def close(self):
		self.file.close()
	def get_next_table(self):
		self.line_count += 1
		self.current_table = self.file.readline()
		if self.current_table:
			return json.loads(self.current_table)
		else:
			return None
	def get_current_table_string(self):
		return self.current_table
	def get_line_count(self):
		return self.line_count


def main(argc, argv):
	if (argc > 1):
		for arg in argv[1:]:
			reader = TableReader(arg)
			table = reader.get_next_table()
			while (table):
				if reader.line_count == 1:
					print(table)
				table = reader.get_next_table()


if __name__ == "__main__":
	main(len(sys.argv), sys.argv)


#!/usr/bin/python3

from reader import *

import sys

def print_column(table, col):
	print(table['relation'][col])

def print_size(table):
	print(len(table['relation']))

def create_evaluation_template(filename, reader):
	file = open(filename, 'w')
	table = reader.get_next_table()
	line_count = reader.get_line_count() 
	file.write('{\n')
	while (table):
		next_table = reader.get_next_table()
		file.write(create_evaluation_entry(table,reader.get_line_count()-1, (next_table == None)))
		table = next_table
	file.write('}\n')
	file.close()

def create_evaluation_entry(table, count, last):
	template = 	'\t"' + str(count) + '": {\n\t\tgeo_columns: [],\n\t\tsize: ' \
		+ str(len(table['relation'])) + ',\n\t\turl: "' + table['url'] + '"\n\t}'
	if not last:
		template += ',\n'
	return template

def info_service(reader, argv):
	table = reader.get_next_table()
	while (table):
		line_count = reader.get_line_count()
		if line_count == int(argv[3]):
			if argv[1] == '--print_col':
				print_column(table, int(argv[4]))
			if argv[1] == '--print_size':
				print_size(table)
		table = reader.get_next_table()

def main(argc, argv):
	reader = TableReader(argv[2])
	if argv[1] == '--create_template':
		create_evaluation_template(argv[3], reader)
	else:
		info_service(reader, argv)
if __name__ == "__main__":
	main(len(sys.argv), sys.argv)

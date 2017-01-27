#!/usr/bin/python3

from reader import *
import sqlite3
import json

import sys

def print_column(table, col):
	print(table['relation'][col])

def print_size(table):
	print(len(table['relation']))

def create_evaluation_template(filename, reader, existing_classification):
	lookup = dict()
	for classif in existing_classification:
		classification_file = open(classif, 'r')
		data = ''.join(classification_file.readlines())
		json_data = json.loads(data)
		for id in json_data:
			lookup[json_data[id]['url']] = json_data[id]
	file = open(filename, 'w')
	table = reader.get_next_table()
	line_count = reader.get_line_count() 
	file.write('{\n')
	while (table):
		next_table = reader.get_next_table()
		file.write(create_evaluation_entry(table,reader.get_line_count()-1, (next_table == None), lookup))
		table = next_table
	file.write('}\n')
	file.close()

def create_evaluation_entry(table, count, last, lookup):
	geo_columns = '[]'
	if table['url'] in lookup:
		geo_columns = str(lookup[table['url']]['geo_columns'])
	template = 	'\t"' + str(count) + '": {\n\t\t"geo_columns": ' + geo_columns + ',\n\t\t"size": ' \
		+ str(len(table['relation'])) + ',\n\t\t"url": "' + table['url'] + '"\n\t}'
	if not last:
		template += ',\n'
	return template

def calculate_statistics(argv):
	# counters
	true_positives = 0
	true_negatives = 0
	false_positives = 0
	false_negatives = 0
	
	# load human classified data
	file = open(argv[2], 'r')
	human_class = json.loads(''.join(file.readlines()))

	# load output of computed classification
	con = sqlite3.connect(argv[3])
	cur = con.cursor()
	lookup = get_table_geo_column_lookup(cur)

	# compare human classification with computed classification
	for id in lookup:
		tp, tn, fp, fn = 0, 0, 0, 0
		computed = [y for (x,y) in lookup[id]]
		human = human_class[str(id)]
		for col in computed:
			if col in human['geo_columns']:
				tp += 1
			else:
				fp += 1
		for col in human['geo_columns']:
			if not (col in computed):
				fn += 1
		tn = human['size'] - (tp + fp + fn)
		true_positives += tp
		true_negatives += tn
		false_positives += fp
		false_negatives += fn
	precision = true_positives / (true_positives + false_positives)
	recall = true_positives / (true_positives + false_negatives)
	print('TP:', true_positives, 'TN:', true_negatives, 'FP:', false_positives, 'FN:', false_negatives)
	print('Precision:', precision)
	print('Recall:', recall)
	print('F1-Measure:', 2 * ((precision * recall) / (precision + recall)))
	return
	
def get_table_geo_column_lookup(cur):
	lookup = dict()

	query_get_tables = 'SELECT Results.ResultId FROM Results'
	query_get_geo_columns = 'SELECT GeoColumns.Id, GeoColumns.ColumnId FROM Results INNER JOIN GeoColumns  ON Results.ResultId = GeoColumns.ResultId WHERE Results.ResultId = ?'

	cur.execute(query_get_tables)
	tables = cur.fetchall()
	for i, table in enumerate(tables):
		id = table[0]
		cur.execute(query_get_geo_columns, (str(id),))
		lookup[id] = cur.fetchall()

	return lookup


def denote_errors(argv):

	file = open(argv[2], 'r')
	human_class = json.loads(''.join(file.readlines()))

	con = sqlite3.connect(argv[3])
	cur = con.cursor()

	cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='Errors'")
	if not cur.fetchall():
		# create table
		cur.execute("CREATE TABLE Errors(Id INTEGER PRIMARY KEY AUTOINCREMENT, ResultId INTEGER, ColumnId INTEGER, FOREIGN KEY(ResultId) REFERENCES Results(ResultId))")
		# insert errors
		lookup = get_table_geo_column_lookup(cur)
		for table_id in human_class:
			computed = [y for (x,y) in lookup[int(table_id)]]
			for col in human_class[table_id]['geo_columns']:
				if not (col in computed):
					cur.execute('INSERT INTO Errors VALUES (null, ?, ?)', (table_id, col))
			for col in computed:
				if not (col in human_class[table_id]['geo_columns']):
					cur.execute('INSERT INTO Errors VALUES (null, ?, ?)', (table_id, col))
			con.commit()
	return

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
	if argv[1] == '--create_template':
		create_evaluation_template(argv[3], TableReader(argv[2]), argv[4:])
	elif argv[1] == '--calculate_statistics':
		calculate_statistics(argv)
	elif argv[1] == '--denote_errors':
		denote_errors(argv)
	else:
		info_service(TableReader(argv[2]), argv)
if __name__ == "__main__":
	main(len(sys.argv), sys.argv)

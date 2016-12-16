#!/usr/bin/python3

import sqlite3
import sys
import ast

HELP_TEXT = '\033[1mplot_report.py\033[0m database destination'

TEMPLATE_REPORT = 'evaluation/templates/report_tpl.tex'

TEMPLATE_TABLE = 'evaluation/templates/table_tpl.tex'

AUTHOR = 'AUTOGENERATE DOCUMENT'


def processResult(cur, result):
	query = 'SELECT * FROM Results'
	cur.execute(query)
	rows = cur.fetchall()
	return

def generateTableTexCode(id, table, url, geoColumns):
	# TODO read template
	tpl = read_tpl(TEMPLATE_TABLE)
	table_name = 'TABLE ' + str(id)

	table_schema = ''
	for i in range(len(table)):
		isGeo = (i in geoColumns)
		if i in geoColumns:
			table_schema += '| l | '
		else:
			table_schema += 'l '
	table_schema = table_schema[:-1]

	rows = ''
	transpose = [list(i) for i in zip(*table)]
	for row in transpose:
		rows += ''.join([x+' & ' for x in row[:-1]]) + row[-1] + ' \\\\\n'

	for i in range(len(tpl[1])):
		if tpl[1][i] == ' TABLE_NAME ':
			tpl[1][i] = table_name
		if tpl[1][i] == ' TABLE_SCHEMA ':
			tpl[1][i] = table_schema
		if tpl[1][i] == ' ROWS ':
			tpl[1][i] = rows
		if tpl[1][i] == ' URL ':
			tpl[1][i] = url

	return buildFromTpl(tpl)

def generateTexDocument(tableCodes, dest):
	# TODO read template
	tpl = read_tpl(TEMPLATE_REPORT)
	# TODO insert tableCodes into template
	print(tpl)
	for i in range(len(tpl[1])):
		if tpl[1][i] == ' AUTHOR ':
			tpl[1][i] = AUTHOR
		if tpl[1][i] == ' CONTENT ':
			tpl[1][i] = ''.join(tableCodes)
	texFile = open(dest+'.tex', 'w')
	texFile.write(buildFromTpl(tpl))
	# TODO save tex document
	# TODO call pdflatex on tex document
	return

def processOutput(cur, dest):
	# TODO define query to get the table
	queryGetTables = 'SELECT Results.ResultId, Results.Url, Results.DWTC_Table FROM Results'
	# TODO define query to get geo columns
	queryGetGeoColumns = 'SELECT GeoColumns.ColumnId FROM Results INNER JOIN GeoColumns  ON Results.ResultId = GeoColumns.ResultId WHERE Results.ResultId = ?'
	# TODO generate latex code for table
	cur.execute(queryGetTables)
	tables = cur.fetchall()

	texCodes = []
	for i, table in enumerate(tables):
		if i < 3: # TODO remove this at the end
			id, url, relations = table
			relations = ast.literal_eval(relations)
			cur.execute(queryGetGeoColumns, (str(id),))
			geoCols = [x[0] for x in cur.fetchall()]
			texCodes.append(generateTableTexCode(id, relations, url, geoCols))

	return texCodes

def read_tpl(filename):
	f = open(filename, 'r')
	# result = []
	data = f.read()
	result = ([],[])
	splits = data.split('>>')
	for part in splits:
		part = part.split('<<')
		result[0].append(part[0])
		if len(part) ==  2:
			result[1].append(part[1])
	return result

def buildFromTpl(tpl):
	# print(tpl[0][:-1])
	return ''.join([x + tpl[1][i] for i, x in enumerate(tpl[0][:-1])]) + tpl[0][-1]

def main(argc, argv):
	if (argc < 3):
		print(HELP_TEXT)
	else:
		db_path = argv[1]
		dest = argv[2]

		con = sqlite3.connect(db_path)
		cur = con.cursor()

		tableTexCodes = processOutput(cur, dest)
		generateTexDocument(tableTexCodes, dest)


if __name__ == "__main__":
	main(len(sys.argv), sys.argv)

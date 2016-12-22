#!/usr/bin/python3

import sqlite3
import sys
import ast
import cgi

HELP_TEXT = '\033[1mplot_report.py\033[0m database destination'

TEMPLATE_REPORT = 'evaluation/templates/report_tpl.html'

TEMPLATE_TABLE = 'evaluation/templates/table_tpl.html'

AUTHOR = 'AUTOGENERATE DOCUMENT'


def processResult(cur, result):
	query = 'SELECT * FROM Results'
	cur.execute(query)
	rows = cur.fetchall()
	return

def generateTableHTMLCode(id, table, url, geoColumns, headerRows):
	# TODO read template
	tpl = read_tpl(TEMPLATE_TABLE)
	table_name = 'TABLE ' + str(id)
	html_url = '<a href="' + cgi.escape(url, quote=True) + '">' + cgi.escape(url) + '</a>'

	rows = ''
	transpose = [list(i) for i in zip(*table)]
	for i, row in enumerate(transpose):
		if i in headerRows:
			rows += '<tr class="header-row">'
		else:
			rows += '<tr>'
		for j, x in enumerate(row):
			if j in geoColumns:
				rows += '<td class="geo-entity">' + cgi.escape(x) + '</td>'
			else:
				rows += '<td>' + cgi.escape(x) + '</td>'
		rows += '</tr>\n'

	for i in range(len(tpl[1])):
		if tpl[1][i] == ' TABLE_NAME ':
			tpl[1][i] = table_name
		if tpl[1][i] == ' ROWS ':
			tpl[1][i] = rows
		if tpl[1][i] == ' URL ':
			tpl[1][i] = html_url

	return buildFromTpl(tpl)

def generateHTMLDocument(tableCodes, dest):
	# read template
	tpl = read_tpl(TEMPLATE_REPORT)
	# insert content into template
	print(tpl)
	for i in range(len(tpl[1])):
		if tpl[1][i] == ' AUTHOR ':
			tpl[1][i] = AUTHOR
		if tpl[1][i] == ' CONTENT ':
			tpl[1][i] = ''.join(tableCodes)
	htmlFile = open(dest, 'w')
	htmlFile.write(buildFromTpl(tpl))
	htmlFile.close()
	return

def processOutput(cur, dest):
	# query to get the table
	queryGetTables = 'SELECT Results.ResultId, Results.Url, Results.DWTC_Table FROM Results'
	# query to get geo columns
	queryGetGeoColumns = 'SELECT GeoColumns.ColumnId FROM Results INNER JOIN GeoColumns  ON Results.ResultId = GeoColumns.ResultId WHERE Results.ResultId = ?'
	# query to get headers
	queryGetHeaderRows = 'SELECT Headers.RowNumber FROM Results INNER JOIN Headers ON Results.ResultId = Headers.ResultId WHERE Results.ResultId = ?'

	cur.execute(queryGetTables)
	tables = cur.fetchall()

	HTMLCodes = []
	for i, table in enumerate(tables):
		id, url, relations = table
		relations = ast.literal_eval(relations)
		cur.execute(queryGetGeoColumns, (str(id),))
		geoCols = [x[0] for x in cur.fetchall()]
		cur.execute(queryGetHeaderRows, (str(id),))
		headerRows = [x[0] for x in cur.fetchall()]
		HTMLCodes.append(generateTableHTMLCode(id, relations, url, geoCols, headerRows))

	return HTMLCodes

def read_tpl(filename):
	f = open(filename, 'r')
	data = f.read()
	result = ([],[])
	splits = data.split('}}')
	for part in splits:
		part = part.split('{{')
		result[0].append(part[0])
		if len(part) ==  2:
			result[1].append(part[1])
	return result

def buildFromTpl(tpl):
	return ''.join([x + tpl[1][i] for i, x in enumerate(tpl[0][:-1])]) + tpl[0][-1]

def main(argc, argv):
	if (argc < 3):
		print(HELP_TEXT)
	else:
		db_path = argv[1]
		dest = argv[2]

		con = sqlite3.connect(db_path)
		cur = con.cursor()

		tableHTMLCodes = processOutput(cur, dest)
		generateHTMLDocument(tableHTMLCodes, dest)


if __name__ == "__main__":
	main(len(sys.argv), sys.argv)

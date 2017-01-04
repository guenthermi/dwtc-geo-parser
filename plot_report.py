#!/usr/bin/python3

import sqlite3
import sys
import ast
import cgi

HELP_TEXT = '\033[1mplot_report.py\033[0m database destination'

TEMPLATE_REPORT = 'evaluation/templates/report_tpl.html'

TEMPLATE_TABLE = 'evaluation/templates/table_tpl.html'

AUTHOR = 'AUTOGENERATE DOCUMENT'


def process_result(cur, result):
	query = 'SELECT * FROM Results'
	cur.execute(query)
	rows = cur.fetchall()
	return

def generate_table_HTML(id, table, url, quality, geo_columns, header_rows, rubbish_rows):
	# read template
	tpl = read_tpl(TEMPLATE_TABLE)

	html_url = '<a href="' + cgi.escape(url, quote=True) + '">' + cgi.escape(url) + '</a>'
	table_name = 'TABLE ' + str(id)
	if not quality:
		table_name += ' - (<span class="important">Rejected for classification</span>)'

	rows = ''
	transpose = [list(i) for i in zip(*table)]
	for i, row in enumerate(transpose):
		css_classes = []
		if i in rubbish_rows:
			css_classes.append('rubbish-row')
		if i in header_rows:
			css_classes.append('header-row')
		if css_classes:
			rows += '<tr class="' + ', '.join(css_classes) + '">'
		else:
			rows += '<tr>'
		for j, x in enumerate(row):
			if j in geo_columns:
				rows += '<td class="geo-entity">' + cgi.escape(x) + '</td>'
			else:
				rows += '<td>' + cgi.escape(x) + '</td>'
		rows += '</tr>\n'
	rows += '<tr>'
	for i, col in enumerate(table):
		if i in geo_columns:
			rows += '<td>'
			for i, interpretation in enumerate(geo_columns[i]):
				if i != 0:
					rows += '</br>'
				value = str(interpretation[0]) + '; ' + str(interpretation[2])
				if interpretation[1]:
					rows += '<b>' + value + '</b>'
				else:
					rows += value
				interpretation[0]
		else:
			rows += '<td></td>'
	rows += '</tr>'

	for i in range(len(tpl[1])):
		if tpl[1][i] == ' TABLE_NAME ':
			tpl[1][i] = table_name
		if tpl[1][i] == ' ROWS ':
			tpl[1][i] = rows
		if tpl[1][i] == ' URL ':
			tpl[1][i] = html_url

	return build_from_tpl(tpl)

def generate_HTML_document(table_codes, dest):
	# read template
	tpl = read_tpl(TEMPLATE_REPORT)
	# insert content into template
	for i in range(len(tpl[1])):
		if tpl[1][i] == ' AUTHOR ':
			tpl[1][i] = AUTHOR
		if tpl[1][i] == ' CONTENT ':
			tpl[1][i] = ''.join(table_codes)
	htmlFile = open(dest, 'w')
	htmlFile.write(build_from_tpl(tpl))
	htmlFile.close()
	return

def process_output(cur, dest):
	# query to get the table
	query_get_tables = 'SELECT Results.ResultId, Results.Url, Results.DWTC_Table, Results.Quality FROM Results'
	# query to get geo columns
	query_get_geo_columns = 'SELECT GeoColumns.Id, GeoColumns.ColumnId FROM Results INNER JOIN GeoColumns  ON Results.ResultId = GeoColumns.ResultId WHERE Results.ResultId = ?'
	# query to get interpretation for geo column
	query_get_interpretations = 'SELECT Interpretations.classification, Interpretations.Best, Interpretations.Info FROM GeoColumns INNER JOIN Interpretations  ON GeoColumns.Id = Interpretations.ColumnId WHERE GeoColumns.Id = ?'
	# query to get headers
	query_get_header_rows = 'SELECT Headers.RowNumber FROM Results INNER JOIN Headers ON Results.ResultId = Headers.ResultId WHERE Results.ResultId = ?'
	# query to get rubbishRows
	query_get_rubbish_rows = 'SELECT rubbishRows.RowNumber FROM Results INNER JOIN rubbishRows ON Results.ResultId = rubbishRows.ResultId WHERE Results.ResultId = ?'

	cur.execute(query_get_tables)
	tables = cur.fetchall()

	HTMLCodes = []
	for i, table in enumerate(tables):
		id, url, relations, quality = table
		relations = ast.literal_eval(relations)
		cur.execute(query_get_geo_columns, (str(id),))
		geo_cols_without_interpretations = cur.fetchall()
		geo_cols_with_interpretations = dict()
		for col in geo_cols_without_interpretations:
			cur.execute(query_get_interpretations, (str(col[0]),))
			geo_cols_with_interpretations[col[1]] = cur.fetchall()
		cur.execute(query_get_header_rows, (str(id),))
		header_rows = [x[0] for x in cur.fetchall()]
		cur.execute(query_get_rubbish_rows, (str(id),))
		rubbish_rows = [x[0] for x in cur.fetchall()]
		HTMLCodes.append(generate_table_HTML(id, relations, url, int(quality), geo_cols_with_interpretations, header_rows, rubbish_rows))

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

def build_from_tpl(tpl):
	return ''.join([x + tpl[1][i] for i, x in enumerate(tpl[0][:-1])]) + tpl[0][-1]

def main(argc, argv):
	if (argc < 3):
		print(HELP_TEXT)
	else:
		db_path = argv[1]
		dest = argv[2]

		con = sqlite3.connect(db_path)
		cur = con.cursor()
		print('Read data...')
		table_HTML_codes = process_output(cur, dest)
		print('Generate html...')
		generate_HTML_document(table_HTML_codes, dest)
		print('Succeeded!')


if __name__ == "__main__":
	main(len(sys.argv), sys.argv)

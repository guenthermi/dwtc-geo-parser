#!/usr/bin/python3

import sqlite3
import sys
import os

class DatabaseOutput:

	def __init__(self, filename, is_simple=True):
		if os.path.isfile(filename):
			os.remove(filename)
		self.con = sqlite3.connect(filename)
		self.cur = self.con.cursor()
		self.simple_schema = is_simple
		self.create_tables()
		print('Database output ínitialization done!')


	def create_tables(self):
		if self.simple_schema:
			self.cur.execute("CREATE TABLE Results(ResultId INTEGER PRIMARY KEY, Url TEXT, Quality INT, DWTC_Table TEXT)")
		else:
			self.cur.execute("CREATE TABLE Results(ResultId INTEGER PRIMARY KEY, Url TEXT, Quality INT)")
			self.cur.execute("CREATE TABLE DWTC(Id INTEGER, Row INTEGER, Col INTEGER, Cell TEXT, FOREIGN KEY(Id) REFERENCES Results(ResultId))")
		self.cur.execute("CREATE TABLE GeoColumns(Id INTEGER PRIMARY KEY AUTOINCREMENT, ResultId INTEGER, ColumnId INT, FOREIGN KEY(ResultId) REFERENCES Results(ResultId))")
		self.cur.execute("CREATE TABLE Interpretations(Id INTEGER PRIMARY KEY AUTOINCREMENT, ColumnId INTEGER, Classification TEXT, Info TEXT, FOREIGN KEY(ColumnId) REFERENCES GeoColumns(Id))")
		self.cur.execute("CREATE TABLE Headers(Id INTEGER PRIMARY KEY AUTOINCREMENT, ResultId INTEGER, RowNumber INT, Header TEXT, FOREIGN KEY(ResultId) REFERENCES Results(ResultId))")
		self.cur.execute("CREATE TABLE RubbishRows(Id INTEGER PRIMARY KEY AUTOINCREMENT, ResultId INTEGER, RowNumber INT, FOREIGN KEY(ResultId) REFERENCES Results(ResultId))")
		self.con.commit()

	def add_result(self, geo_columns, id, url, headers, rubbish_rows, quality, table):
		if self.simple_schema:
			self.cur.execute('INSERT INTO Results VALUES (?, ?, ?, ?)', (str(id), url, str(quality), str(table)))
		else:
			self.cur.execute('INSERT INTO Results VALUES (?, ?, ?)', (str(id), url, str(quality)))
		result_id = self.cur.lastrowid
		if not self.simple_schema:
			for i, col in enumerate(table):
				for j, cell in enumerate(col): 
					self.cur.execute('INSERT INTO DWTC VALUES (?, ?, ?, ?)', (str(result_id), str(j), str(i), cell))
		for column in geo_columns:
			self.cur.execute('INSERT INTO GeoColumns VALUES (null, ?, ?)', (str(result_id), column))
			column_id = self.cur.lastrowid
			for (name, info) in geo_columns[column]:
				self.cur.execute('INSERT INTO Interpretations VALUES (null, ?, ?, ?)', (str(column_id), name, info))
		for row_id in headers:
			self.cur.execute('INSERT INTO Headers VALUES (null, ?, ?, ?)', (str(result_id), str(row_id), str(headers[row_id])))
		for row_id in rubbish_rows:
			self.cur.execute('INSERT INTO RubbishRows VALUES (null, ?, ?)', (str(result_id), str(row_id)))
		self.con.commit()

def main(argc, argv):
	if (argc != 2):
		return
	db_output = DatabaseOutput(argv[1], False)
	d = dict()
	d['1'] = ['name1', 'name2']
	db_output.add_result(d, 120, 'http://www.example.com', [['test', 'nix'],['test2', 'nix2']], [['01', '02', '03'], ['11', '12', '13']])

if __name__ == "__main__":
	main(len(sys.argv), sys.argv)



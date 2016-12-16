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
		self.createTables()
		print('Initialization done!')


	def createTables(self):
		if self.simple_schema:
			self.cur.execute("CREATE TABLE Results(ResultId INTEGER PRIMARY KEY, Url TEXT, DWTC_Table TEXT)")
		else:
			self.cur.execute("CREATE TABLE Results(ResultId INTEGER PRIMARY KEY, Url TEXT)")
			self.cur.execute("CREATE TABLE DWTC(Id INTEGER, Row INTEGER, Col INTEGER, Cell TEXT, FOREIGN KEY(Id) REFERENCES Results(ResultId))")
		self.cur.execute("CREATE TABLE GeoColumns(Id INTEGER PRIMARY KEY AUTOINCREMENT, ResultId INTEGER, ColumnId INT, FOREIGN KEY(ResultId) REFERENCES Results(ResultId))")
		self.cur.execute("CREATE TABLE Interpretations(Id INTEGER PRIMARY KEY AUTOINCREMENT, ColumnId INTEGER, Classification TEXT, FOREIGN KEY(ColumnId) REFERENCES GeoColumns(Id))")
		self.cur.execute("CREATE TABLE Headers(Id INTEGER PRIMARY KEY AUTOINCREMENT, ResultId INTEGER, Header TEXT, FOREIGN KEY(ResultId) REFERENCES Results(ResultId))")
		self.con.commit()

	def addResult(self, geoColumns, id, url, headers, table):
		if self.simple_schema:
			self.cur.execute('INSERT INTO Results VALUES (?, ?, ?)', (str(id), url, str(table)))
		else:
			self.cur.execute('INSERT INTO Results VALUES (?, ?)', (str(id), url))
		resultId = self.cur.lastrowid
		if not self.simple_schema:
			for i, col in enumerate(table):
				for j, cell in enumerate(col): 
					self.cur.execute('INSERT INTO DWTC VALUES (?, ?, ?, ?)', (str(resultId), str(j), str(i), cell))
		for column in geoColumns:
			self.cur.execute('INSERT INTO GeoColumns VALUES (null, ?, ?)', (str(resultId), column))
			columnId = self.cur.lastrowid
			for name in geoColumns[column]:
				self.cur.execute('INSERT INTO Interpretations VALUES (null, ?, ?)', (str(columnId), name))
		for header in headers:
			self.cur.execute('INSERT INTO Headers VALUES (null, ?, ?)', (str(resultId), str(header)))
		self.con.commit()

def main(argc, argv):
	if (argc != 2):
		return
	dbOutput = DatabaseOutput(argv[1], False)
	d = dict()
	d['1'] = ['name1', 'name2']
	dbOutput.addResult(d, 120, 'http://www.example.com', [['test', 'nix'],['test2', 'nix2']], [['01', '02', '03'], ['11', '12', '13']])

if __name__ == "__main__":
	main(len(sys.argv), sys.argv)




import re
import numpy as np

from reader import *
import sys

RE_NUMBER = re.compile('^[\-]?[0-9]*,?[0-9]*\.?[0-9]*$')

RE_NO_NUMBER = re.compile('[a-z,A-Z]')

RE_ENGLISH = re.compile('^[a-z,A-Z,\-,\s,\'.]*$')

RE_ADDRESS = re.compile('^(([a-z,A-Z,\']*|[0-9]*)(\s|$)+)*$')

RE_GEO_COMLETE = re.compile('^(([a-z,A-Z,\-,\'.\,]*|[0-9]*)(\s|$)+)*$')

RE_NO_RUBBISH = re.compile('.*[a-z,A-Z,0-9].*')

class Rubbish:
	UNVALID, VALID, NUMBER, GEO = range(4) 

def rubbish(elem):
	if elem.isdigit():
		return Rubbish.NUMBER
	if (len(elem) < 2) or (not no_rubbish(elem)):
		return Rubbish.UNVALID
	if number(elem):
		return Rubbish.NUMBER
	if geo(elem):
		return Rubbish.GEO
	return Rubbish.VALID

def no_rubbish(elem):
	if RE_NO_RUBBISH:
		return True
	else:
		return False

def number(elem):
	if RE_NUMBER.match(elem):
		return True
	return False

def english_phrase(elem):
	if RE_ENGLISH.match(elem):
		return True
	return False

def address(elem):
	if RE_ADDRESS.match(elem):
		return True
	return False

def geo(elem):
	if RE_GEO_COMLETE.match(elem):
		return True
	return False

def process(table):
	# possible geo columns
	result = {'columns': [], 'column_indices':[]}

	# TODO determine table direction

	# detect rubbish rows and columns
	rubbishRows, rubbishCols = detectRubbish(table)

	# determine header, rubish rows
	headers = guess_header_positions(table, rubbishRows, rubbishCols)
	# print(headers)

	# remove rubbish rows and headers
	result = cleanup_table(table, rubbishRows, rubbishCols, headers)

	return result, headers

def cleanup_table(table, rubbishRows, rubbishCols, headers):
	result = {'columns': [], 'column_indices': []}

	for i, col in enumerate(table):
		newcol =  ([],[])
		count = 0
		for j, cell in enumerate(col):
			if (not (j in rubbishRows)) and (not (j in headers)):
				if rubbish(cell) == Rubbish.GEO:
					newcol[0].append(cell)
					newcol[1].append(j)
		if len(set(newcol[0])) > 1:
			result['columns'].append(newcol)
			result['column_indices'].append(i)
	return result

def guess_header_positions(table, rubbishRows, rubbishCols):
	interpretations = [] # col classification
	for i, col in enumerate(table):
		if not (i in rubbishCols):
			classes = []
			for j, cell in enumerate(col):
				if not (j in rubbishRows):
					classes.append(rubbish(cell))
			counts = np.bincount(classes)
			if (len(counts))> 1:
				interpretations.append(np.argmax(counts[1:])+1)
			else:
				interpretations.append(0)
		else:
			interpretations.append(0)
	headers = determine_headers(table, interpretations)
	return headers

def detectRubbish(table):
	rubbishRows = set()
	rubbishCols = set()
	# row-wise representation
	transpose = [list(i) for i in zip(*table)]

	# delete all rows that contain rubish
	rubbishRates = determineRubbishColumnRates(table)
	rubbishRows = set()
	for i, row in enumerate(transpose):
		rowClassification = classifyLine(row)
		counts = np.bincount(rowClassification)
		unvalid = False
		if counts[Rubbish.UNVALID] > (len(row) / 2):
			for j, elem in enumerate(row):
				if (rowClassification[j] == Rubbish.UNVALID) and (rubbishRates[j] < 0.5): # TODO replace 0.5 with meridian value
					unvalid = True
		if unvalid:
			rubbishRows.add(i)
	# remove rubbish rows -> new Transpose
	newTranspose = {'rows': [], 'indices': []}
	for i in range(len(transpose)):
		if not (i in rubbishRows):
			newTranspose['rows'].append(transpose[i])
			newTranspose['indices'].append(i)
	# remove rubbish cols
	newTable = [list(i) for i in zip(*newTranspose['rows'])]
	cleanNewTable = {'cols': [], 'col_indices': [], 'row_indices': newTranspose['indices']}
	for i, col in enumerate(newTable):
		classification = classifyLine(col)
		# print(np.argmax(np.bincount(classification)))
		if np.argmax(np.bincount(classification)) == Rubbish.UNVALID:
			rubbishCols.add(i)
	return rubbishRows, rubbishCols

def classifyLine(line):
	result = []
	for i, elem in enumerate(line):
		result.append(rubbish(elem))
	return result

def determine_headers(table, classes):
	# print(classes)
	result = dict()
	has_numbers = Rubbish.NUMBER in classes
	transpose = [list(i) for i in zip(*table)]
	for i, row in enumerate(transpose):
		count = 0
		others = 0
		non_unvalid = False
		for j, cell in enumerate(row):
			if classes[j] != 0:
				cl = rubbish(cell)
				if cl != Rubbish.UNVALID:
					non_unvalid = True
				if classes[j] != cl:
					if (classes[j] == Rubbish.NUMBER) and (cell != ''):
						count += 2
					else:
						if (cell == ''):
							count += 0.2
							others += 0.8
					if (cl == Rubbish.GEO) and (classes[j] == Rubbish.VALID):
						count += 0
					if (cl == Rubbish.UNVALID) and (not has_numbers):
						count += 0.4
				else:
					others +=1
		if non_unvalid:
			if count > 2:
				result[i] = row
				# print(i, [(x,rubbish(x)) for x in row])
			else:
				if (count == 2) and (others > 0) and ((i / len(transpose)) > 0.9 or ((i / len(transpose)) < 0.1)):
					result[i] = row
					# print(i, [(x,rubbish(x)) for x in row])
	return result

def determineRubbishColumnRates(table):
	result = []

	for col in table:
		rubishCount = 0
		for elem in col:
			if rubbish(elem) == Rubbish.UNVALID:
				rubishCount += 1
		result.append(rubishCount / len(col))
	return result

def main(argc, argv):
	reader = TableReader(argv[1])
	table = reader.getNextTable()
	while (table):
		line_count = reader.getLineCount()
		if line_count == int(argv[2]):
			print('get here')
			table['relation']
			print(process(table['relation']))
			break
		table = reader.getNextTable()

if __name__ == "__main__":
	main(len(sys.argv), sys.argv)

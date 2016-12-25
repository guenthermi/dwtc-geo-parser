
import re
import numpy as np

from reader import *
import sys

RE_NUMBER = re.compile('^[0-9]*,?[0-9]*\.?[0-9]*$')

RE_NO_NUMBER = re.compile('[a-z,A-Z]')

RE_ENGLISH = re.compile('^[a-z,A-Z,\s,\'.]*$')

RE_ADDRESS = re.compile('^(([a-z,A-Z,\']*|[0-9]*)(\s|$)+)*$')

RE_GEO_COMLETE = re.compile('^(([a-z,A-Z,\'.\,]*|[0-9]*)(\s|$)+)*$')

class Rubbish:
	UNVALID, VALID, NUMBER = range(3) 

def rubbish(elem):
	if elem.isdigit():
		return Rubbish.NUMBER
	if len(elem) < 2:
		return Rubbish.UNVALID
	if number(elem):
		return Rubbish.NUMBER
	return Rubbish.VALID

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

	# # for identification of header rows
	# has_numbers = False

	# TODO (1) determine table direction

	# (2) clean table (delete rubish)
	clean_table = cleanTable(table)

	# (3) determine header, rubish rows
	headers = guess_header_positions(clean_table)
	print(headers)

	# (4) Classify columns into rubish, numbers, string(valid)
	for i, col in enumerate(table): # iterate columns by index
		col_filtered = filter_col(col)
		newcol = col_filtered['col']
		has_numbers = has_numbers or col_filtered['has_numbers']
		if not len(newcol[0]) == 0:
			result['columns'].append(newcol)
			result['column_indices'].append(i)
	
	# TODO (5) identity possible geo columns

	# add headers to result
	result = remove_headers(result, headers)
	return result, headers

def filter_col(column):
	output = ([],[])
	count_others = 0
	has_numbers = False
	for i, elem in enumerate(column):
		v = rubbish(elem)
		if v == Rubbish.VALID:
			if geo(elem):
				output[0].append(elem)
				output[1].append(i)
			else:
				count_others += 1
		elif v == Rubbish.NUMBER:
			count_others += 1
			has_numbers = True
	if len(output[0]) < count_others:
		return {'col': ([],[]), 'has_numbers': has_numbers}
	return {'col': output, 'has_numbers': has_numbers}

def remove_headers(columns, header_guess):
	result = {'columns': [], 'column_indices':[]}
	now_empty = []
	for i, col in enumerate(columns['columns']):
		# col[0]: content, col[1]: indices
		newcol = ([],[])
		for j, entry in enumerate(col[1]):
			if not (entry in header_guess):
				newcol[0].append(col[0][j])
				newcol[1].append(col[1][j])
		if newcol != ([],[]):
			result['columns'].append(newcol)
			result['column_indices'].append(columns['column_indices'][i])
		# remove entrys with col[1][j] in header_guess for every j
		# check if header_guesses are the only entries in indices
	return result

# maybe use this as additional feature
def guess_header_positions_old(table, has_numbers):
	result = dict()
	if has_numbers:
		transpose = [list(i) for i in zip(*table)]
		for i, row in enumerate(transpose):
			containNumber = False
			for j in row:
				if (j != '') and number(j):
					containNumber = True
					break
			if not containNumber:
				result[i] = row
	return result

def guess_header_positions(table):
	# TODO create classificaton matrix by calling classifyLine on all non-rubish rows
	transpose = [list(i) for i in zip(*table['cols'])]
	matrix = []
	for row in transpose:
		matrix.append(classifyLine(row))
	# TODO call compareClassificationLines on matrix
	headers = determine_headers(matrix, table['row_indices'])

	result = dict()
	for i, row in enumerate(transpose):
		containNumber = False
		for j in row:
			if (j != '') and number(j):
				containNumber = True
				break
		if not containNumber:
			result[i] = row
	return result	

def cleanTable(table):
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
		if np.bincount(classification).argmax != Rubbish.UNVALID:
			cleanNewTable['cols'].append(col)
			cleanNewTable['col_indices'].append(i)
	return cleanNewTable

def classifyLine(line):
	result = []
	for elem in line:
		result.append(rubbish(elem))
	return result

def determine_headers(matrix, indices):
	# counts = []
	headers = []
	for i in range(len(matrix)-1):
		count = 0
		for j in range(len(matrix[0])):
			if matrix[i][j] != matrix[i+1][j]:
				count += 1
		# counts.append(count)
		if count > 1:
			headers.append(indices[i])
		else:
			if (count > 0) and (((indices[i] / indices[-1]) > 0.9) or ((indices[i] / indices[-1]) < 0.1)):
				headers.append(indices[i])
	return headers

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
			table['relation']
			print(process(table['relation']))
			break
		table = reader.getNextTable()

if __name__ == "__main__":
	main(len(sys.argv), sys.argv)


import re

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
	result = {'columns': [], 'column_indices':[]}
	has_numbers = False
	# iterate columns by index
	for i, col in enumerate(table):
		col_filtered = filter_col(col)
		newcol = col_filtered['col']
		has_numbers = has_numbers or col_filtered['has_numbers']
		if not len(newcol[0]) == 0:
			result['columns'].append(newcol)
			result['column_indices'].append(i)
	header_guess, headers = guess_header_positions(table, has_numbers)
	result = remove_headers(result, header_guess)
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
		# col[0]: content, col[1]: indecies
		newcol = ([],[])
		for j, entry in enumerate(col[1]):
			if not (entry in header_guess):
				newcol[0].append(col[0][j])
				newcol[1].append(col[1][j])
		if newcol != ([],[]):
			result['columns'].append(newcol)
			result['column_indices'].append(columns['column_indices'][i])
		# remove entrys with col[1][j] in header_guess for every j
		# check if header_guesses are the only entries in indecies
	return result

def guess_header_positions(table, has_numbers):
	result = []
	headers = []
	if has_numbers:
		transpose = [list(i) for i in zip(*table)]
		for i, row in enumerate(transpose):
			containNumber = False
			for j in row:
				if (j != '') and number(j):
					containNumber = True
					break
			if not containNumber:
				result.append(i)
				headers.append(row)
	return result, headers


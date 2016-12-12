#!/usr/bin/python3

import redis
import sys
import gzip

HELP_TEXT = "\033[1mcreateRedisIndex\033[0m source file"

HOST = 'localhost'
PORT = 6379
REDIS_DB = 0

MAX_LINE_COUNT = float('inf')


def connect():
	return redis.StrictRedis(host=HOST, port=PORT, db=REDIS_DB)

def readGeoNames(filename, r):
	f = gzip.open(filename, 'r')
	line_count = 0
	print('Start loading aliases from geo names...')
	for line in f:
		if line_count > MAX_LINE_COUNT:
			break
		line_count += 1
		
		if (line_count % 1000000) == 0:
			print(line_count, 'data from', line_count, 'geo entities are loaded')

		splits = line.split(b'\t')

		# add alisases
		aliases = set(splits[3].split(b','))
		aliases.add(splits[1])
		for alias in aliases:
			if (alias):
				ids = r.get(alias)
				if ids == None:
					ids = b''
				else:
					ids += b','
			ids += splits[0]
			r.set(alias, ids)

		# add content
		content_line = splits[6] + b'\t' + splits[7] + b'\t' + splits[8] + b'\t' + splits[14] + b'\t' + splits[17] # timezone
		r.set(splits[0], content_line)

	print('All aliases are loaded.')
	return

def main(argc, argv):
	if (argc != 2):
		print(HELP_TEXT)
	r = connect()
	r.flushall()
	readGeoNames(argv[1], r)
	print('End')



if __name__ == "__main__":
	main(len(sys.argv), sys.argv)



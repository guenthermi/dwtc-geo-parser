#!/usr/bin/python3

import ujson as json
import sys

# make sure that there is no cycle in the graph!!
MAX_ITERATION = 1000 # maximal number of nodes (to prevent infinite loops)

class CoverageTree:
	def __init__(self, config):
		f = open(config, 'r')
		data = json.loads(''.join(f.readlines()))
		self.origin = self._loadTree(data["0"], data)

	def _loadTree(self, node, data):
		count = 0
		result = dict()
		for key in node:
			if key == "successors":
				succs = []
				for id in node["successors"]:
					count += 1
					if count < MAX_ITERATION:
						succs.append(self._loadTree(data[id], data))
					else:
						print('ERROR: Maximal number of nodes reached. Either '
							+ 'your graph has cycles or there are simply to '
							+ 'much nodes', file=sys.stderr)
				result["successors"] = succs
			else:
				result[key] = node[key]
		return result

	def getOrigin(self):
		return self.origin


def main(argc, argv):
	if argc > 1:
		tree = CoverageTree(argv[1])
		print(tree.getOrigin())
	else:
		print('config file missing')

if __name__ == "__main__":
	main(len(sys.argv), sys.argv)


#!/usr/bin/python3

import ujson as json
import sys

# make sure that there is no cycle in the graph!!
MAX_ITERATION = 1000 # maximal number of nodes (to prevent infinite loops)

class CoverageTree:
	def __init__(self, config):
		f = open(config, 'r')
		data = json.loads(''.join(f.readlines()))
		self.node_lookup = self._create_lookup(data)
		self.origin = self._load_tree(data["0"], data)

	def _load_tree(self, node, data):
		count = 0
		result = dict()
		for key in node:
			if key == "successors":
				succs = []
				for id in node["successors"]:
					count += 1
					if count < MAX_ITERATION:
						succs.append(self._load_tree(data[id], data))
					else:
						print('ERROR: Maximal number of nodes reached. Either '
							+ 'your graph has cycles or there are simply to '
							+ 'much nodes', file=sys.stderr)
				result["successors"] = succs
			else:
				result[key] = node[key]
		return result

	def _create_lookup(self, data):
		result = dict()
		for id in data:
			# assume that names are unique
			result[data[id]['name']] = data[id]
		return result

	def get_origin(self):
		return self.origin

	def get_lookup(self):
		return self.node_lookup

def main(argc, argv):
	if argc > 1:
		tree = CoverageTree(argv[1])
		print(tree.get_origin())
	else:
		print('config file missing')

if __name__ == "__main__":
	main(len(sys.argv), sys.argv)


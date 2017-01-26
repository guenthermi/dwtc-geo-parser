#!/usr/bin/python3

import ujson as json
import sys
import copy

# make sure that there is no cycle in the graph!!
MAX_ITERATION = 1000 # maximal number of nodes (to prevent infinite loops)

class CoverageTree:
	def __init__(self, config):
		f = open(config, 'r')
		data = json.loads(''.join(f.readlines()))
		self.origin = self._load_tree(data["0"], data)
		self.node_lookup = self._create_lookup()

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

	def _create_lookup(self):
		result = dict()
		paths = [[copy.deepcopy(self.origin)]]
		found = True
		while found:
			found = False
			new_paths = []
			for path in paths:
				if path[-1]['successors']:
					for succ in path[-1]['successors']:
						new_paths.append(path + [succ])
					found = True
				else:
					new_paths.append(path)
			paths = new_paths
		for path in paths:
			for entry in path:
				if 'successors' in entry:
					del entry['successors']
			result[path[-1]['name']] = path
		return result

	def get_origin(self):
		return self.origin

	def get_lookup(self):
		return self.node_lookup

def main(argc, argv):
	if argc > 1:
		tree = CoverageTree(argv[1])
		lookup = tree.get_lookup()
		for key in lookup:
			print(key, lookup[key])
	else:
		print('config file missing')

if __name__ == "__main__":
	main(len(sys.argv), sys.argv)


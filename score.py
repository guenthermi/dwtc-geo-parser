#!/usr/bin/python3

import sys
import numpy as np

class Score:
	def __init__(self):
		self.scores = dict()
	def addScore(self, key, value):
		if key in self.scores:
			self.scores[key] += value
		else:
			self.scores[key] = value
	def getScore(self, key):
		return self.scores[key]
	def getMax(self):
		m = max(self.scores, key=lambda x: self.scores.get(x))
		return m, self.scores[m]

class ScoreSet:
	def __init__(self):
		self.scoreSet = dict()
	def addScores(self, name, scores):
		self.scoreSet[name] = scores
	def getScoreDistribution(self, key):
		# Returns for each possible value for key the number of occurences in scoreSet
		result = dict()
		for scoresName in self.scoreSet:
			if key in self.scoreSet[scoresName]:
				result[self.scoreSet[scoresName][key]] += 1
		return result

def main(argc, argv):
	print('TODO: do some tests')

if __name__ == "__main__":
	main(len(sys.argv), sys.argv)



class Scoring:
	def __init__(self, gaze):
		self.gaze = gaze

	def calculateScore(column):
		hNumFound = 0 # heuristic: how many entities are found
		hEquality = 0 # heuristic: 
		h

		# TODO get feature scores from gazetter
		response = gaze.lookupColumn(column)
		sumCounts = response['sumCounts'] # to determine what kind of geo entities are most propably in the column
		# TODO guess what kind of data is in the column

		hNumFound = len(column) / response['numFound']
		determineEqualityScore()
		# TODO call determineEqualityScore for features
		# TODO merge equality scores into one score
		return

	def determineMostProbableFeatures():
	# Features: FeatureClass (w=0.65), CountryCode (w=0.25), Timezone (w=0.05), FeatureCode (w=0.05)
	# for f in features: sum += -w(f)/ln(equality(f)); 

	def determineEqualityScore():
		# create average equality
		# maybe logorithmic scale
		return

	def 

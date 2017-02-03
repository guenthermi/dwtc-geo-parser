# DWTC-Geo-Parser (and Geo-Coder)

This repository contains the code for the Geoparser and Geocoder for the [Dresden Web Table Corpus](https://wwwdb.inf.tu-dresden.de/misc/dwtc/). It is able to classify geo entity columns for tables

# Setup

You need to install following python packages:
* redis
* ujson

Install: ````pip3 install redis ujson````

In addition you need redis and sqlite3

````sudo apt-get install redis-server sqlite3````


To run the code you have to install [redis.io](https://redis.io/) and start a redis server.

````
redis-server
````
After that you have to create the geo names index by running
````
# Download Geo Names Gazetteer Data
mkdir data
cd data
wget http://download.geonames.org/export/dump/allCountries.zip
unzip allCountries.zip
gzip allCountries.txt
cd ..

# Fill Redis Server with Data
./createRedisIndex.py data/allCountries.txt.gz
````
Redis will save a backup of the index in dwtc-geo-parser folder. The next time you start a redis server in this location the backup will be loded (which is much faster than recreating the index from allCountries.txt.gz).

To create the Wikidata class index run the wikidata_extrator. This can take a while.

````
cd wikidata_extractor
mvn install
java -classpath target/WikidataExtractor-0.0.1-SNAPSHOT-jar-with-dependencies.jar Main
cd ..
```` 

You can download the DWTC Corpus via:

````
cd data
for i in $(seq -w 0 500); do wget http://wwwdb.inf.tu-dresden.de/misc/dwtc/data_feb15/dwtc-$i.json.gz; done
cd ..
````

# Getting Started

You can test the geoparsing and geocoding by running:

````
./run 0-100 output.db report.html none data/dwtc-000.json.gz
````

# Geoparsing and Geocoding

To run the the geo parser and geocoder call `classify.py` where `selector` describes the range of input tables (e.g. `0-100`), `destination` is the location of the database for storing the results and `[dump]` a list of dump files of the DWTC Corpus.

````
./classify.py selector destination [dump]...
````

# Classify Errors

If you have human classified data in the right format (TODO: provide example) you can denote the errors of the classification of geo columns by running the following command:

````
./helper.py --denote_errors human_classification database
````

To calculate precision, recall and F1-Measure run:

````
./helper.py --calculate_statistics human_classification database
````

# Create HTML Output

You can create an HTML site which presents the output results of the geoparsing and geocoding by running:

````
./plot_report.py database destination
````

`database` has to by the location of the output database and `destination` is the path to the desired HTML page.

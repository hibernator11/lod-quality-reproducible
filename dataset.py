import rdflib
from SPARQLWrapper import SPARQLWrapper, JSON, XML
import time

class Dataset():
    def __init__(self, file):
        self.graph = rdflib.Graph()
        self.limit = 10
        #self.graph.parse("data/zeri-data-quality.ttl")
        self.graph.parse(file)
        self.sparqlEndpoint = SPARQLWrapper(self.getEndpoint())
        self.sparqlEndpoint.setReturnFormat(JSON)

    def getEndpoint(self):
        query = """
        SELECT DISTINCT ?sparql
        WHERE {
            ?s void:sparqlEndpoint ?sparql
        }"""

        qres = self.graph.query(query)

        endpoints = []
        for row in qres:
            endpoints.append(str(row.sparql))

        return endpoints[0]
    
    def getMetrics(self):
        query = """
        prefix dcterms: <http://purl.org/dc/terms/> 
        prefix skos: <http://www.w3.org/2004/02/skos/core#> 
        prefix schema: <https://schema.org/> 
        prefix wdt: <http://www.wikidata.org/prop/direct/> 
        prefix dqv: <http://www.w3.org/ns/dqv#> 
        
        SELECT DISTINCT ?query ?description ?dimensionLabel
        WHERE {{
            ?s void:sparqlEndpoint <{0}> .
            ?s dqv:hasQualityMeasurement ?qualityMeasurement .
            ?qualityMeasurement dqv:isMeasurementOf ?metric .
            ?metric schema:description ?description .
            ?metric schema:query ?query .
            ?metric dqv:inDimension ?dimension .
            ?dimension skos:prefLabel ?dimensionLabel
        }}""".format(self.getEndpoint())

        qres = self.graph.query(query)

        metrics = []
        for row in qres:
            
            query = str(row.query)
            description = str(row.description)
            dimension = str(row.dimensionLabel)
            metrics.append([query, description, dimension])

        return metrics
    
    def getDimensions(self):
        query = """
        prefix dcterms: <http://purl.org/dc/terms/> 
        prefix skos: <http://www.w3.org/2004/02/skos/core#> 
        prefix schema: <https://schema.org/> 
        prefix wdt: <http://www.wikidata.org/prop/direct/> 
        prefix dqv: <http://www.w3.org/ns/dqv#> 
        
        SELECT DISTINCT ?dimensionLabel
        WHERE {{
            ?s void:sparqlEndpoint <{0}> .
            ?s dqv:hasQualityMeasurement ?qualityMeasurement .
            ?qualityMeasurement dqv:isMeasurementOf ?metric .
            ?metric dqv:inDimension ?dimension .
            ?dimension skos:prefLabel ?dimensionLabel
        }}""".format(self.getEndpoint())

        qres = self.graph.query(query)

        dimensions = []
        for row in qres:
            dimension = str(row.dimensionLabel)
            dimensions.append(dimension)

        return dimensions
    
    def runDimension(self, dimension):
        
        query = """
        prefix dcterms: <http://purl.org/dc/terms/> 
        prefix skos: <http://www.w3.org/2004/02/skos/core#> 
        prefix schema: <https://schema.org/> 
        prefix wdt: <http://www.wikidata.org/prop/direct/> 
        prefix dqv: <http://www.w3.org/ns/dqv#> 
        
        SELECT DISTINCT ?query ?description ?description
        WHERE {{
            ?s void:sparqlEndpoint <{0}> .
            ?s dqv:hasQualityMeasurement ?qualityMeasurement .
            ?qualityMeasurement dqv:isMeasurementOf ?metric .
            ?metric schema:description ?description .
            ?metric schema:query ?query .
            ?metric dqv:inDimension ?dimension .
            ?dimension skos:prefLabel "{1}"@en
        }}""".format(self.getEndpoint(), dimension)
        
        qres = self.graph.query(query)
        result = ''
       
        start = time.time()

        for row in qres:
            textQuery = str(row.query)
            label = str(row.description)
            self.sparqlEndpoint.setQuery(textQuery.format(self.limit))
            
            try:
                ret = self.sparqlEndpoint.queryAndConvert()
               
                if ret:
                    result = 'ok'
                else:
                    result = "error"
        
            except Exception as e:
                print(e)

        end = time.time()        
        result = result + " - " + str(end - start) + " - " + label
        return result
 
    def runMetrics(self):
        self.sparqlEndpoint.setReturnFormat(JSON)
        
        for m in self.getMetrics():
            print('viene')
            textQuery = m[0]
            self.sparqlEndpoint.setQuery(textQuery.format(self.limit))
            print('xx',textQuery.format(self.limit))
        
            result = ''
            try:
                ret = self.sparqlEndpoint.queryAndConvert()
                
                if ret:
                    result = 'ok'
                else:
                    result = "not"
        
                #for r in ret["results"]["bindings"]:
                #    authors.append(r['name']['value'] + ' - ' + r['author']['value'])
               
            except Exception as e:
                print(e)

        return result
 
if __name__ == '__main__' :
    file = "data/zeri-data-quality.ttl"
    d = Dataset(file)
    endpoint = d.getEndpoint()
    print(endpoint)
    print(d.getMetrics())
    print(d.getDimensions())
    print(d.runMetrics())
    print(d.runDimension('Availability'))
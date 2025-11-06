import rdflib
from SPARQLWrapper import SPARQLWrapper, JSON, XML
import time
import json

class Dataset():
    def __init__(self, file):
        self.graph = rdflib.Graph()
        self.limit = 10
        
        #self.graph.parse("data/zeri-data-quality.ttl")
        self.graph.parse(file)
        self.sparqlEndpoint = SPARQLWrapper(self.getEndpoint())
        self.sparqlEndpoint.setReturnFormat(JSON)
        self.performance = "Performance"
        self.syntactic = "Syntactic validity"
        self.conciseness = "Conciseness"
        self.consistency = "Consistency"
        self.completeness_population = "Completeness-Population"
        self.completeness_population_check = "10"
        self.accuracy = "Accuracy"
        self.understandability_labels = "Understandability-Labels"
        self.RC_URIs_length = "Representational-Conciseness-URIs-Length"
        self.RC_Containers = "Representational-Conciseness-Containers"
        self.interpretability_viaf = "Interpretability-VIAF"
        self.interpretability_isni = "Interpretability-Isni"
        self.negatives = [self.conciseness, self.understandability_labels, self.RC_URIs_length, self.RC_Containers, self.interpretability_viaf, self.interpretability_isni,self.consistency]
        self.manual = [self.accuracy]
        self.performancelimit = 100
        self.syntacticlimit = 100

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
    
    def getTitle(self):
        query = """
        PREFIX dcterms: <http://purl.org/dc/terms/> 
        SELECT DISTINCT ?title
        WHERE {
            ?s dcterms:title ?title
        }"""

        qres = self.graph.query(query)

        title = []
        for row in qres:
            title.append(str(row.title))

        return title[0]
    
    
    def getDescription(self):
        query = """
        PREFIX dcterms: <http://purl.org/dc/terms/> 
        SELECT DISTINCT ?description
        WHERE {
            ?s dcterms:description ?description
        }"""

        qres = self.graph.query(query)

        description = []
        for row in qres:
            description.append(str(row.description))

        return description[0]
    
    def getCriteria(self):
        
        query = """
        prefix dcterms: <http://purl.org/dc/terms/> 
        prefix skos: <http://www.w3.org/2004/02/skos/core#> 
        prefix schema: <https://schema.org/> 
        prefix wdt: <http://www.wikidata.org/prop/direct/> 
        prefix dqv: <http://www.w3.org/ns/dqv#> 
        
        SELECT DISTINCT ?criterionLabel
        WHERE {{
            ?s void:sparqlEndpoint <{0}> .
            ?s dqv:hasQualityMeasurement ?qualityMeasurement .
            ?qualityMeasurement dqv:isMeasurementOf ?metric .
            ?metric skos:prefLabel ?criterionLabel .
            ?metric schema:query ?query 
        }}""".format(self.getEndpoint())
        
        #print(query)

        qres = self.graph.query(query)

        criteria = []
        for row in qres:
            criterion = str(row.criterionLabel)
            criteria.append(criterion)

        return criteria
    
    def getAssessmentResults(self):
        
        query = """
        prefix dcterms: <http://purl.org/dc/terms/> 
        prefix skos: <http://www.w3.org/2004/02/skos/core#> 
        prefix schema: <https://schema.org/> 
        prefix dqv: <http://www.w3.org/ns/dqv#> 
        
        SELECT DISTINCT ?dimensionLabel ?criterionLabel ?value
        WHERE {{
            ?s void:sparqlEndpoint <{0}> .
            ?s dqv:hasQualityMeasurement ?qualityMeasurement .
            ?qualityMeasurement dqv:isMeasurementOf ?metric .
            ?qualityMeasurement dqv:value ?value .
            ?metric skos:prefLabel ?criterionLabel .
            ?metric dqv:inDimension ?dimension .
            ?dimension skos:prefLabel ?dimensionLabel 
        }}""".format(self.getEndpoint())
        
        #print(query)

        qres = self.graph.query(query)

        assessment = []
        for row in qres:    
            value = str(row.value)
            if value =="1":
                value = "correct"
            else:
                value = "not satisfied"
            assessment.append({"dimension": str(row.dimensionLabel),
                               "criterion": str(row.criterionLabel), 
                               "value": value})
        return assessment
    
    def runCriterion(self, criterion):
        jsonResult = []
        
        query = """
        PREFIX dcterms: <http://purl.org/dc/terms/> 
        PREFIX skos: <http://www.w3.org/2004/02/skos/core#> 
        PREFIX schema: <https://schema.org/> 
        PREFIX wdt: <http://www.wikidata.org/prop/direct/> 
        PREFIX dqv: <http://www.w3.org/ns/dqv#> 
        PREFIX ldqd: <https://www.w3.org/2016/05/ldqd#>
        
        SELECT DISTINCT ?query ?description
        WHERE {{
            ?s void:sparqlEndpoint <{0}> .
            ?s dqv:hasQualityMeasurement ?qualityMeasurement .
            ?qualityMeasurement dqv:isMeasurementOf ?metric .
            ?metric schema:description ?description .
            ?metric schema:query ?query .
            ?metric skos:prefLabel "{1}" 
        }}""".format(self.getEndpoint(), criterion)
        
        qres = self.graph.query(query)
       
        sparqlResult = ''
        for row in qres:
            
            label = str(row.description)
            
            if criterion == self.performance:
                assessmentQuery = str(row.query).format(self.performancelimit)
                performance = self.assessPerformance(assessmentQuery)
                
                jsonResult.append({"query": assessmentQuery,"label": label, 
                                   "time": performance["time"],
                                   "sparqlResult": performance["result"],
                                   "sparqlResultRaw":"-"})
            
            else:
                assessmentQuery = str(row.query).format(self.limit)
                self.sparqlEndpoint.setQuery(assessmentQuery)
                
                #try:
                start = time.time()
                ret = self.sparqlEndpoint.queryAndConvert()
                print(ret)
                
                sparqlResult = "error"
                if criterion in self.negatives :
                    sparqlResult = 'ok'
                
                for r in ret["results"]["bindings"]:
                    #authors.append(r['name']['value'] + ' - ' + r['author']['value'])
                    # some criteria works inside out
                    if criterion in self.negatives :
                        sparqlResult = 'error'
                        break
                    elif criterion == self.completeness_population :
                        if r['total']['value'] == self.completeness_population_check:
                            sparqlResult = 'ok'
                    else: 
                        sparqlResult = 'ok'
                
                end = time.time()  
                jsonResult.append({"query": assessmentQuery,"label": label, 
                                   "time": str(round(end - start,2)),
                                   "sparqlResult":sparqlResult,
                                   "sparqlResultRaw":str(ret)})
            
                #except Exception as e:
                #    print(e)

        return jsonResult
    
    def assessPerformance(self, assessmentQuery):
        jsonResult = ''
        
        try:
            self.sparqlEndpoint.setQuery(assessmentQuery)
            
            total = 0
            one = 0
            for x in range(0, 10):
            
                start = time.time()
                ret = self.sparqlEndpoint.queryAndConvert()
                
                end = time.time()
                one = (end - start)
                total = total + one
            
            #print(total/10 <= one)
            jsonResult = {"time": str(round(total/10, 2)) + " (total/10) - " + str(round(one,2)), 
                               "result": str(total/10 <= one)}
        except Exception as e:
            print(e)
        
        return jsonResult
        
 
 
if __name__ == '__main__' :
    file = "data/crb-data-quality.ttl"
    #file = "data/bne-data-quality.ttl"
    
    d = Dataset(file)
    endpoint = d.getEndpoint()
    print(endpoint)
    #print(d.getCriteria())
    d.runCriterion('Conciseness')
    #d.runCriterion('Interpretability-Isni')
    #d.runCriterion('Completeness-Population')
    print(d.getAssessmentResults())

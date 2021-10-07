import json, datetime, requests 
from elasticsearch import Elasticsearch
import psutil
from queue import Queue
from time import sleep


#Defined variables
IndexName = "system_info"
ENDPOINT = 'http://localhost:9200/'

data_queue = Queue(maxsize=10)


#Functions start from here
def getListOfProcessSortedByMemory():
    '''
    Get list of running process sorted by Memory Usage
    '''
    listOfProcObjects = []
    # Iterate over the list
    for proc in psutil.process_iter():
       try:
           # Fetch process details as dict
           pinfo = proc.as_dict(attrs=['pid', 'name', 'username', 'memory_percent', 'cpu_percent'])
           pinfo['vms'] = proc.memory_info().vms / (1024 * 1024)
           # Append dict to list
           listOfProcObjects.append(pinfo);
       except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
           pass
    # Sort list of dict by key vms i.e. memory usage
    listOfProcObjects = sorted(listOfProcObjects, key=lambda procObj: procObj['vms'], reverse=True)
    return listOfProcObjects


class Curr_Date(object):
    def get():
        return datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")

class ELK(object):
    #Intitalize the connection with elasticsearch
    def __init__(self):
        self.es = Elasticsearch(timeout=600, hosts=ENDPOINT)
    #Fucntion to put info in elasticsearch
    def put(self, info):
        try:
            res  = {}
            for process in info:
                res = self.es.index(index=IndexName, doc_type='_doc', document=process)
            return res
        except Exception as e:
            print("Error while pushing the data into elasticSearch on ELKL : {}".format(e))
    def delete(self):
        self.es.indices.delete(index=IndexName, ignore=[400, 404])

def main():
    get_info = getListOfProcessSortedByMemory()
    _elk = ELK()
    _elk.delete()
    response = _elk.put(get_info)
    print(response)

if __name__=="__main__":
    while(1):
        main()
        sleep(5)

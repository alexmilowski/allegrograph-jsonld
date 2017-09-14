from flask import has_request_context, has_app_context, current_app, request
import requests
import json
import urllib
from pyld import jsonld

class RESTIOError(IOError):
   def __init__(self,msg,url,status,text):
      super().__init__(msg)
      self.url = url;
      self.status = status
      self.text = text

def uri_parameter(uris):
   return list(map(lambda x: '<' + str(x) + '>',uris))

def from_json(quads):
   subjects = {}
   for quad in quads:
      target = subjects.get(quad[0])
      if target is None:
         target = {'@id':quad[0]}
         subjects[quad[0]] = target
      value = target.get(quad[1])
      if value is None:
         target[quad[1]] = quad[2]
      elif type(value)==list:
         list.append(value)
      else:
         target[quad[1]] = [value,quad[2]]
   ld = list(subjects.values())
   if len(ld)==1:
      ld = ld[0]
   return ld


class AGraphConnection:
   def __init__(self,url,username=None,password=None):
      self.url = url
      if self.url[-1]=='/':
         self.url = self.url[0:-1]
      self.username = username
      self.password = password

   def get(self,graphs,subjects):
      params = {}
      if len(graphs)>0:
         params['context'] = uri_parameter(graphs)
      if len(subjects)>0:
         params['subj'] = uri_parameter(subjects)

      uri = self.url + '/statements'
      req = requests.get(uri,params=params,headers={'accept':'application/json'},auth=self.get_authentication())

      if (req.status_code>=200 or req.status_code<300):
         return from_json(json.loads(req.text))
      else:
         raise RESTIOError('Cannot get graphs {} and subjects {}, status={}'.format(graphs,subjects,req.status_code),uri,req.status_code,req.text)

   def query(self,q,limit=None,graphs=[]):
      params = {'query':str(q)}
      if limit is not None:
         params['limit'] = limit
      if len(graphs)>0:
         params['context'] = uri_parameter(graphs)

      uri = self.url
      req = requests.post(uri,params=params,headers={'accept':'application/json'},auth=self.auth)

      if (req.status_code>=200 or req.status_code<300):
         data = json.loads(req.text)
         return from_json(data)
      else:
         raise RESTIOError('Cannot query repository, graphs {}, status={}'.format(graphs,req.status_code),uri,req.status_code,req.text)

   def delete(self,graphs):
      params = {'context' : uri_parameter(graphs) }

      uri = self.url + '/statements'
      req = requests.delete(uri,params=params,auth=self.get_authentication())

      if (req.status_code<200 or req.status_code>=300):
         raise RESTIOError('Cannot delete graphs {}, status={}'.format(graphs,req.status_code),uri,req.status_code,req.text)

   def replace(self,data,graph):
      if graph is None:
         params = {}
      else:
         params = {'context':uri_parameter([graph])}

      content = jsonld.normalize(data, {'algorithm': 'URDNA2015', 'format': 'application/nquads'}).encode('utf-8')

      uri = self.url + '/statements'
      req = requests.put(uri,params=params,data=content,headers={'content-type':'text/plain; charset=utf-8'},auth=self.get_authentication())

      if (req.status_code<200 or req.status_code>=300):
         raise RESTIOError('Cannot replace graph {}, status={}'.format(graph,req.status_code),uri,req.status_code,req.text)

   def append(self,data,graph):
      if graph is None:
         params = {}
      else:
         params = {'context':uri_parameter([graph])}

      content = jsonld.normalize(data, {'algorithm': 'URDNA2015', 'format': 'application/nquads'}).encode('utf-8')

      uri = self.url + '/statements'
      req = requests.post(uri,params=params,data=content,headers={'content-type':'text/plain; charset=utf-8'},auth=self.get_authentication())

      if (req.status_code<200 or req.status_code>=300):
         raise RESTIOError('Cannot replace graph {}, status={}'.format(graph,req.status_code),uri,req.status_code,req.text)

      if (req.status_code<200 or req.status_code>=300):
         raise RESTIOError('Cannot append to graph {}, status={}'.format(graph,req.status_code),uri,req.status_code,req.text)

   def get_authentication(self):
      if self.username is None:
         if has_request_context() and request.authorization is not None:
            return (request.authorization.username, request.authorization.password)
         else:
            return None
      else:
         return (self.username, self.password)

def make_connection(url,username=None,password=None):
   return AGraphConnection(url,username,password)

def get_connection():
   if has_app_context():
      service_def = current_app.config.get('AGRAPH_SERVICE')
      return AGraphConnection(service_def.get('url'),username=service_def.get('username'),password=service_def.get('password'))
   else:
      raise ValueError('No connection can be created')

def get(graphs=[],subjects=[],connection=None):
   if connection is None:
      connection = get_connection()

   return connection.get(graphs,subjects)

def query(q,graphs=[]):
   if connection is None:
      connection = get_connection()

   return connection.query(q,graphs=graphs)

def delete_graph(graphs=[],connection=None):
   if connection is None:
      connection = get_connection()

   connection.delete(graphs)

def update_graph(data,graph=None,connection=None):
   if connection is None:
      connection = get_connection()

   return connection.replace(data,graph)

def append_graph(data,graph=None,connection=None):
   if connection is None:
      connection = get_connection()

   return connection.append(data,graph)

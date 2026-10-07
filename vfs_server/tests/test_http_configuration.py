import base64,http.client,json,tempfile,threading,unittest
from pathlib import Path
from vfs_server.server import create_server
class HTTPTests(unittest.TestCase):
 def test_token_read_write_and_restart(self):
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp);token=root/'token';token.write_text('fixture-secret')
   server=create_server(root/'data',port=0,token_file=str(token));thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
   def request(method,path,body=None,auth=None):
    conn=http.client.HTTPConnection('127.0.0.1',server.server_port,timeout=3)
    headers={'Content-Type':'application/json'}
    if auth:headers['Authorization']=auth
    conn.request(method,path,json.dumps(body) if body is not None else None,headers);response=conn.getresponse();status=response.status;data=json.loads(response.read());conn.close();return status,data
   try:
    body={'path':'/fixture','source':'test','content_b64':base64.b64encode(b'bits').decode()}
    self.assertEqual(request('POST','/artifacts',body)[0],401)
    self.assertEqual(request('POST','/artifacts',body,'Bearer wrong')[0],401)
    status,data=request('POST','/artifacts',body,'Bearer fixture-secret');self.assertEqual(status,201);digest=data['artifact']['digest']
    self.assertEqual(request('GET','/artifacts/'+digest)[0],401)
    self.assertEqual(request('GET','/artifacts/'+digest,auth='Bearer fixture-secret')[0],200)
    self.assertEqual(request('POST','/verify',{'digest':digest})[0],401)
    self.assertTrue(request('POST','/verify',{'digest':digest},'Bearer fixture-secret')[1]['verified'])
   finally:server.shutdown();thread.join();server.server_close()
   reopened=create_server(root/'data',port=0,token_file=str(token))
   try:self.assertEqual(reopened.RequestHandlerClass.store.read_content(digest),b'bits')
   finally:reopened.server_close()
if __name__=='__main__':unittest.main()

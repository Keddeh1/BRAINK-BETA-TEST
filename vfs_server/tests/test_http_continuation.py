import base64,http.client,json,socket,tempfile,threading,unittest,urllib.error
from pathlib import Path
from vfs_server.client import VFSClient
from vfs_server.model import ArtifactWrite
from vfs_server.server import create_server

class HTTPContinuationTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name);self.token=self.root/'token';self.token.write_text('owner-test-identity');self.servers=[]
 def tearDown(self):
  for server,thread in self.servers:server.shutdown();thread.join();server.server_close()
  self.tmp.cleanup()
 def start(self):
  server=create_server(self.root/'data',port=0,token_file=str(self.token));thread=threading.Thread(target=server.serve_forever,daemon=True);self.servers.append((server,thread));return server,thread
 def client(self,server):return VFSClient('http://127.0.0.1:'+str(server.server_port),'owner-test-identity')
 def request(self):return ArtifactWrite('/context',b'one','source://one',continuation_id='undertaking',expected_version=0)
 def test_lost_ack_retries_one_commit(self):
  server,thread=self.start();handler=server.RequestHandlerClass;original=handler.send_json;lost=[]
  def drop_first_ack(instance,status,body):
   if status==201 and not lost:
    lost.append(body);instance.connection.shutdown(socket.SHUT_RDWR);instance.connection.close();return
   original(instance,status,body)
  handler.send_json=drop_first_ack;thread.start()
  result=self.client(server).write(self.request())
  self.assertEqual(result,lost[0]);self.assertEqual(handler.store.verify_receipt_chain()['count'],1)
 def test_live_restart_preserves_old_result_and_new_binding(self):
  server,thread=self.start();thread.start();first=self.client(server).write(self.request())
  self.client(server).write(ArtifactWrite('/context',b'two','source://two',continuation_id='later',expected_version=1))
  server.shutdown();thread.join();server.server_close();self.servers.remove((server,thread))
  replacement,worker=self.start();worker.start()
  self.assertEqual(self.client(replacement).write(self.request()),first)
  self.assertEqual(replacement.RequestHandlerClass.store.resolve_path('/context').source,'source://two')
  self.assertEqual(replacement.RequestHandlerClass.store.verify_receipt_chain()['count'],2)
 def test_changed_request_conflicts(self):
  server,thread=self.start();thread.start();client=self.client(server);client.write(self.request())
  with self.assertRaises(urllib.error.HTTPError) as error:
   client.write(ArtifactWrite('/context',b'changed','source://one',continuation_id='undertaking',expected_version=0))
  self.assertEqual(error.exception.code,409);self.assertEqual(server.RequestHandlerClass.store.verify_receipt_chain()['count'],1)
 def test_unidentified_write_is_not_automatically_replayed(self):
  server,thread=self.start();handler=server.RequestHandlerClass
  def drop_ack(instance,status,body):
   instance.connection.shutdown(socket.SHUT_RDWR);instance.connection.close()
  handler.send_json=drop_ack;thread.start()
  with self.assertRaises(ConnectionError):
   self.client(server).write(ArtifactWrite('/context',b'one','source://one'))
  self.assertEqual(handler.store.verify_receipt_chain()['count'],1)

 def test_invalid_configuration(self):
  for endpoint in ['http://remote.example','http://user:pass@localhost','http://localhost/?x=1']:
   with self.assertRaises(ValueError):VFSClient(endpoint,'token')

if __name__=='__main__':unittest.main()

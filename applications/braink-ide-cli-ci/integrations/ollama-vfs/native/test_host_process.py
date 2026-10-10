import tempfile,unittest
from unittest.mock import patch
from host_process import start

class HostProcessTest(unittest.TestCase):
    def test_missing_executable_is_retained_not_reported_running(self):
        with tempfile.TemporaryDirectory() as root,patch('host_process.observe',return_value={'state':'SERVICE_UNAVAILABLE'}),patch('host_process.shutil.which',return_value=None),patch('host_process.subprocess.Popen') as spawn:
            result=start(root,root+'/models','native-host')
        spawn.assert_not_called();self.assertEqual(result['state'],'EXECUTABLE_ABSENT');self.assertTrue(result['receipt']['observer']['verified'])
    def test_existing_observed_service_is_not_duplicated(self):
        with tempfile.TemporaryDirectory() as root,patch('host_process.observe',return_value={'state':'SERVICE_OBSERVED','version':'test-fixture','models':[]}),patch('host_process.subprocess.Popen') as spawn:
            result=start(root,root+'/models','native-host')
        spawn.assert_not_called();self.assertEqual(result['process_ownership'],'EXISTING_SERVICE')

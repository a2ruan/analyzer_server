# Analyzer Server
This is a python webserver capable of automatically generating reports from test data via text recognition.  
This application is designed to function as a scalable data processing microservice.  
Powered using Python FastAPI and Bootstrap.

# Features
1. Automated report generation when connected to test database
2. Automated log data parsing and unit test reports
3. Ultra-fast text recognition algorithm capable of parsing 40k+ lines/s (10x faster than conventional fuzzy matching)
4. Scalable architecture that is deployable via EC2.  Multiple nodes can be run concurrently, and requires a load balancer.

# Demo
The following demo shows the webservice pulling data from a database, performing textual analysis from logs, then writing the results back to a results database.  
Finally, the results are shown graphically via a webpage for front-end users. 
Any new entries into the source database will be queued for analysis, and processed when the server is idle.
![](https://github.com/a2ruan/analyzer_server/blob/main/templates/images/report_demo.gif)

# Architecture
![Architecture Diagram](https://github.com/a2ruan/analyzer_server/blob/main/templates/images/system_architecture_diagram.PNG)

# Setup
Step 1: Install all requirements (requires python 3.10+)
```
pip install -r requirements.txt
```

Step 2: Click on the batch file start_server.bat to start the wsgi server.
```
start cmd.exe /k start_server.bat
```

# How to generate custom reports
## Analyzers
An analyzer is a python file with a single class named "Analyzer".  The analyzer class will have the following reserved keywords, that are injected into the Analyzer when the class is initialized: 

self.folder_path (this is the folder path containing the unzipped test logs)
self.test_details (this contains a dictionary of test details i.e uuid, test_case, test_log ect)
Inside that class, there is a mandatory function run(), which will be executed by the server whenever the user requests a report.  The purpose of run() is to return a dictionary containing all the unit test results.

```python

import sys
sys.path.append("..")
from analyzer import MetaAnalyzer # Inherit MetaAnalyzer, which is shared by all Analyzers.  Can use pre-build functions such as self.check_for_unexpected_reboot
 
class Analyzer(MetaAnalyzer):
    def __init__(self):
        super().__init__()
 
    def run(self):
        # The purpose of this function is to analyze all logs within this folder and subfolders, and return a dictionary of test results
        results = {}
        results["status"] = "pass" # Mandatory to return key with status = "pass" or "fail"
        results["warning"] = False # Mandatory to return key with status = True or False
         
        print("Reboot Check")
        if self.check_for_unexpected_reboot(self.folder_path): # Note: self.folder_path is a reserved variable that contains the folder path of the test logs
            results['unexpected_reboot'] = True
            results["status"] = "fail" # If an unexpected reboot occurs, the test should fail
        else: results['unexpected_reboot'] = False
 
        print("Check if USB check is failed")
        if self.check_usb_failure(self.folder_path):
            results['usb_check_failure'] = True
            results["warning"] = True # If USB enumeration is lost, the test should be listed as conditional_pass
        else: results['usb_check_failure'] = False
         
        return results
```

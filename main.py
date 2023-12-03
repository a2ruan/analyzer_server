# Main server

import threading
from interface import *
import shutil
from fastapi import FastAPI, Request
from starlette.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from variables import MetaVariables
import os
import time
import asyncio
import tarfile
import requests
from datetime import datetime
import json
templates = Jinja2Templates(directory="..")

PORT = 5600
app = FastAPI()

ENABLE_AUTOMATED_REPORT = True
REPORT_HASH = "04012023a" # change the report hash to regenerate old reports

def looping_task():
    # This task is for periodically reading from database, finding next job to run, and running reports (automated)
    dbc = database_connector()

    while ENABLE_AUTOMATED_REPORT:
        print(f"Starting Automated Report at: {time.time()}")
        # Step 0: Check if test_log size is greater than 20GB.  Delete oldest folders
        dest_fpath = f"C:\\Users\\gvle\\Desktop\\templogs\\"
        if os.path.exists(dest_fpath):
            cachable_analyzer_helper = AnalyzerHelper()
            dirsize = cachable_analyzer_helper.get_dir_size(dest_fpath)
            print(dirsize)
            max_time = 0
            min_time = 10000000000000000000000000
            if dirsize > 5000000000:
                print("MAX CACHE DETECTED.  DELETING OLDEST FILES")
                for it in os.scandir(dest_fpath):
                    if it.is_dir():
                        print(it.path)
                        folder_path = it.path
                        folder_modified_date = os.stat(folder_path).st_mtime
                        print(folder_modified_date)
                        folder_modified_datetime = datetime.fromtimestamp(folder_modified_date)

                        if folder_modified_date > max_time:
                            max_time = folder_modified_date
                        if folder_modified_date < min_time:
                            min_time = folder_modified_date
                mean_time = 0
                if max_time != 0 and min_time != 0:
                    mean_time = (max_time + min_time) / 2
                print("MEAN TIME")
                print(mean_time)
                folders_to_remove = []
                for it in os.scandir(dest_fpath):
                    if it.is_dir():
                        folder_path = it.path
                        folder_modified_date = os.stat(folder_path).st_mtime
                        if folder_modified_date < mean_time:
                            folders_to_remove.append(it.path)
                print("FOLDERS TO REMOVE:")
                print(len(folders_to_remove))
                for folders in folders_to_remove:
                    try:
                        shutil.rmtree(folders)
                    except Exception as e:
                        print(e)

        # Step 1: Fetch test data
        test_data = dbc.fetch_data()
        
        # Step 2: Identify test data with valid test logs, and row id above 25700, and report that is None
        keys = []
        key_map = {}
        for key in test_data: 
            keys.append(test_data[key]["id"])
            key_map[test_data[key]["id"]] = key
        test_id_sorted = sorted(keys)
        last_key = 0
        target_uuid = None
        for key in reversed(sorted(keys)):
            #print("#"*10)
            #print(key)
            #print(test_data[key_map[key]])
            
            targetable_row = True
            #print("REPORT HASH")
            #print(test_data[key_map[key]]["report_hash"])
            
            if test_data[key_map[key]]["report"] not in [None,"None",""] and test_data[key_map[key]]["report_hash"] == REPORT_HASH: 
                #print("Report Already Exists")
                targetable_row = False
            if test_data[key_map[key]]["test_log"] in [None,"None",""]: 
                targetable_row = False
                #print("Log doesn't exist")
            if test_data[key_map[key]]["id"] <= 20700: 
                #print("Row below 25700")
                targetable_row = False
            #print(targetable_row)
            if targetable_row:
                print("Found targetable row!")
                
                target_uuid = test_data[key_map[key]]["uuid"]
                print(target_uuid)
                break
        if target_uuid != None:
            try:
                r = requests.get(f"http://localhost:{PORT}/api/submit_job_json_return/uuid/{target_uuid}")
                result = r.json()
                print(r.json())
                if 'result' in result:
                    status = result['result']['status']
                    warning = result['result']['warning']
                    if status == "MISMATCH DETECTED":
                        test_status = "mismatch"
                    else:
                        status_result = False
                        warning_result = False
                        if status in ["pass","Pass",False,"false"]: status_result = True
                        if warning in ["fail","Fail",True,"true"]: warning_result = True
                        test_status = "pass"
                        if status_result == True and warning_result == True: test_status = "warning"
                        elif status_result == True and warning_result == False: test_status = "pass"
                        elif status_result == False: test_status = "fail"
                    print(f"Final Status: {test_status}")
                    dbc.write_to_table_by_uuid(table="department_name_test",uuid=target_uuid,payload={
                        "report":test_status,
                        "report_hash":REPORT_HASH
                    })
            except Exception as e:
                print(e)
                dbc.write_to_table_by_uuid(table="department_name_test",uuid=target_uuid,payload={
                        "report":"error",
                        "report_hash":REPORT_HASH
                    })
                print("Error!!")
                pass
                #dbc.write_to_table_by_uuid(table="department_name_test",uuid=target_uuid,payload={
                #        "report":"error"
                #}) 
        else:
            print("Sleeping for long time")
            time.sleep(60)
        time.sleep(5)

thread_main = threading.Thread(target=looping_task)
thread_main.setDaemon=True
thread_main.start()

ENABLE_CACHING = True  # This means server will not redownload files if already exists

task_status_dict = {}
task_status_string = {}
report_id_dict = {}

@app.get("/api/compare_tests")
def compare_tests(request:Request):
    return templates.TemplateResponse("analysis_server/templates/comparison_request.html", {"request":request})

@app.get("/api/compare/{hash_previous}/{hash_current}")
def generate_comparison_report(request:Request, hash_previous, hash_current):
    output = {}
    output_payload = {
            "request": request,
            "error_message": f"Error generating report."
        }
    try:
        reportmaker = report_maker()
        output = reportmaker.generate_report(hash_previous, hash_current)
        print("COMPARISON BELOW--")
        #print(json.dumps(output,indent=4))
    except Exception as e:
        output_payload = {
            "request": request,
            "error_message": f"Error generating report. {e}"
        }
        output = {}
    if output == {}:
        output_payload = {
            "request": request,
            "error_message": f"Error generating report.  Stop code 2."
        }
        return templates.TemplateResponse("analysis_server/templates/404_error.html", output_payload)

    payload = {
        "request":request,
        "comparison":output
    }

    return templates.TemplateResponse("analysis_server/templates/comparison.html", payload)

@app.get("/")
@app.get("/api/reports-list")
def reports_list(request: Request):
    return templates.TemplateResponse("analysis_server/templates/reports_list.html", {"request": request})

@app.get("/api/make_report/uuid/{uuid}")
def demo(uuid, request: Request):
    print("Starting demo")
    kwargs = {
        "uuid": uuid
    }
    print("Submitting job!")
    thread1 = threading.Thread(
        target=submit_job_by_uuid, args=(uuid, request,))
    thread1.start()
    # submit_job_by_uuid(uuid, request)
    print("DICTSIZE=")
    print(sys.getsizeof(report_id_dict))
    print("Done!")
    return templates.TemplateResponse("analysis_server/templates/submit_job.html", {"request": request, "kwargs": kwargs})

@app.get("/api/view_report/uuid/{uuid}")
def view_report_by_uuid(uuid, request: Request):
    print("DICTSIZE=")
    print(sys.getsizeof(report_id_dict))
    # print(report_id_dict)
    if uuid in report_id_dict:
        output_payload = report_id_dict[uuid]
        output_payload["cachel2"] = "L2"
        if "error_message" in output_payload:
            return templates.TemplateResponse("analysis_server/templates/404_error.html", output_payload)
        return templates.TemplateResponse("analysis_server/templates/demo.html", output_payload)
    else:
        # Redirect response if not found in cached memory
        response = RedirectResponse(url=f'/api/make_report/uuid/{uuid}')
        return response


@app.get("/get_job_progress/uuid/{uuid}")
async def demo(uuid, request: Request):
    if uuid in task_status_dict and uuid in task_status_string:
        return [task_status_dict[uuid], task_status_string[uuid]]
    else:
        return {}


def print_data_size(output):
    for i in range(100):
        print(output)

@app.get("/api/submit_job_json_return/uuid/{uuid}")
@app.get("/api/submit_job/uuid/{uuid}")
def submit_job_by_uuid(uuid, request: Request = None):
    try:
        src_url = request.url._url
        start_time = time.time()
        # Given a test uuid or file path, return a report
        print(uuid)

        task_status_dict[uuid] = 0
        task_status_string[uuid] = "Querying program database for test details"

        path = "default"
        test_details = "None"
        test_time_start = time.time()
        # Use a instance of AnalyzerHelper to allow for cached database results
        cachable_analyzer_helper = AnalyzerHelper()
        if os.path.exists(path):
            print("Will submit report using path")
            test_details = cachable_analyzer_helper.get_test_metadata(path)
        elif uuid not in [None, "none", "None"]:
            print(f"Getting using UUID = {uuid}")
            test_details = cachable_analyzer_helper.get_test_metadata(uuid)
        task_status_dict[uuid] = 15
        task_status_string[uuid] = "Copying files from dir to analyzer server"
        test_end_time = time.time()
        if test_details == None:
            error_message = "UUID invalid or no logs found in test_log folder"
            output_payload = {
                "request": request,
                "error_message": error_message
            }
            report_id_dict[uuid] = output_payload
            task_status_dict[uuid] = -1
            if "submit_job_json_return" in src_url: 
                return output_payload
            return templates.TemplateResponse("analysis_server/templates/404_error.html", output_payload)

        task_status_dict[uuid] = 30
        if "test_log" in test_details:
            if test_details["test_log"] not in [None, "none", "None"]:
                # Extract all logs to local server
                src_fpath = os.path.normpath(test_details['test_log'])
                print(src_fpath)
                dest_fpath = f"C:\\Users\\gvle\\Desktop\\templogs\\{test_details['uuid']}"

                copy_start_time = time.time()
                if os.path.exists(dest_fpath) and ENABLE_CACHING:
                    print("Assumes that there is already cached results")
                    cached_indicator = "cached"
                else:
                    try:
                        AnalyzerHelper().copy_and_extract_files(src_fpath, dest_fpath)
                    except Exception as e:
                        error_message = f"Error when copying files from dir due to network issues.  Please try again. {e}"
                        output_payload = {
                            "request": request,
                            "error_message": error_message
                        }
                        report_id_dict[uuid] = output_payload
                        task_status_dict[uuid] = -1
                        if "submit_job_json_return" in src_url: 
                            return output_payload
                        return templates.TemplateResponse("analysis_server/templates/404_error.html", output_payload)
                    cached_indicator = "non-cached"

                dir_size = round(AnalyzerHelper().get_dir_size(
                    dest_fpath)/1000000, 2)  # Directory size in MB

                task_status_dict[uuid] = 60
                task_status_string[uuid] = f"Processing data and analyzing files ({dir_size} MB)"
                copy_end_time = time.time()
                # return test_details
                # Finally, analyze the folder
                print("_"*100)
                print("Start time")
                print(test_details['start_time'])

                result = cachable_analyzer_helper.analyze(
                    test_details['analyzer'], dest_fpath)
                
                # Seperate pm log section from results
                pm_log_stats = {"PM Log not found":""}
                if "pm_log_stats" in result:
                    pm_log_stats = result["pm_log_stats"]
                    result.pop("pm_log_stats")

                
                
                task_status_dict[uuid] = 80
                task_status_string[uuid] = "Getting computer configuration data from test logs"
                print(result)

                if result == {}:
                    error_message = "Unable to find a mapped analyzer.  This means that the test_case_name or test_case_module is not mapped to a valid analyzer, therefore no analysis can be performed."
                    output_payload = {
                        "request": request,
                        "error_message": error_message
                    }
                    report_id_dict[uuid] = output_payload
                    task_status_dict[uuid] = -1
                    if "submit_job_json_return" in src_url: 
                        return output_payload
                    return templates.TemplateResponse("analysis_server/templates/404_error.html", output_payload)
                
                start_time2 = time.time()
                config_info = cachable_analyzer_helper.get_config_metadata(uuid) or {
                }
                if "uuid" in config_info:
                    config_info.pop("uuid")
                task_status_dict[uuid] = 90
                task_status_string[uuid] = "Getting firmware configuration data from test logs"
                firmware_info = cachable_analyzer_helper.get_firmware_metadata(uuid) or {
                }
                if "uuid" in firmware_info:
                    firmware_info.pop("uuid")
                print("FW COMPONENTS")
                fw_components = {}
                try:
                    if "fw_components" in firmware_info:
                        fw_components = eval(firmware_info["fw_components"])
                        firmware_info.pop("fw_components")
                except: fw_components = {}

                additional_time = time.time() - start_time2
                
                print(additional_time)
                print("Additional Time used:")
                print("Copying time took:")
                print(copy_start_time-copy_end_time)

                elapsed_time = round(time.time() - start_time, 2)
                print("TEST TIME:")
                print(test_time_start-test_end_time)
                
                output_payload = {
                    "request": request,
                    "cached_indicator": cached_indicator,
                    "dir_size": dir_size,
                    "elapsed_time": elapsed_time,
                    "firmware_info": firmware_info,
                    "pm_log_stats":pm_log_stats,
                    "fw_components":fw_components,
                    "config_info": config_info,
                    "result": result,
                    "test_details": test_details,
                    "descriptions": MetaVariables.result_descriptions,
                    "cachel2":"L0"
                }
                
                if "submit_job_json_return" in src_url: # For jobs that don't need json
                    output_payload = {
                        "result": result,
                        "test_details": test_details,
                    }
                    return output_payload

                report_id_dict[uuid] = output_payload
                task_status_string[uuid] = "Finished analysis.  Opening report soon."
                task_status_dict[uuid] = 100
                if "submit_job_json_return" in src_url: 
                    return output_payload
                return templates.TemplateResponse("analysis_server/templates/demo.html", output_payload)
                return result
            return test_details
        else:
            return "Invalid"
    except Exception as e:
        error_message = f"No test logs found! {e}"
        output_payload = {
            "request": request,
            "error_message": error_message
        }
        report_id_dict[uuid] = output_payload
        task_status_dict[uuid] = -1
        return templates.TemplateResponse("analysis_server/templates/404_error.html", output_payload)

@app.get("/get_data")
async def get_table():
    db_connector = database_connector()
    output_dict = db_connector.fetch_data(table="department_name_test", columns=[
                                          "id", "test_case", "test_log", "uuid", "start_time", "current_time", "status"])
    print(len(output_dict))
    return output_dict


@app.get("/get_files")
async def get_files(request: Request):
    try:
        path = request.headers.get('path')
        if os.path.exists(path):
            arr = os.listdir(path)
            # print(arr)
        return arr
    except:
        return {}


def read_root():
    return {"Hello": "World"}


if __name__ == "__main__":
    db_connector = database_connector()
    output_dict = db_connector.fetch_data(table="department_name_test", columns=[
                                          "id", "test_case", "test_log", "uuid", "start_time", "current_time", "status"])
    print(len(output_dict))

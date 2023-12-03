import sys
sys.path.append("..")
import asyncio, time, os, tarfile, shutil
from database_connector import database_connector
from variables import MetaVariables
import importlib.util, importlib
from interface import *
from difflib import SequenceMatcher

ENABLE_CACHING = True  # This means server will not request test results repeatedly

class AnalyzerHelper:
    def __init__(self, test_details=None, **kwargs):
        self.metadata_cache = {}
        self.test_case_map = MetaVariables.test_case_map
        self.result_descriptions = MetaVariables.result_descriptions

    def get_test_details(self, search_str):
        db_connector = database_connector()
        test_details = {}
        if self.metadata_cache != {} and ENABLE_CACHING: output_dict = self.metadata_cache
        else:
            output_dict = db_connector.fetch_data(table="department_name_test", columns=[
                                                  "id", "test_case", "computer_name", "driver", "device_id", "firmware_uuid", "test_log", "uuid", "current_cycles", "target_cycles", "start_time", "current_time", "status","local_time"])
            self.metadata_cache = output_dict
        test_details = {}
        for row in output_dict:
            if output_dict[row]['test_log'] == None: continue
            if output_dict[row]['test_log'] in search_str or search_str in output_dict[row]['test_log']:
                test_details = output_dict[row]
                break
            elif str(output_dict[row]['uuid']) in search_str or search_str in str(output_dict[row]['uuid']):
                test_details = output_dict[row]
                break
        if test_details == {}: return None
        return test_details

    def get_firmware_metadata(self, search_str):
        # The purpose is to find the test, and return it's metadata
        # Search string can be test_log path or uuid (str)
        print(f"SEARCH STRING = {search_str}")
        db_connector = database_connector()
        test_details = self.get_test_details(search_str)
        if test_details == {}: return None
        # Also append system config data
        output_dict = db_connector.fetch_data(table="department_name_firmwarebuilder", columns=[
                                              "b_build_num", "device_firmware_id", "firmware_name", "firmware_nickname", "device_firmware_name", "table_id", "table_rev", "board_part_num", "repo_loc","fw_components"])
        config_info = {}
        for row in output_dict:
            if output_dict[row]['b_build_num'] == test_details['firmware_uuid']:
                config_info = output_dict[row]
                break

        return config_info

    def get_config_metadata(self, search_str):
        # The purpose is to find the test, and return it's metadata
        # Search string can be test_log path or uuid (str)
        print(f"SEARCH STRING = {search_str}")
        db_connector = database_connector()
        test_details = self.get_test_details(search_str)

        if test_details == {}: return None

        # Also append system config data
        output_dict = db_connector.fetch_data(table="department_name_configuration", columns=[
                                              "uuid", "program", "program_date","program_internal","program_internal_date","test2", "testerinternal", "programfwt", "quark","programxio", "agm", "motherboard", "processor", "socket", "sb", "fw1", "imu", "fw2", "fw3_g", "fw4_fw1", "fw4_fw2"])
        config_info = {}
        for row in output_dict:
            if output_dict[row]['uuid'] == test_details['uuid']:
                config_info = output_dict[row]
                break

        return config_info

    def get_test_metadata(self, search_str):
        # The purpose is to find the test, and return it's metadata
        # Search string can be test_log path or uuid (str)
        print(f"SEARCH STRING = {search_str}")
        db_connector = database_connector()
        test_details = self.get_test_details(search_str)
        if test_details == {}: return None
        else: self.test_details = test_details

        # Also append json data into output dict
        output_dict = db_connector.fetch_data(
            table="department_name_json", columns=["id", "json_data", "uuid"])
        for json_row in output_dict:
            if output_dict[json_row]['uuid'] == test_details['uuid']:
                for test_case_type in self.test_case_map:
                    if test_case_type in output_dict[json_row]['json_data']:
                        test_details['TP::testcase_module'] = test_case_type
                        test_details['analyzer'] = self.test_case_map[test_case_type]
                        break

        # Worst case scenario, just put test case details into json
        if "TP:testcase_module" not in test_details:
            test_details['TP::testcase_module'] = "Unable to find test case module in variables.py map.  Selecting next best analyzer."
            test_details['analyzer'] = "default"
            for fuzzy_test_case in self.test_case_map:
                print(fuzzy_test_case)
                if fuzzy_test_case in test_details['test_case']:
                    test_details['analyzer'] = self.test_case_map[fuzzy_test_case]
                    break
        return test_details

    def analyze(self, test_case, path):
        # Analyzes all logs found in folder and subfolders of path (must be unzipped or un-tar)
        # Test case is the key value of the self.test_case_map of this class
        # The output is a json file containing all results from the specific mapped test_case

        try:
            print("STARTING ANALYSIS")
            print(test_case)
            spec = importlib.util.spec_from_file_location("Analyzer", test_case)
            foo = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(foo)
            try:
                temp_analyzer = foo.Analyzer()
                temp_analyzer.test_details = self.test_details
                temp_analyzer.folder_path = path
                results = temp_analyzer.run()
                
                # Check if fail status is mismatched with pass status
                if "status" in results and "status" in self.test_details:
                    if results["status"] in [True,"pass","Pass"] and self.test_details["status"] in [False,"fail","Fail"]:
                        results["status"] = "MISMATCH DETECTED"
                        print("Mismatch detected!")
                else:
                    print("Warning!")
                #results["status"] = "MISMATCH DETECTED"
            except Exception as e:
                print(e)
                return {}
            print(f"RESULTS!!! = {results}")
            return results
        except:
            return {}

    def get_dir_size(self, path='.'):
        total = 0
        with os.scandir(path) as it:
            for entry in it:
                if entry.is_file():
                    if ".zip" in entry.name or ".tar" in entry.name: pass
                    else: total += entry.stat().st_size 
                elif entry.is_dir(): total += self.get_dir_size(entry.path)     
        return total

    def copy_and_extract_files(self, src_fpath, dest_fpath):
        # Copies file or folder from one location to another, while extracting a duplicate of all .zip, .tar, .tar.gz files in all subdirectories
        if os.path.exists(dest_fpath):
            shutil.rmtree(dest_fpath)
        try:
            shutil.copytree(src_fpath, dest_fpath)  # for folders
        except:
            # For zip files and tar.gz files
            os.makedirs(dest_fpath, exist_ok=True)
            shutil.copy(src_fpath, dest_fpath)

        for path, subdirs, files in os.walk(dest_fpath):
            for name in files:
                print(os.path.join(path, name))

                fname = os.path.join(path, name)
                if fname.endswith("tar.gz"):
                    print("EXTRACT1")
                    tar = tarfile.open(fname, "r:gz")
                    tar.extractall(path=path)
                    tar.close()
                elif fname.endswith("tar"):
                    print("EXTRACT2")
                    tar = tarfile.open(fname, "r:")
                    tar.extractall(path=path)
                    tar.close()
                elif fname.endswith(".zip"):
                    shutil.unpack_archive(fname, path, "zip")

# Purpose of the report maker is to generate comparasion reports between two stacks, given a UUID

import sys
import time
sys.path.append("..")
from database_connector import database_connector
from sqlalchemy import create_engine, text, inspect
import asyncio
from datetime import datetime
import uuid, json
import copy

class report_maker:
    def __init__(self):
        self.db_connector = database_connector()



    def get_most_common_key(self, dict_list):
        # Given a dictionary, return the key with the highest value
        most_common_item = ""
        most_common_frequency = 0
        for item in dict_list:
            if item == None:
                continue
            if dict_list[item] > most_common_frequency:
                most_common_frequency = dict_list[item]
                most_common_item = item
        return most_common_item

    def generate_report(self, previous_uuid=None, current_uuid=None):
        try:
            report_output = {}
            
            # Generate report
            if previous_uuid == None and current_uuid == None:
                previous_uuid = "dc07a681-b74d-4f2c-af87-90212362a01f"
                current_uuid = "9860fc8b-f8b3-45b4-8f6b-3d8fb61c6de9"

            # Table 1: firmware Component Comparison
            previous_firmware_payload = {}
            current_firmware_payload = {}

            # Table 2: Driver Comparison Table
            previous_driver_info = {}
            current_driver_info = {}

            # Table 3: Systems Tested Info
            previous_systems_tested_info = {}
            current_systems_tested_info = {}


            # ---------------------------------------

            # Step 1: Import all test data into dictionary
            self.department_name_test_data = self.db_connector.fetch_data(table="department_name_test", columns=["id","test_case","computer_name","test_log","report","driver","firmware_uuid","uuid","start_time","current_time","status","report_hash"])

            # Step 2: Import all firmware info into dictionary
            self.department_name_firmwarebuilder_data = self.db_connector.fetch_data(table="department_name_firmwarebuilder", columns=[
                                                "b_build_num", "device_firmware_id", "firmware_name", "firmware_nickname", "device_firmware_name", "table_id", "table_rev", "board_part_num", "repo_loc","fw_components"])
            # Step 3: Import all computer configuration info into dictionary
            self.department_name_configuration_data = self.db_connector.fetch_data(table="department_name_configuration", columns=[
                                                "uuid", "program", "program_date","program_internal","program_internal_date","test2", "testerinternal", "programfwt", "quark","programxio", "agm", "motherboard", "processor", "socket", "sb", "fw1", "imu", "fw2", "fw3_g", "fw4_fw1", "fw4_fw2"])

            # Step 4: Import reb Metrics
            self.department_name_reb_metrics = self.db_connector.fetch_data(table="department_name_reb_metrics", columns=["uuid","min_fw_post_time","sample_size"])


            # Step 4: Generate tables
            print(len(self.department_name_configuration_data))
            print(len(self.department_name_firmwarebuilder_data))
            print(len(self.department_name_test_data))

            # Step 5: Find test info for both previous and current test data
            previous_test_info = {}
            current_test_info = {}
            for row in self.department_name_test_data:
                row_data = self.department_name_test_data[row]
                if str(row_data['uuid']) in previous_uuid:# uuid.UUID(previous_uuid):
                    previous_test_info = row_data
                    #print(self.department_name_test_data[row])
                elif str(row_data['uuid']) in current_uuid:# == uuid.UUID(current_uuid):
                    current_test_info = row_data
                    #print(self.department_name_test_data[row])
                
                if previous_test_info != {} and current_test_info != {}:
                    break
            
            if previous_test_info == {} or current_test_info == {}: 
                print("Unable to find all uuid's.  Fail.")
                return {}
            
            # Get current and previous firmware information
            for row in self.department_name_firmwarebuilder_data:
                row_data = self.department_name_firmwarebuilder_data[row]
                
                if row_data["b_build_num"] == previous_test_info["firmware_uuid"]:
                    
                    print("FOUND A")
                    #print(row_data)
                    previous_firmware_payload = row_data
                if row_data["b_build_num"] == current_test_info["firmware_uuid"]:
                    
                    print("FOUND B")
                    #print(row_data)
                    current_firmware_payload = row_data
            
            print(type(previous_firmware_payload["fw_components"]))
            print(type(current_firmware_payload["fw_components"]))
            # Weird issue where identical string cannot be eval sequentially.  W/A is to set previous firmware and current firmware if data is the same
            if previous_firmware_payload["fw_components"] == current_firmware_payload["fw_components"]:
                print("Identical")
                previous_firmware_payload["fw_components"] = eval(previous_firmware_payload["fw_components"])
                current_firmware_payload["fw_components"] = previous_firmware_payload["fw_components"]
            else:
                previous_firmware_payload["fw_components"] = eval(previous_firmware_payload["fw_components"])
                current_firmware_payload["fw_components"] = eval(current_firmware_payload["fw_components"])

            print(json.dumps(previous_firmware_payload,indent=4))
            print(json.dumps(current_firmware_payload,indent=4))

            # Get all similar tests based on same driver and same firmware (bbuildnum)
            previous_uuid_similar = {}
            current_uuid_similar = {}

            for row in self.department_name_test_data:
                row_data = self.department_name_test_data[row]
                if row_data["driver"] == previous_test_info["driver"] and row_data["firmware_uuid"] == previous_test_info["firmware_uuid"]:
                    previous_uuid_similar[row] = row_data
                elif row_data["driver"] == current_test_info["driver"] and row_data["firmware_uuid"] == current_test_info["firmware_uuid"]:
                    current_uuid_similar[row] = row_data
            
            print(f"Found {len(previous_uuid_similar)} tests similar to previous uuid")
            print(f"Found {len(current_uuid_similar)} tests similar to current uuid")
            
            
            # Remap computer config information to have uuid as key, for faster access
            self.department_name_configuration_data_remapped = {}
            
            for row in self.department_name_configuration_data:
                row_data = self.department_name_configuration_data[row]
                self.department_name_configuration_data_remapped[row_data["uuid"]] = row_data
            
            # Remap reb matric information to have uuid as key, for faster access
            self.department_name_reb_metrics_remapped = {}

            for row in self.department_name_reb_metrics:
                row_data = self.department_name_reb_metrics[row]
                self.department_name_reb_metrics_remapped[row_data["uuid"]] = row_data
            print("LLL")
            previous_driver_info = self.get_driver_components(previous_uuid_similar)
            
            current_driver_info = self.get_driver_components(current_uuid_similar)
            
            # Generate comparasion table
            driver_comparator = {}
            for driver_key, driver_info in current_driver_info.items():
                print(previous_driver_info[driver_key])
                print(driver_info)
                if driver_key in previous_driver_info:
                    if previous_driver_info[driver_key] == driver_info:
                        driver_comparator[driver_key] = {
                            "current":driver_info,
                            "previous":""
                        }
                    else:
                        driver_comparator[driver_key] = {
                            "current":driver_info,
                            "previous":f"Yes ({previous_driver_info[driver_key]})"
                        }

            report_output["driver_comparison"] = {
                "data":driver_comparator
            }

            # Get all unique computers and firmware bootup time
            previous_computers = self.get_computer_info(previous_uuid_similar)
            current_computers = self.get_computer_info(current_uuid_similar)

            print(json.dumps(previous_computers,indent=4))
            print(json.dumps(current_computers,indent=4))
            ####################################################
            report_output["current_computers"] = {
                "data":current_computers
            }

            # Get firmware comparison table
            ####################################################
            firmware_comparison = self.firmware_component_comparator(previous_firmware_payload,current_firmware_payload)
            report_output["firmware_comparison"] = {
                "data":firmware_comparison
            }

            print(json.dumps(firmware_comparison, indent=4))
            
            # Add stack information
            previous_driver = previous_test_info["driver"]
            current_driver = current_test_info["driver"]

            current_firmware = current_firmware_payload["firmware_name"]
            previous_firmware = previous_firmware_payload["firmware_name"]

            current_table = ""
            previous_table = ""
            try:
                current_table = current_firmware_payload["table_id"] + "-" + current_firmware_payload["table_rev"]
                previous_table = previous_firmware_payload["table_id"] + "-" + previous_firmware_payload["table_rev"]
            except:
                pass

            current_fw1 = current_driver_info["fw1"]
            previous_fw1 = previous_driver_info["fw1"]

            current_firmware_nickname = self.get_nickname(current_firmware)
            previous_firmware_nickname = self.get_nickname(previous_firmware)

            stack_info = {
                "previous_driver":previous_driver,
                "current_driver":current_driver,
                "current_firmware":current_firmware,
                "previous_firmware":previous_firmware,
                "current_fw1":current_fw1,
                "previous_fw1":previous_fw1,
                "previous_firmware_nickname":previous_firmware_nickname,
                "current_firmware_nickname":current_firmware_nickname,
                "current_table":current_table,
                "previous_table":previous_table
            }

            report_output["stack_info"] = stack_info

            # Generate current pass/fail rate for each test case
            test_comparison = {}
            #import ipdb
            #ipdb.set_trace()
            
            test_comparison = self.get_test_case_comparison(current_uuid_similar)
            test_comparison_previous_stack = self.get_test_case_comparison(previous_uuid_similar)

            # Sort dictionary
            print(test_comparison.keys())
            print("------")
            order = ["firmware","install","reb_cb","reb_wb","reb_s3","reb_s4","reb","link","pcie","smu","reb","decode","usb","3dwl","amf","_dpm","ren","fr","time","heaven","wildlife","portroyal"]
            completed_tests = []
            sorted_test_comparison = {}

            for keyword in order:
                print(f"-->{keyword}")
                for key in copy.deepcopy(test_comparison):
                    print(f"KEY:{key}")
                    try:
                        if keyword in key.lower() and key not in completed_tests:
                            print("---->MATCHED")
                            completed_tests.append(key)
                            sorted_test_comparison[key] = test_comparison[key]
                            print(key + "\n") 
                    except:
                        pass
            # Add all remaining tests:
            for key in copy.deepcopy(test_comparison):
                if key not in completed_tests and key not in ["null",None,"None"]:
                    sorted_test_comparison[key] = test_comparison[key]

            # Add previous result check
            for key in copy.deepcopy(sorted_test_comparison):
                for test in test_comparison_previous_stack:
                    if test == key:
                        sorted_test_comparison[key]["previous_fail_count"] = test_comparison_previous_stack[test]["current_fail_count"]

            # Generate stack score
            stack_score = 0
            cumulative_failures = 0
            cumulative_tests = 0
            for key in sorted_test_comparison:
                cumulative_tests += sorted_test_comparison[key]["total_test_count"]
                cumulative_failures += sorted_test_comparison[key]["current_fail_count"]
            stack_score = int(round((cumulative_tests-cumulative_failures)/cumulative_tests*100,0))

            print("PRINTING COMPARISON")
            print(json.dumps(sorted_test_comparison,indent=4))
            report_output["test_case_info"] = {
                "metadata":{
                "stack_score":stack_score
                },
                "data":sorted_test_comparison
            }


        except Exception as e:
            print(e)
            return {}
        print("DONE!")
        return report_output
    
    def get_test_case_comparison(self, input_dict):
        current_uuid_similar = input_dict
        test_comparison = {}
        for test in current_uuid_similar:
            try:
                test_case = current_uuid_similar[test]["test_case"]
                if test_case in ["null"]: continue
                report = current_uuid_similar[test]["report"]
                status = current_uuid_similar[test]["status"]
                
                if test_case in test_comparison:
                    test_comparison[test_case]["total_test_count"] += 1
                    if report in ["fail"] or status in ["fail"]:#,"running"]:
                        test_comparison[test_case]["current_fail_count"] += 1
                    
                    test_comparison[test_case]["fail_rate"] = int(round(test_comparison[test_case]["current_fail_count"]/test_comparison[test_case]['total_test_count']*100,0))
                
                else:
                    test_comparison[test_case] = {
                        "test_case":test_case,
                        "total_test_count": 1,
                        "current_fail_count":0,
                        "fail_rate":0,
                        "previous_fail_count":-1,
                        "color_code":0
                    }
                    if report in ["fail"] or status in ["fail","running"]:
                        test_comparison[test_case]["current_fail_count"] = 1
                    test_comparison[test_case]["fail_rate"] = int(round(test_comparison[test_case]["current_fail_count"]/test_comparison[test_case]['total_test_count']*100,0))
                    

            except Exception as k:
                print(k)
        return test_comparison

    def get_nickname(self, name):
        if "_" in name:
            tokens = name.split("_")
            if len(tokens) >= 2:
                for token in tokens:
                    if "PRD" in token or "BRP" in token:
                        return token
        return ""

    def get_computer_info(self, uuid_dict):
        output = {}
        list_of_reb_cb_reb_wb = []

        # Remap reb metrics table for mor convenient key/value


        for row in uuid_dict:
            try:
                row_data = uuid_dict[row]
                config_data = self.department_name_configuration_data_remapped[row_data['uuid']]
                #print(config_data)
                motherboard = config_data['motherboard']
                cpu = config_data['processor']
                if "bkc" in row_data['computer_name'].lower():
                    pc_name = row_data['computer_name'].upper()
                else:
                    pc_name = row_data['computer_name'].upper().replace("SYSC","")

                mobo_type = "A+A Desktop"
                if "intel" in cpu.lower():
                    mobo_type = "I+A Desktop"

                if pc_name in output:
                    output[pc_name]["motherboard"] = motherboard
                    output[pc_name]["cpu"] = cpu
                else:
                    output[pc_name] = {
                        'type':mobo_type,
                        'computer_name':pc_name.strip(),
                        'motherboard':motherboard.strip(),
                        'cpu':cpu.strip(),
                        "min_fw_post_time":"N/A"
                    }

                # Add firmware POST TIME
                
                if "reb_cb" in row_data["test_case"] or "reb_wb" in row_data["test_case"]:
                    print(f"FOUND for {row_data['computer_name']}")
                    # Check in reb metrics for POST time information
                    
                    try:
                        reb_metrics = self.department_name_reb_metrics_remapped[row_data['uuid']]
                        # Make sure sample size >=5
                        #print(reb_metrics)
                        if float(reb_metrics["sample_size"]) <= 5:
                            pass
                            #print("Sample size too small")
                        elif output[pc_name]['min_fw_post_time'] == "N/A":
                            output[pc_name]['min_fw_post_time'] = float(reb_metrics['min_fw_post_time'])
                        elif reb_metrics['min_fw_post_time'] < output[pc_name]['min_fw_post_time']:
                            output[pc_name]['min_fw_post_time'] = float(reb_metrics['min_fw_post_time'])
                        
                    except Exception as e:
                        #print(f"No reb metrics FOUND for {row_data['computer_name']}::{row_data['test_case']}")
                        print(e)
                        pass
            except Exception as p:
                print(p)

        return output

    def firmware_component_comparator(self, firmware_info_previous, firmware_info_current):
        # given two firmware components, make a comparison table between the two
        # key = column name, value1 = current version, value2 = Yes (previous version)
        print("DEBUG")
        print(firmware_info_previous)
        print(firmware_info_current)
        print("DONE")
        comparator = {}
        for index, value in firmware_info_current["fw_components"].items():
            fw_component = index.replace("_" + value["image_version"],"")
            comparator[fw_component] = {
                "current":value["image_version"],
                "previous":""
            }
            
            for index_i, value_i in firmware_info_previous["fw_components"].items():
                fw_component_i = index_i.replace("_" + value_i["image_version"],"")
                print(f"{fw_component_i} / {fw_component}")
                if fw_component_i == fw_component:
                    print(f'{value_i["image_version"]} / {value["image_version"]}')
                    if value_i["image_version"] != value["image_version"]:
                        comparator[fw_component]["previous"] = f"Yes ({value_i['image_version']})"
                    print("MATCH! \n")
        print("WAITING")
        # Lastly, add table info

        current_table = f"{firmware_info_current['table_id']}-{firmware_info_current['table_rev']}"
        previous_table = f"{firmware_info_previous['table_id']}-{firmware_info_previous['table_rev']}"
        comparator["table"] = {
            "current":current_table,
            "previous":""
        }
        if current_table != previous_table:
            comparator["table"]["previous"] = f"Yes ({previous_table})"

        return comparator
                
    def get_driver_components(self, dict_input):
        # Get current computer config information.  Will use most frequently non-zeroed values
        payload = {
            "fw3_G":"",
            "fw1":"",
            "IMU":"",
            "fw2":"",
        }
        print("KKK")
        fw3_g = {}
        fw1 = {}
        imu = {}
        fw2 = {}
        for test in dict_input:
            try:
                test_data = self.department_name_configuration_data_remapped[dict_input[test]['uuid']]
                if test_data["fw3_g"] not in fw3_g: fw3_g[test_data["fw3_g"]] = 1
                else: fw3_g[test_data["fw3_g"]] += 1

                if test_data["fw1"] not in fw1: fw1[test_data["fw1"]] = 1
                else: fw1[test_data["fw1"]] += 1

                if test_data["imu"] not in imu: imu[test_data["imu"]] = 1
                else: imu[test_data["imu"]] += 1

                if test_data["fw2"] not in fw2: fw2[test_data["fw2"]] = 1
                else: fw2[test_data["fw2"]] += 1
            except:
                print(f"Error reading {test}")

        payload = {
            "fw3_G":self.get_most_common_key(fw3_g),
            "fw1":self.get_most_common_key(fw1),
            "IMU":self.get_most_common_key(imu),
            "fw2":self.get_most_common_key(fw2),
        }
        print(payload)    
        return payload

if __name__ == "__main__":
    
    reportmaker = report_maker()
    reportmaker.generate_report("c87533c8-22d5-4ba6-99e6-d0279dc5410d","3d1dc9ea-5c60-4b29-b0f2-fb1a486cd7e1")



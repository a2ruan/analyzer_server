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

            # Table 1: IFWI Component Comparison
            previous_ifwi_payload = {}
            current_ifwi_payload = {}

            # Table 2: Driver Comparison Table
            previous_driver_info = {}
            current_driver_info = {}

            # Table 3: Systems Tested Info
            previous_systems_tested_info = {}
            current_systems_tested_info = {}


            # ---------------------------------------

            # Step 1: Import all test data into dictionary
            self.bkc_regression_test_data = self.db_connector.fetch_data(table="bkc_regression_test", columns=["id","test_case","computer_name","test_log","report","driver","vbios_uuid","uuid","start_time","current_time","status","report_hash"])

            # Step 2: Import all IFWI info into dictionary
            self.bkc_regression_ifwibuilder_data = self.db_connector.fetch_data(table="bkc_regression_ifwibuilder", columns=[
                                                "bios_build_num", "asic_ifwi_id", "ifwi_name", "ifwi_nickname", "asic_ifwi_name", "pptable_id", "pptable_rev", "board_part_num", "repo_loc","fw_components"])
            # Step 3: Import all computer configuration info into dictionary
            self.bkc_regression_configuration_data = self.db_connector.fetch_data(table="bkc_regression_configuration", columns=[
                                                "uuid", "orc3", "orc3_date","orc3_internal","orc3_internal_date","papi2", "agt_internal", "amdvbflash", "quark","amdxio", "agm", "motherboard", "processor", "socket", "sbios", "pmfw", "imu", "psp_tos", "rlc_g", "pdfw_fw1", "pdfw_fw2"])

            # Step 4: Import ACPI Metrics
            self.bkc_regression_acpi_metrics = self.db_connector.fetch_data(table="bkc_regression_acpi_metrics", columns=["uuid","min_fw_post_time","sample_size"])


            # Step 4: Generate tables
            print(len(self.bkc_regression_configuration_data))
            print(len(self.bkc_regression_ifwibuilder_data))
            print(len(self.bkc_regression_test_data))

            # Step 5: Find test info for both previous and current test data
            previous_test_info = {}
            current_test_info = {}
            for row in self.bkc_regression_test_data:
                row_data = self.bkc_regression_test_data[row]
                if str(row_data['uuid']) in previous_uuid:# uuid.UUID(previous_uuid):
                    previous_test_info = row_data
                    #print(self.bkc_regression_test_data[row])
                elif str(row_data['uuid']) in current_uuid:# == uuid.UUID(current_uuid):
                    current_test_info = row_data
                    #print(self.bkc_regression_test_data[row])
                
                if previous_test_info != {} and current_test_info != {}:
                    break
            
            if previous_test_info == {} or current_test_info == {}: 
                print("Unable to find all uuid's.  Fail.")
                return {}
            
            # Get current and previous ifwi information
            for row in self.bkc_regression_ifwibuilder_data:
                row_data = self.bkc_regression_ifwibuilder_data[row]
                
                if row_data["bios_build_num"] == previous_test_info["vbios_uuid"]:
                    
                    print("FOUND A")
                    #print(row_data)
                    previous_ifwi_payload = row_data
                if row_data["bios_build_num"] == current_test_info["vbios_uuid"]:
                    
                    print("FOUND B")
                    #print(row_data)
                    current_ifwi_payload = row_data
            
            print(type(previous_ifwi_payload["fw_components"]))
            print(type(current_ifwi_payload["fw_components"]))
            # Weird issue where identical string cannot be eval sequentially.  W/A is to set previous ifwi and current ifwi if data is the same
            if previous_ifwi_payload["fw_components"] == current_ifwi_payload["fw_components"]:
                print("Identical")
                previous_ifwi_payload["fw_components"] = eval(previous_ifwi_payload["fw_components"])
                current_ifwi_payload["fw_components"] = previous_ifwi_payload["fw_components"]
            else:
                previous_ifwi_payload["fw_components"] = eval(previous_ifwi_payload["fw_components"])
                current_ifwi_payload["fw_components"] = eval(current_ifwi_payload["fw_components"])

            print(json.dumps(previous_ifwi_payload,indent=4))
            print(json.dumps(current_ifwi_payload,indent=4))

            # Get all similar tests based on same driver and same ifwi (biosbuildnum)
            previous_uuid_similar = {}
            current_uuid_similar = {}

            for row in self.bkc_regression_test_data:
                row_data = self.bkc_regression_test_data[row]
                if row_data["driver"] == previous_test_info["driver"] and row_data["vbios_uuid"] == previous_test_info["vbios_uuid"]:
                    previous_uuid_similar[row] = row_data
                elif row_data["driver"] == current_test_info["driver"] and row_data["vbios_uuid"] == current_test_info["vbios_uuid"]:
                    current_uuid_similar[row] = row_data
            
            print(f"Found {len(previous_uuid_similar)} tests similar to previous uuid")
            print(f"Found {len(current_uuid_similar)} tests similar to current uuid")
            
            
            # Remap computer config information to have uuid as key, for faster access
            self.bkc_regression_configuration_data_remapped = {}
            
            for row in self.bkc_regression_configuration_data:
                row_data = self.bkc_regression_configuration_data[row]
                self.bkc_regression_configuration_data_remapped[row_data["uuid"]] = row_data
            
            # Remap acpi matric information to have uuid as key, for faster access
            self.bkc_regression_acpi_metrics_remapped = {}

            for row in self.bkc_regression_acpi_metrics:
                row_data = self.bkc_regression_acpi_metrics[row]
                self.bkc_regression_acpi_metrics_remapped[row_data["uuid"]] = row_data
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

            # Get all unique computers and vbios bootup time
            previous_computers = self.get_computer_info(previous_uuid_similar)
            current_computers = self.get_computer_info(current_uuid_similar)

            print(json.dumps(previous_computers,indent=4))
            print(json.dumps(current_computers,indent=4))
            ####################################################
            report_output["current_computers"] = {
                "data":current_computers
            }

            # Get IFWI comparison table
            ####################################################
            ifwi_comparison = self.ifwi_component_comparator(previous_ifwi_payload,current_ifwi_payload)
            report_output["ifwi_comparison"] = {
                "data":ifwi_comparison
            }

            print(json.dumps(ifwi_comparison, indent=4))
            
            # Add stack information
            previous_driver = previous_test_info["driver"]
            current_driver = current_test_info["driver"]

            current_ifwi = current_ifwi_payload["ifwi_name"]
            previous_ifwi = previous_ifwi_payload["ifwi_name"]

            current_pptable = ""
            previous_pptable = ""
            try:
                current_pptable = current_ifwi_payload["pptable_id"] + "-" + current_ifwi_payload["pptable_rev"]
                previous_pptable = previous_ifwi_payload["pptable_id"] + "-" + previous_ifwi_payload["pptable_rev"]
            except:
                pass

            current_pmfw = current_driver_info["PMFW"]
            previous_pmfw = previous_driver_info["PMFW"]

            current_ifwi_nickname = self.get_nickname(current_ifwi)
            previous_ifwi_nickname = self.get_nickname(previous_ifwi)

            stack_info = {
                "previous_driver":previous_driver,
                "current_driver":current_driver,
                "current_ifwi":current_ifwi,
                "previous_ifwi":previous_ifwi,
                "current_pmfw":current_pmfw,
                "previous_pmfw":previous_pmfw,
                "previous_ifwi_nickname":previous_ifwi_nickname,
                "current_ifwi_nickname":current_ifwi_nickname,
                "current_pptable":current_pptable,
                "previous_pptable":previous_pptable
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
            order = ["ifwi","install","acpi_cb","acpi_wb","acpi_s3","acpi_s4","acpi","link","pcie","smu","acpi","decode","usb","3dwl","amf","_dpm","pnp","furmark","timespy","heaven","wildlife","portroyal"]
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
        list_of_acpi_cb_acpi_wb = []

        # Remap acpi metrics table for mor convenient key/value


        for row in uuid_dict:
            try:
                row_data = uuid_dict[row]
                config_data = self.bkc_regression_configuration_data_remapped[row_data['uuid']]
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

                # Add VBIOS POST TIME
                
                if "acpi_cb" in row_data["test_case"] or "acpi_wb" in row_data["test_case"]:
                    print(f"FOUND for {row_data['computer_name']}")
                    # Check in ACPI metrics for POST time information
                    
                    try:
                        acpi_metrics = self.bkc_regression_acpi_metrics_remapped[row_data['uuid']]
                        # Make sure sample size >=5
                        #print(acpi_metrics)
                        if float(acpi_metrics["sample_size"]) <= 5:
                            pass
                            #print("Sample size too small")
                        elif output[pc_name]['min_fw_post_time'] == "N/A":
                            output[pc_name]['min_fw_post_time'] = float(acpi_metrics['min_fw_post_time'])
                        elif acpi_metrics['min_fw_post_time'] < output[pc_name]['min_fw_post_time']:
                            output[pc_name]['min_fw_post_time'] = float(acpi_metrics['min_fw_post_time'])
                        
                    except Exception as e:
                        #print(f"No ACPI metrics FOUND for {row_data['computer_name']}::{row_data['test_case']}")
                        print(e)
                        pass
            except Exception as p:
                print(p)

        return output

    def ifwi_component_comparator(self, ifwi_info_previous, ifwi_info_current):
        # given two ifwi components, make a comparison table between the two
        # key = column name, value1 = current version, value2 = Yes (previous version)
        print("DEBUG")
        print(ifwi_info_previous)
        print(ifwi_info_current)
        print("DONE")
        comparator = {}
        for index, value in ifwi_info_current["fw_components"].items():
            fw_component = index.replace("_" + value["image_version"],"")
            comparator[fw_component] = {
                "current":value["image_version"],
                "previous":""
            }
            
            for index_i, value_i in ifwi_info_previous["fw_components"].items():
                fw_component_i = index_i.replace("_" + value_i["image_version"],"")
                print(f"{fw_component_i} / {fw_component}")
                if fw_component_i == fw_component:
                    print(f'{value_i["image_version"]} / {value["image_version"]}')
                    if value_i["image_version"] != value["image_version"]:
                        comparator[fw_component]["previous"] = f"Yes ({value_i['image_version']})"
                    print("MATCH! \n")
        print("WAITING")
        # Lastly, add PPTable info

        current_pptable = f"{ifwi_info_current['pptable_id']}-{ifwi_info_current['pptable_rev']}"
        previous_pptable = f"{ifwi_info_previous['pptable_id']}-{ifwi_info_previous['pptable_rev']}"
        comparator["PPTable"] = {
            "current":current_pptable,
            "previous":""
        }
        if current_pptable != previous_pptable:
            comparator["PPTable"]["previous"] = f"Yes ({previous_pptable})"

        return comparator
                
    def get_driver_components(self, dict_input):
        # Get current computer config information.  Will use most frequently non-zeroed values
        payload = {
            "RLC_G":"",
            "PMFW":"",
            "IMU":"",
            "PSP_TOS":"",
        }
        print("KKK")
        rlc_g = {}
        pmfw = {}
        imu = {}
        psp_tos = {}
        for test in dict_input:
            try:
                test_data = self.bkc_regression_configuration_data_remapped[dict_input[test]['uuid']]
                if test_data["rlc_g"] not in rlc_g: rlc_g[test_data["rlc_g"]] = 1
                else: rlc_g[test_data["rlc_g"]] += 1

                if test_data["pmfw"] not in pmfw: pmfw[test_data["pmfw"]] = 1
                else: pmfw[test_data["pmfw"]] += 1

                if test_data["imu"] not in imu: imu[test_data["imu"]] = 1
                else: imu[test_data["imu"]] += 1

                if test_data["psp_tos"] not in psp_tos: psp_tos[test_data["psp_tos"]] = 1
                else: psp_tos[test_data["psp_tos"]] += 1
            except:
                print(f"Error reading {test}")

        payload = {
            "RLC_G":self.get_most_common_key(rlc_g),
            "PMFW":self.get_most_common_key(pmfw),
            "IMU":self.get_most_common_key(imu),
            "PSP_TOS":self.get_most_common_key(psp_tos),
        }
        print(payload)    
        return payload

if __name__ == "__main__":
    
    reportmaker = report_maker()
    reportmaker.generate_report("c87533c8-22d5-4ba6-99e6-d0279dc5410d","3d1dc9ea-5c60-4b29-b0f2-fb1a486cd7e1")



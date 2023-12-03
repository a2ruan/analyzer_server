from dataclasses import dataclass

@dataclass
class MetaVariables:
    # MetaClass for storing shared global variables

    # Test Case Map is a dictionary used to map a TC::testcase_module or test_case name to a specific analyzer file
    # Test Cases are looked up from top to bottom, therefore add keys with specific test case modules on the top, and backup strings at the bottom
    test_case_map = {
    }

    # These descriptions will show up on report as a tooltip if the unit test name matches the key below
    result_descriptions = {
        "status":"The overall result of the test",
        "unexpected_reboot":"Checks if the SUT rebooted during the test or not",
        "warning":"Indicates if there is a non-critical unit test that failed i.e USB check, PM logs missing",
        "sleep_duration_warning":"Checks if sleep time is out of range",
        "pcie_status_mismatch":"Checks if PCIe or DPM status encountered mismatch during test",
        "missing_pm_logs":"Checks if pm logs are missing in log file location",
        "usb_check_failure":"Checks if USB enumeration failure is found in failure log",
        "scores_failed_to_read":"There is a missing scores failure text found in failure log",
        "program_setup_fail":"There was a setup failure detected in failure log, indicating that the test could not have run",
        "program_teardown_fail":"There was a teardown failure detected in failure log, indicating that the test could not have finished",
        "quark_fail":"Check if there are any quark failure indicators i.e gfxoff fail, L0 fail, or if there are quark setup issues",
        "id":"This is the row number of the test, stored into the program database",
        "test_log":"Network location of the test logs generated during program runtime",
        "uuid":"This is a unique hash representing the test case.  Each uuid corresponds to a row in the program database",
        "TP::testcase_module":"This is the test case module found in the json file. Fuzzy means that the analyzer could not be found, therefore the server will select the best match",
        "analyzer":"This is the script used to analyze logs in the test_log folder.  The analyzer file is stored on the analyzer server, and is synced to Github.",
        "program":"The github commit id of the base program version used for testing",
    }
from analyzer import MetaAnalyzer

class Analyzer(MetaAnalyzer):
    def __init__(self):
        super().__init__()

    def run(self):
        # The purpose of this function is to analyze all logs within this folder and subfolders
        results = {}
        results["status"] = "pass"
        results["warning"] = False

        print("Reboot Check")
        if self.check_for_unexpected_reboot(self.folder_path):
            results['unexpected_reboot'] = True
            results["status"] = "fail"
        else:
            results['unexpected_reboot'] = False

        print("Check if sleep time out of limit")
        if self.check_sleep_duration_out_of_limit(self.folder_path):
            results['sleep_duration_warning'] = True
            results["warning"] = True
        else:
            results['sleep_duration_warning'] = False

        print("Check if USB check is failed")
        if self.check_usb_failure(self.folder_path):
            results['usb_check_failure'] = True
            results["warning"] = True
        else:
            results['usb_check_failure'] = False

        print("Check if PCIE status is wrong")
        if self.check_pcie_status(self.folder_path):
            results['pcie_status_mismatch'] = True
            results["status"] = "fail"
        else:
            results['pcie_status_mismatch'] = False

        print("Check if sleep is enabled")
        if self.check_sleep_enabled(self.folder_path):
            results['s3_not_enabled'] = True
            results["status"] = "fail"

        print("Check Quark failures")
        if self.check_quark_failure(self.folder_path):
            results['quark_fail'] = True
            results["status"] = "fail"
        else:
            results['quark_fail_detected'] = False

        if self.check_driver_loaded(self.folder_path):
            results['driver_fail'] = True
            results["status"] = "fail"
        else:
            results['driver_fail'] = False

        if self.check_nak_fail(self.folder_path):
            results['naks_fail'] = True
            results["status"] = "fail"
        else:
            results['naks_fail'] = False

        if self.check_device_lost(self.folder_path):
            results['device_lost'] = True
            results["status"] = "fail"
        else:
            results['naks_fail'] = False

        print(f"Lines parsed = {self.lines_parsed}")
        results['lines_parsed'] = self.lines_parsed

        return results
    
    # Analyzer Specific Functions
    def check_device_lost(self, path):
        error_log = self.get_file_path(["program_program_errors.log"], path)
        if error_log is not None:
            if self.fuzzy_lookup_string("TEST Fail AT due to device lost", error_log, 80) > 80:
                return True
        return False

    def check_driver_loaded(self, path):
        error_log = self.get_file_path(["program_program_errors.log"], path)
        if error_log is not None:
            if self.fuzzy_lookup_string("driver check fail", error_log, 90) > 90: # VCN script only
                return True
        return False
    
    def check_nak_fail(self, path):
        error_log = self.get_file_path(["program_program_errors.log"], path)
        if error_log is not None:
            if self.fuzzy_lookup_string("PCIE NAKs alert", error_log, 90) > 90: # VCN script only
                return True
        return False
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

        print("Check if PM Logs Exists")
        if self.check_if_pm_logs_exist(self.folder_path):
            results['missing_pm_logs'] = True
            results["warning"] = True
        else:
            results['missing_pm_logs'] = False

        print("Check if PCIE status is wrong")
        if self.check_pcie_status(self.folder_path):
            results['pcie_status_mismatch'] = True
            results["status"] = "fail"
        else:
            results['pcie_status_mismatch'] = False

        if self.check_gen_speed_fail(self.folder_path):
            results['gen_speed_fail'] = True
            results["status"] = "fail"
        else:
            results['gen_speed_fail'] = False
        
        if self.check_width_fail(self.folder_path):
            results['width_fail'] = True
            results["status"] = "fail"
        else:
            results['width_fail'] = False

        print("Check if setup failed")
        if self.check_setup_failure(self.folder_path):
            results['program_setup_fail'] = True
            results["status"] = "fail"

        print("SMU Message Fail")
        if self.smu_message_fail(self.folder_path):
            results['smu_message_fail'] = True
            results["status"] = "fail"
        else:
            results['smu_message_fail'] = False

        print("Check if teardown failed")
        if self.check_teardown_failure(self.folder_path):
            results['program_teardown_fail'] = True
            results["status"] = "fail"

        print(f"Lines parsed = {self.lines_parsed}")
        results['lines_parsed'] = self.lines_parsed

        return results
    
    def smu_message_fail(self, path):
        error_log = self.get_file_path(["program_program_errors.log"], path)
        if error_log is not None:
            if self.fuzzy_lookup_string("Setting dpm_state = cause exception: deviceMP1FW.send_message - response not OK", error_log, 80) > 80:
                return True
        return False
    
    def check_gen_speed_fail(self, path):
        error_log = self.get_file_path(["program_program_errors.log"], path)
        if error_log is not None:
            if self.fuzzy_lookup_string("Failed to achieve GEN", error_log, 90) > 90: # VCN script only
                return True
        return False
    
    def check_width_fail(self, path):
        error_log = self.get_file_path(["program_program_errors.log"], path)
        if error_log is not None:
            if self.fuzzy_lookup_string("Failed to achieve X", error_log, 95) > 95: # VCN script only
                return True
        return False
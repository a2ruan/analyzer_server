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

        print("Check if scores failed to read")
        if self.check_score_failed_to_read(self.folder_path):
            results['scores_failed_to_read'] = True
            results["warning"] = True

        print("Check if setup failed")
        if self.check_setup_failure(self.folder_path):
            results['program_setup_fail'] = True
            results["status"] = "fail"

        print("Check if teardown failed")
        if self.check_teardown_failure(self.folder_path):
            results['program_teardown_fail'] = True
            results["status"] = "fail"

        if self.check_smu_message_fail(self.folder_path):
            results['smu_message_fail'] = True
            results["status"] = "fail"
        else:
            results['smu_message_fail'] = False

        if self.check_uvd_fail(self.folder_path):
            results['uvd_fail'] = True
            results["status"] = "fail"
        else:
            results['uvd_fail'] = False

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

        print(f"Lines parsed = {self.lines_parsed}")
        results['lines_parsed'] = self.lines_parsed
        results['pm_log_stats'] = self.pm_log_analysis(self.folder_path)
        return results
    
    # Specific Unit Test Functions

    def check_smu_message_fail(self, path):
        error_log = self.get_file_path(["program_program_errors.log"], path)
        if error_log is not None:
            if self.fuzzy_lookup_string("'smu_message_sent': 'fail'", error_log, 90) > 90: # VCN script only
                return True
        return False
    
    def check_uvd_fail(self, path):
        error_log = self.get_file_path(["program_program_errors.log"], path)
        if error_log is not None:
            if self.fuzzy_lookup_string("'uvd_result': 'fail'", error_log, 90) > 90: # VCN script only
                return True
        return False
    
    def check_driver_loaded(self, path):
        error_log = self.get_file_path(["program_program_errors.log"], path)
        if error_log is not None:
            if self.fuzzy_lookup_string("'dGPU_driver_loaded': 'fail'", error_log, 90) > 90: # VCN script only
                return True
        return False
    
    def check_nak_fail(self, path):
        error_log = self.get_file_path(["program_program_errors.log"], path)
        if error_log is not None:
            if self.fuzzy_lookup_string("'nak_result': 'fail'", error_log, 90) > 90: # VCN script only
                return True
        return False
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
            results["status"] = "fail" # PM Log is mandatory
        else:
            results['missing_pm_logs'] = False

        if self.check_dpm_ds_fail(self.folder_path):
            results['dpm_ds_fail'] = True
            results["status"] = "fail"
        else:
            results['dpm_ds_fail'] = False

        if self.check_gpu_support(self.folder_path):
            results['gpu_unsupported'] = True
            results["status"] = "fail"

        print("Check if setup failed")
        if self.check_setup_failure(self.folder_path):
            results['program_setup_fail'] = True
            results["status"] = "fail"

        print("Check if teardown failed")
        if self.check_teardown_failure(self.folder_path):
            results['program_teardown_fail'] = True
            results["status"] = "fail"

        print(f"Lines parsed = {self.lines_parsed}")
        results['lines_parsed'] = self.lines_parsed

        return results

    def check_dpm_ds_fail(self, path):
        error_log = self.get_file_path(["program_program_errors.log"], path)
        if error_log is not None:
            if self.fuzzy_lookup_string("DPM/DS Failure", error_log, 90) > 90: 
                return True
            elif self.fuzzy_lookup_string("Unable to find GPU", error_log, 90) > 90:# Clock is missing
                return True       
        return False
    
    def check_gpu_support(self, path):
        error_log = self.get_file_path(["program_program_errors.log"], path)
        if error_log is not None:
            if self.fuzzy_lookup_string("NAVI2X and NAVI1X not supported", error_log, 90) > 90: 
                return True  
        return False
    
    

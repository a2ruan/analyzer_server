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

        if self.check_ren(self.folder_path):
            results['ren_fail'] = True
            results["status"] = "fail"
        else:
            results['ren_fail'] = False

        if self.check_quark(self.folder_path):
            results['quark_fail'] = True
            results["status"] = "fail"
        else:
            results['quark_fail'] = False

        print("Check if setup failed")
        if self.check_setup_failure(self.folder_path):
            results['program_setup_fail'] = True
            results["status"] = "fail"

        print("Check if teardown failed")
        if self.check_teardown_failure(self.folder_path):
            results['program_teardown_fail'] = True
            results["status"] = "fail"

        return results

    def check_ren(self, path):
        error_log = self.get_file_path(["program_program_errors.log"], path)
        if error_log is not None:
            if self.fuzzy_lookup_string("Failed to disable GFX driver", error_log, 90) > 90: # VCN script only
                return True
            elif self.fuzzy_lookup_string("Failed to disable GFX driver", error_log, 90) > 90: # VCN script only
                return True
        return False
    
    def check_quark(self, path):
        error_log = self.get_file_path(["FAIL.log"], path)
        if error_log is not None:
            if self.fuzzy_lookup_string("Quark test failed", error_log, 90) > 90: # VCN script only
                return True
        return False
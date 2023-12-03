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

        print("Check if setup failed")
        if self.check_setup_failure(self.folder_path):
            results['program_setup_fail'] = True
            results["status"] = "fail"

        print("Check if teardown failed")
        if self.check_teardown_failure(self.folder_path):
            results['program_teardown_fail'] = True
            results["status"] = "fail"

        print("Check Quark failures")
        if self.check_quark_failure(self.folder_path):
            results['quark_fail'] = True
            results["status"] = "fail"
        else:
            results['quark_fail_detected'] = False

        print("Check UVD errors")
        if self.check_uvd_errors(self.folder_path):
            results['uvd_errors'] = True
            results["status"] = "fail" # VCN script will fail test if UVD errors detected
        else:
            results['uvd_errors'] = False

        print(f"Lines parsed = {self.lines_parsed}")
        results['lines_parsed'] = self.lines_parsed

        return results


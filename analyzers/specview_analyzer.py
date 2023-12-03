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

        print(f"Lines parsed = {self.lines_parsed}")
        results['lines_parsed'] = self.lines_parsed

        return results

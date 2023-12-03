# Interface for all analyzers
import os
# from fuzzywuzzy import fuzz
from rapidfuzz import fuzz  # This one is literally 100x faster
import datetime
import time
# Custom library to read file backwards, significant speed improvement in some cases
from file_read_backwards import FileReadBackwards
import pandas as pd
import statistics
ENABLE_OPTIMIZATIONS = False

class MetaAnalyzer:
    def __init__(self):
        self.lines_parsed = 0
        pass



    def get_file_path(self, filters=None, folder_path=None, hard_filter_mode=None):
        # Returns the full file path.  This algorithm searches inside folder_path for files with filters in file name
        for path, subdirs, files in os.walk(folder_path):
            for name in files:
                if hard_filter_mode == None:
                    for filter in filters:
                        if filter in name:
                            pass
                        else:
                            continue
                        print(os.path.join(path, name))
                        return os.path.join(path, name)
                else:
                    pass_all_filters = True
                    for filter in filters:
                        if filter in name:
                            pass
                        else:
                            pass_all_filters = False
                    if pass_all_filters == True:
                        print(os.path.join(path, name))
                        return os.path.join(path, name)
        return None
    
    from functools import lru_cache

    @lru_cache(maxsize=None)
    def fuzzy_lookup_string(self, search_str=None, file_path=None, target_match=99, override_time_delta=False):
        # For each line in file_path file, returns highest probability (as a ratio) of text occurance
        # Target match will result in function returning a ratio early, due to encountering an early match
        print("#"*100)
        max_ratio = 0
        best_line = ""

        counter = 0
        start_time = time.time()
        if 'start_time' not in self.test_details:
            return 0  # Error
        verbose_print = False
        cumulative_time = 0

        # Read length of text file, and read lines in reverse for ultra large files
        print("LENGTH READING_TIME")
        read_lines_backwards = False
        line_timestamp_miss_count = 0
        start_length_reading = time.time()
        num_lines = sum(1 for line in open(file_path))
        self.lines_parsed += num_lines
        end_length_reading = time.time()-start_length_reading
        print(end_length_reading)

        if num_lines > 10000 and ENABLE_OPTIMIZATIONS:
            fileobj = FileReadBackwards(file_path)
            print("File lines greater than limit.  Employing reverse reading method.")
            read_lines_backwards = True
        else:
            fileobj = open(file_path)

        with fileobj as f:
            for line in f:
                counter += 1

                if verbose_print:
                    print("#"*100)
                if verbose_print:
                    print(line)

                # Skip lines if greater that start timestamp + buffer time
                # start_time = self.test
                if verbose_print:
                    print(
                        f"Detected start time = {self.test_details['start_time']}")
                # print(type(self.test_details['start_time']))
                tracker_start = time.time()
                actual_str = ""
                try:
                    if len(line.split(" - ", 1)) > 1:
                        # print("multiple lines found!")
                        tokenized_str = line.split(" - ", 1)
                        timestamp_str = tokenized_str[0]
                        actual_str = tokenized_str[1]
                        element = datetime.datetime.strptime(
                            timestamp_str, "%Y-%m-%d %H:%M:%S,%f")
                        tuple = element.timetuple()
                        # print(tuple)
                        timestamp = time.mktime(tuple)
                        if verbose_print:
                            print(timestamp_str)

                        flipflop = 1
                        if element > self.test_details['start_time']:
                            delta = element - self.test_details['start_time']
                        else:
                            delta = self.test_details['start_time'] - element
                            flipflop = -1

                        if verbose_print:
                            print("delta")
                        if verbose_print:
                            print(override_time_delta)
                        if verbose_print:
                            print(delta.seconds*flipflop)
                        if delta.seconds * flipflop > 0 or override_time_delta:
                            if verbose_print:
                                print("Time within bounds!")
                            pass
                        else:
                            if verbose_print:
                                print("Time not within bounds! Skipping")
                            # For reversed line cases, if line miss count exceeds 10 consecutive counts, then don't parse the rest of the log
                            # There are some time savings for ultra large files
                            if read_lines_backwards:
                                line_timestamp_miss_count += 1
                            if line_timestamp_miss_count > 10:
                                return max_ratio
                            continue
                except Exception as e:
                    print(f"EXCEPTION OCCURRED {e}")
                cumulative_time += time.time()-tracker_start
                if verbose_print:
                    print("CONTINUING TO RATIOCHECKER!")
                # If timestamp detected, remove timestamp for improved string searching and runtime
                
                # Edge case: filter out bad 3d wl error logs
                if search_str == "unexpected reboot":
                    unqualified_ratio = fuzz.partial_ratio("'unexpected_reboot': 'pass'".strip(), actual_str.strip())
                    if unqualified_ratio > 99:
                        continue

                if actual_str != "":
                    str_match_ratio = fuzz.partial_ratio(
                        search_str.strip(), actual_str.strip())
                else:
                    str_match_ratio = fuzz.partial_ratio(
                        search_str.strip(), line.strip())

                if str_match_ratio > max_ratio:
                    best_line = line
                    max_ratio = str_match_ratio

                if str_match_ratio > target_match:  # Early abort to save space
                    print("Early return")
                    print(f"BEST LINE = {best_line}")
                    print(f"BEST RATIO = {max_ratio}")

                    if counter > 0:
                        print(
                            f"TIME TAKEN PER LINE (ms) for {str(counter)} lines")
                        print((time.time()-start_time)/counter*1000)
                        print(
                            f"Cumulative Time = {str(time.time() - start_time)}")
                        print(
                            f"Cumulative Time in tracker = {str(cumulative_time)}")

                    return max_ratio

        print(f"BEST LINE = {best_line}")
        print(f"BEST RATIO = {max_ratio}")

        if counter > 0:
            print(f"TIME TAKEN PER LINE (ms) for {str(counter)} lines")
            print((time.time()-start_time)/counter*1000)
            print(f"Cumulative Time = {str(time.time() - start_time)}")
            print(f"Cumulative Time in tracker = {str(cumulative_time)}")
        return max_ratio

    def check_setup_failure(self, path):
        print("Checking for setup failure")
        error_log = self.get_file_path(["program_program_errors.log"], path)
        print(error_log)
        if error_log is not None:
            # program setup should never appear in failure log, therefore entire log is parsed, without time filtering
            if self.fuzzy_lookup_string("failed during setup", error_log, 70, False) > 70:
                return True
            else:
                return False
        return False

    def check_teardown_failure(self, path):
        print("Checking for teardown failure")
        error_log = self.get_file_path(["program_program_errors.log"], path)
        print(error_log)
        if error_log is not None:
            # program teardown fail should never appear in failure log, therefore entire log is parsed, without time filtering
            if self.fuzzy_lookup_string("failed during teardown", error_log, 70, False) > 70:
                return True
            else:
                return False
        return False
    
    def check_quark_failure(self, path):
        print("Checking for rap failures")
        error_log = self.get_file_path(["program_program_errors.log"], path)
        print(error_log)
        if error_log is not None:
            if self.fuzzy_lookup_string("L0 test FAILED", error_log, 90) > 90: # reb script
                return True
            elif self.fuzzy_lookup_string("Quark test failed", error_log, 90) > 90: # Decode script
                return True
            elif self.fuzzy_lookup_string("gfxoff test FAILED", error_log, 90) > 90: # reb script
                return True
            elif self.fuzzy_lookup_string("gfxoff test inconclusive", error_log, 90) > 90: # reb script
                return True
            elif self.fuzzy_lookup_string("L0 test inconclusive", error_log, 90) > 90: # reb script
                return True
            elif self.fuzzy_lookup_string("L0 test inconclusive", error_log, 90) > 90: # reb script
                return True
            elif self.fuzzy_lookup_string("Could not find Quark.exe file on system", error_log, 90) > 90: # reb script
                return True
            elif self.fuzzy_lookup_string("Quark test file missing", error_log, 90) > 90: # Decode script
                return True
            else:
                return False
        return False

    def check_pcie_status(self, path):
        # Check if pcie dpm failed
        print("Checking for pcie dpm failure")
        error_log = self.get_file_path(["program_program_errors.log"], path)
        print(error_log)
        if error_log is not None:
            if self.fuzzy_lookup_string("Failed to achieve GEN", error_log, 80) > 80:
                return True
            elif self.fuzzy_lookup_string("check_pcie_dpm pcie status is wrong for DPM", error_log, 80) > 80:
                return True
            else:
                return False
        return False

    def check_sleep_enabled(self, path):
        # Check if s3 is enabled
        print("Checking for s3 enablement")
        error_log = self.get_file_path(["program_program_errors.log"], path)
        print(error_log)
        if error_log is not None:
            if self.fuzzy_lookup_string("s3 is not enabled", error_log, 80) > 80:
                return True
            else:
                return False
        return False

    def check_usb_failure(self, path):
        # Check if usb failed
        print("Checking for usb loss")
        error_log = self.get_file_path(["program_program_errors.log"], path)
        print(error_log)
        if error_log is not None:
            if self.fuzzy_lookup_string("Failed USB test", error_log, 80) > 80:
                return True
            elif self.fuzzy_lookup_string("FAIL USB Speed", error_log, 80) > 80:
                return True
            elif self.fuzzy_lookup_string("FAIL CRC CHECK", error_log, 80) > 80:
                return True
            elif self.fuzzy_lookup_string("Failed USB test", error_log, 80) > 80:
                return True
            elif self.fuzzy_lookup_string("Failed to initialize USB test", error_log, 80) > 80:
                return True
            else:
                return False
        return False

    def check_score_failed_to_read(self, path):
        print("Checking if score failed to read")
        error_log = self.get_file_path(["program_program_errors.log"], path)
        info_log = self.get_file_path(["program_program_info_only.log"], path)
        print(error_log)
        if error_log is not None:
            if self.fuzzy_lookup_string("Error found trying to parse score", error_log, 80) > 80:
                return True
        if error_log is not None:
            if self.fuzzy_lookup_string("Avg score is 0.0", error_log, 80) > 80:
                return True
        return False

    def check_sleep_duration_out_of_limit(self, path):
        # Check if sleep duration is too high or low
        print("Checking for sleep duration")
        error_log = self.get_file_path(["program_program_errors.log"], path)
        print(error_log)
        if error_log is not None:
            if self.fuzzy_lookup_string("Sleep time is outside of allocated time range fail", error_log, 80) > 80:
                return True
            else:
                return False
        return False
    
    def check_uvd_errors(self, path):
        error_log = self.get_file_path(["program_program_errors.log"], path)
        if error_log is not None:
            if self.fuzzy_lookup_string("UVD ERRORS DETECTED", error_log, 90) > 90: # VCN script only
                return True
            elif self.fuzzy_lookup_string("UVD logging error", error_log, 90) > 90: # VCN script only
                return True
        return False

    def check_if_pm_logs_exist(self, path):
        # Check if pm logs exists
        print("checking if PM Logs exists")
        pm_log = self.get_file_path(["csv", "pm"], path)
        if pm_log in [None]:
            return True
        return False

    def check_for_unexpected_reboot(self, path):
        # Check in fail log for unexpected reboot
        print(f"PATH={path}")
        fail_log = self.get_file_path(["FAIL.log"], path)

        if fail_log is not None:
            if self.fuzzy_lookup_string("unexpected reboot", fail_log, 98) > 98:
                return True

        fail_log = self.get_file_path(["program_program_errors.log"], path)
        if fail_log is not None:
            if self.fuzzy_lookup_string("unexpected reboot", fail_log, 90) > 90:
                return True
            elif self.fuzzy_lookup_string("Reboot detected", fail_log, 90) > 90:
                return True
            elif self.fuzzy_lookup_string("An unexpected system reboot has occured", fail_log, 90) > 90:
                return True
            
        return False

    def pm_log_analysis(self, path):
        # Searches for the largest pm log in folder or subfolders, and returns key metrics
        pm_log_path = self.get_file_path(["csv", "pm"], path, hard_filter_mode=1)
        if pm_log_path != None:
            print(pm_log_path)

            try:
                # Read the Excel file into a pandas dataframe
                df = pd.read_csv(pm_log_path, nrows=500)

                # Print the dataframe
                data = df.to_dict()
                #print(df.to_dict())

                stats = {}

                for index, row in enumerate(data):
                    #print(row)
                    try:
                        values = data[row].values()
                        # Calculate the mean
                        try:
                            mean = round(statistics.mean(values), 2)
                        except statistics.StatisticsError:
                            mean = "Error"

                        # Calculate the median
                        try:
                            median = round(statistics.median(values), 2)
                        except statistics.StatisticsError:
                            median = "Error"
                    
                        # Calculate the maximum value
                        try:
                            max_val = round(max(values), 2)
                        except ValueError:
                            max_val = "Error"

                        # Calculate the minimum value
                        try:
                            min_val = round(min(values), 2)
                        except ValueError:
                            min_val = "Error"
                    
                        # Calculate the mode
                        try:
                            mode = round(statistics.mode(values), 2)
                        except statistics.StatisticsError:
                            mode = "Error"
                    
                        # Calculate the standard deviation
                        try:
                            stdev = round(statistics.stdev(values), 2)
                        except statistics.StatisticsError:
                            stdev = "Error"

                        # Calculate the variance
                        try:
                            variance = round(statistics.variance(values), 2)
                        except statistics.StatisticsError:
                            variance = "Error"

                        temp_payload = {
                            "mean":mean,
                            "max":max_val,
                            "min":min_val,
                            "mode":mode,
                            "variance":variance,
                            "stdev":stdev,

                        }
                        miss_counter = 0
                        total_counter = 0
                        for item in temp_payload:
                            total_counter += 1
                            if temp_payload[item] in ["Error",0]:
                                miss_counter += 1

                        if miss_counter == total_counter:
                            pass
                        else:
                            stats[row] = temp_payload

                    except:
                        pass
                    
                import json
                #print(json.dumps(stats,indent=4))
                return stats
            except:
                return {}
        

        return {}

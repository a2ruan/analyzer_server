import pandas as pd
import statistics

class excel_parser:
    def __init__(self):
        pass

    def get_pm_log_path(folders=None):
        pass
    
    def get_statistics(excel_file='pm_log_3DWL_time_amf.csv', rows=1000):
        try:
            # Read the Excel file into a pandas dataframe
            df = pd.read_csv(excel_file, nrows=rows)

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

                    stats[row] = {
                        "mean":mean,
                        "max":max_val,
                        "min":min_val,
                        "mode":mode,
                        "variance":variance,
                        "stdev":stdev,

                    }
                except:
                    pass
                
            import json
            print(json.dumps(stats,indent=4))
        except:
            return {}

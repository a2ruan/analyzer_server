import requests
import time

print("Hello World Test")
start_time = time.time()
for i in range(1000):
    try:

        output = requests.get("http://localhost.program.com:5600")
        time.sleep(0.25)
        print(i)
        print(output.text)
        #print(i)
    except:
        print(f"Dropped packet at {i}")

print(time.time() - start_time)

#print("File Tree Test")
#output = requests.get("http://localhost.program.com:5600/get_files", headers={'path':r'\\dir\rtg_test\test_data\NAVI31\D70201\reb\0a2f4ee5-64d7-4dab-9a98-8edb59836922\reb_s3_3d_uvd'})
#print(output.text)


#print("SMU Test using PATH for tar.gz")
#output = requests.get("http://localhost.program.com:5600/api/submit_job", headers={'path':r'\\dir\rtg_test\test_data\NAVI31 FGL\D70711\pcie\5de0e8b5-6c08-47e7-8ac5-ece3bbdb2505\forced_smu_stress\Results_2023-02-25-07-04-17-478506-forced_smu_stress.tar.gz'})
#print(output.text)

#print("USB Test using PATH for zip")
#output = requests.get("http://localhost.program.com:5600/api/submit_job", headers={'uuid':'8b997e46-f3c5-44cf-b501-7564c7b32664'})
#print(output.text)

#print("USB Test using PATH for zip")
#output = requests.get("http://localhost.program.com:5600/api/submit_job", headers={'uuid':'6786e90c-d189-4df1-aba5-66151044c51c'})
#print(output.text)

#print("ren Test using PATH for zip")
#output = requests.get("http://localhost.program.com:5600/api/submit_job", headers={'uuid':'ed56147f-f695-4b34-970e-e4b8de70d8a2'})
#print(output.text)

#print("reb S4 Test using PATH for zip, with PM Logs, and Sleep warning")
#output = requests.get("http://localhost.program.com:5600/api/submit_job", headers={'uuid':'46ee7128-acf6-4725-b23c-2b1e6f5d5df7'})
#print(output.text)

#print("reb S4 Test using PATH for zip, with no PM Logs, and USB warning")
#output = requests.get("http://localhost.program.com:5600/api/submit_job", headers={'uuid':'93c41db0-f9cf-498c-8b17-9068f94b2f5e'})
#print(output.text)

#print("reb WB Test using PATH for zip, no PM Logs")
#output = requests.get("http://localhost.program.com:5600/api/submit_job", headers={'uuid':'d2c3ecdc-8cd0-4386-a511-d46db6944a33'})
#print(output.text)

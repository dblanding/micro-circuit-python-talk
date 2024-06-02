import datetime
import requests
import time

url = "http://192.168.1.62"
filename = "clock_data.txt"
count = 1

def get_data():
    response = requests.get(url)
    lines = response.text.split('\n')
    data = [line for line in lines
            if len(line) and line[0].isnumeric()]
    with open(filename, 'a') as f:
        f.write("-------\n")
        for line in data:
            f.write(line + '\n')

get_data()

while count:
    if not count % 5:
        print(f"{count}")

    if count == 50:
        count = 0
        start = time.time()
        print(f"Saving a batch")
        get_data()
        end = time.time()
        delta = end - start
        print(f"get_data() took {delta:.2f} seconds")

        
    count += 1
    time.sleep(60)

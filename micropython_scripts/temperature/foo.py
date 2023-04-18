with open('data.txt') as f:
    lines = f.readlines()
yesterdate = lines[0].split()[-1].strip()
lines = [line for line in lines if line[0].isdigit()]
lines.sort()
low = lines[0]
high = lines[-1]

print(yesterdate)
print('Low: ', low)
print('High: ', high)

string = 'VERSION "HIPBNYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYY/4/%%%/4/\'%**4YYY///"'
string1= 'hello 1234 helll'
import re 
match = re.findall('"(?:[^"]|.)*"|[^\s]+', string)
print(match)
import yaml  
s=yaml.safe_load(open('schema.yml'))  
paths=s.get('paths',{}) 

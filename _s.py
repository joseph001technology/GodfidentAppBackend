import yaml  
f=open('schema.yml','r',encoding='utf-8')  
s=yaml.safe_load(f.read())  
f.close()  
paths=list(s.get('paths',{}).keys()) 

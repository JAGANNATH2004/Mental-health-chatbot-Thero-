import google.generativeai as genai

# Replace with your actual API key
genai.configure(api_key="AIzaSyDQY83Wqdgw94yHpgSiRyKOykdV317jzHs")

import json  
from google.generativeai import list_models  

models = list(list_models())  
print(json.dumps([m.name for m in models], indent=2))  # Prints model names only
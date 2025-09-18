#!/usr/bin/env python3
"""
Script simple para probar GridMR con WordCount
"""

import base64
import json
import time
import urllib.request

# IP de tu master en AWS
MASTER = "http://35.153.249.132:8080"

def post_json(url, data):
    req = urllib.request.Request(
        url, 
        data=json.dumps(data).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode())

def get_text(url):
    with urllib.request.urlopen(url) as resp:
        return resp.read().decode()

def main():
    print("🚀 Prueba simple de WordCount")
    
    # Scripts de Map y Reduce
    map_script = """#!/usr/bin/env python3
import sys
for line in sys.stdin:
    for word in line.strip().split():
        print(f"{word.lower()}\\t1")
"""
    
    reduce_script = """#!/usr/bin/env python3
import sys
from collections import defaultdict

word_count = defaultdict(int)
for line in sys.stdin:
    word, count = line.strip().split("\\t")
    word_count[word] += int(count)

for word, count in sorted(word_count.items()):
    print(f"{word}\\t{count}")
"""
    
    # Datos de prueba
    input_text = """
    hello world hello
    world of distributed computing
    hello distributed world
    computing is fun
    distributed systems are powerful
    hello world
    """ * 100  # Repetir para tener más datos
    
    # Crear job
    job_id = f"wordcount-{int(time.time())}"
    job = {
        "job_id": job_id,
        "input_text": input_text,
        "split_size": 100,
        "reducers": 2,
        "format": "text",
        "map_script_b64": base64.b64encode(map_script.encode()).decode(),
        "reduce_script_b64": base64.b64encode(reduce_script.encode()).decode()
    }
    
    print(f"📤 Enviando job: {job_id}")
    result = post_json(f"{MASTER}/api/jobs", job)
    print(f"✅ Job enviado: {result}")
    
    # Monitorear
    print("⏳ Esperando resultado...")
    while True:
        status = json.loads(get_text(f"{MASTER}/api/jobs/status?job_id={job_id}"))
        print(f"   Estado: {status.get('state', 'UNKNOWN')}")
        
        if status.get("state") in ("SUCCEEDED", "FAILED"):
            break
        time.sleep(1)
    
    # Resultado
    if status.get("state") == "SUCCEEDED":
        result = get_text(f"{MASTER}/api/jobs/result?job_id={job_id}")
        print("\n📄 RESULTADO:")
        print("=" * 40)
        print(result)
        print("=" * 40)
    else:
        print(f"❌ Job falló: {status}")

if __name__ == "__main__":
    main()
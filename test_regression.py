#!/usr/bin/env python3
"""
Script para probar regresión lineal con GridMR
"""

import base64
import json
import time
import urllib.request
import random

# IP de tu master en AWS
MASTER = "http://54.87.145.230:8080"

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

def generate_linear_data(n_points=1000):
    """Generate linear data: y = 2x + 3 + noise"""
    data = []
    for _ in range(n_points):
        x = random.uniform(0, 10)
        y = 2 * x + 3 + random.gauss(0, 0.5)  # y = 2x + 3 + noise
        data.append(f"{x:.4f} {y:.4f}")
    return "\n".join(data)

def main():
    print("🚀 Prueba de Regresión Lineal")
    
    map_script = """#!/usr/bin/env python3
import sys

def mapper():
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            x_str, y_str = line.split()
            x, y = float(x_str), float(y_str)
            print(f"sum_x\\t{x}")
            print(f"sum_y\\t{y}")
            print(f"sum_xy\\t{x*y}")
            print(f"sum_x2\\t{x*x}")
            print("count\\t1")
        except ValueError:
            continue

if __name__ == "__main__":
    mapper()
"""
    
    reduce_script = """#!/usr/bin/env python3
import sys

def reducer():
    sum_x = 0.0
    sum_y = 0.0
    sum_xy = 0.0
    sum_x2 = 0.0
    n = 0

    for line in sys.stdin:
        key, val = line.strip().split("\\t")
        val = float(val)
        if key == "sum_x":
            sum_x += val
        elif key == "sum_y":
            sum_y += val
        elif key == "sum_xy":
            sum_xy += val
        elif key == "sum_x2":
            sum_x2 += val
        elif key == "count":
            n += int(val)

    if n > 0:
        denom = (n * sum_x2 - sum_x**2)
        if denom == 0:
            print("Cannot compute regression: division by zero.")
            return

        beta1 = (n * sum_xy - sum_x * sum_y) / denom
        beta0 = (sum_y - beta1 * sum_x) / n

        print(f"Data points: {n}")
        print(f"Intercept (β₀): {beta0:.4f}")
        print(f"Slope (β₁): {beta1:.4f}")
        print(f"Linear model: y ≈ {beta0:.4f} + {beta1:.4f} * x")
        print("Expected: y ≈ 3.0000 + 2.0000 * x")
    else:
        print("No data found.")

if __name__ == "__main__":
    reducer()
"""
    
    # Generar datos (y = 2x + 3 + noise)
    print("📊 Generando datos sintéticos (y = 2x + 3 + ruido)...")
    input_data = generate_linear_data(5000)
    
    job_id = f"regression-{int(time.time())}"
    job = {
        "job_id": job_id,
        "input_text": input_data,
        "split_size": 200,
        "reducers": 1,  # Solo 1 reducer para combinar todos los datos
        "format": "text",
        "map_script_b64": base64.b64encode(map_script.encode()).decode(),
        "reduce_script_b64": base64.b64encode(reduce_script.encode()).decode()
    }
    
    print(f"📤 Enviando job: {job_id}")
    result = post_json(f"{MASTER}/api/jobs", job)
    print(f"✅ Job enviado: {result}")
    
    print("⏳ Calculando regresión lineal...")
    while True:
        status = json.loads(get_text(f"{MASTER}/api/jobs/status?job_id={job_id}"))
        print(f"   Estado: {status.get('state', 'UNKNOWN')}")
        
        if status.get("state") in ("SUCCEEDED", "FAILED"):
            break
        time.sleep(2)
    
    if status.get("state") == "SUCCEEDED":
        result = get_text(f"{MASTER}/api/jobs/result?job_id={job_id}")
        print("\n📄 RESULTADO:")
        print("=" * 50)
        print(result)
        print("=" * 50)
        print("💡 El modelo debería ser cercano a: y ≈ 3.0000 + 2.0000 * x")
    else:
        print(f"❌ Job falló: {status}")

if __name__ == "__main__":
    main()
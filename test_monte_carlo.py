#!/usr/bin/env python3
"""
Script para probar GridMR distribuido desde PC local
Ejemplo: Estimación de Pi usando Monte Carlo
"""

import base64
import json
import sys
import time
import os
import urllib.request
import random

# Configuración del Master remoto
MASTER = "http://54.87.145.230:8080"  # IP de tu master en AWS

def b64_encode_file(filepath):
    """Codifica un archivo en base64"""
    with open(filepath, "rb") as f:
        return base64.b64encode(f.read()).decode("ascii")

def post_json(url, data):
    """Hace un POST con JSON"""
    print(f"📤 POST {url}")
    req = urllib.request.Request(
        url, 
        data=json.dumps(data).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read().decode())
    except Exception as e:
        print(f"❌ Error en POST: {e}")
        return None

def get_text(url):
    """Hace un GET y retorna texto"""
    try:
        with urllib.request.urlopen(url) as resp:
            return resp.read().decode()
    except Exception as e:
        print(f"❌ Error en GET: {e}")
        return None

def generate_monte_carlo_data(num_points=10000):
    """Genera datos aleatorios para Monte Carlo"""
    print(f"🎲 Generando {num_points} puntos aleatorios para Monte Carlo...")
    data = []
    for _ in range(num_points):
        x = random.uniform(-1, 1)
        y = random.uniform(-1, 1)
        data.append(f"{x:.6f} {y:.6f}")
    return "\n".join(data)

def test_connection():
    """Prueba la conexión con el master"""
    print("🔍 Probando conexión con el master...")
    try:
        response = get_text(f"{MASTER}/api/health")
        if response:
            print("✅ Conexión exitosa con el master")
            return True
    except:
        pass
    
    print("❌ No se puede conectar al master")
    print(f"   Verifica que {MASTER} esté corriendo")
    return False

def main():
    print("=" * 60)
    print("🚀 GridMR Monte Carlo Test - Cliente Local")
    print("=" * 60)
    
    # Verificar conexión
    if not test_connection():
        return
    
    # Preparar archivos
    print("\n📁 Preparando archivos de MapReduce...")
    
    map_script = """#!/usr/bin/env python3
import sys
import math

def mapper():
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            x_str, y_str = line.split()
            x, y = float(x_str), float(y_str)
            inside = 1 if x*x + y*y <= 1 else 0
            print(f"inside\\t{inside}")
            print("total\\t1")
        except ValueError:
            continue

if __name__ == "__main__":
    mapper()
"""
    
    reduce_script = """#!/usr/bin/env python3
import sys

def reducer():
    inside_count = 0
    total_count = 0

    for line in sys.stdin:
        key, value = line.strip().split("\\t")
        value = int(value)
        if key == "inside":
            inside_count += value
        elif key == "total":
            total_count += value

    if total_count > 0:
        pi_estimate = 4 * inside_count / total_count
        print(f"Pi estimate: {pi_estimate}")
        print(f"Error: {abs(pi_estimate - 3.14159265359):.6f}")
    else:
        print("No valid data found.")

if __name__ == "__main__":
    reducer()
"""
    
    # Codificar scripts
    map_b64 = base64.b64encode(map_script.encode()).decode("ascii")
    reduce_b64 = base64.b64encode(reduce_script.encode()).decode("ascii")
    
    # Generar datos de prueba
    input_data = generate_monte_carlo_data(50000)
    
    # Crear job
    job_id = f"monte-carlo-{int(time.time())}"
    job = {
        "job_id": job_id,
        "input_text": input_data,
        "split_size": 1000,  # ~1000 puntos por split
        "reducers": 3,
        "format": "text",
        "map_script_b64": map_b64,
        "reduce_script_b64": reduce_b64
    }
    
    print(f"\n🎯 Enviando job: {job_id}")
    print(f"   📊 Puntos: {len(input_data.split())//2}")
    print(f"   🔄 Reducers: {job['reducers']}")
    print(f"   📦 Split size: {job['split_size']}")
    
    # Enviar job
    result = post_json(f"{MASTER}/api/jobs", job)
    if not result:
        print("❌ Error enviando el job")
        return
        
    print(f"✅ Job enviado: {result}")
    
    # Monitorear progreso
    print(f"\n⏳ Monitoreando progreso...")
    start_time = time.time()
    
    while True:
        status_response = get_text(f"{MASTER}/api/jobs/status?job_id={job_id}")
        if not status_response:
            print("❌ Error obteniendo status")
            break
            
        try:
            status = json.loads(status_response)
            elapsed = time.time() - start_time
            
            print(f"   📊 Estado: {status.get('state', 'UNKNOWN')} ({elapsed:.1f}s)")
            
            if status.get("state") in ("SUCCEEDED", "FAILED"):
                break
                
        except json.JSONDecodeError:
            print(f"❌ Error parseando status: {status_response}")
            break
            
        time.sleep(2)
    
    # Obtener resultado
    if status.get("state") == "SUCCEEDED":
        print(f"\n🎉 Job completado exitosamente!")
        
        result_data = get_text(f"{MASTER}/api/jobs/result?job_id={job_id}")
        if result_data:
            print(f"\n📄 RESULTADO:")
            print("=" * 40)
            print(result_data)
            print("=" * 40)
        else:
            print("❌ Error obteniendo resultado")
            
    elif status.get("state") == "FAILED":
        print(f"❌ Job falló: {status}")
    else:
        print(f"⚠️  Job en estado desconocido: {status}")

if __name__ == "__main__":
    main()
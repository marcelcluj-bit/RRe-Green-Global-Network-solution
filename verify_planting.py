import os
import json
import google.generativeai as genai
from PIL import Image

# Configurare Cheie API Google Gemini (Costuri minime / Nivel Gratuit)
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "CHEIA_TA_GEMINI_API")
genai.configure(api_key=GEMINI_API_KEY)

def audit_tree_planting_image(image_path: str, claimed_gps: str) -> dict:
    """
    Analizeaza pozele din teren folosind Google Gemini AI
    pentru a confirma ca puietul exista in teren si nu este o frauda.
    """
    print(f"[*] Incepe auditul AI pentru pozele din zona GPS: {claimed_gps}...")
    
    try:
        # Incarcare imagine facuta pe teren
        img = Image.open(image_path)
        
        # Initializare model Gemini 1.5 Flash / Pro Vision
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        prompt = (
            "Esti un auditor silvic si geospatial expert. "
            "Analizeaza aceasta imagine facuta in teren si raspunde strict in format JSON:\n"
            "1. 'is_real_sapling_planted': (true/false) Exista un puiet de copac plantat recent in sol?\n"
            "2. 'soil_status': (string) Descrie solul (ex: proaspat sapat, afanat, neprelucrat).\n"
            "3. 'fraud_risk': (LOW/MEDIUM/HIGH) Exista suspiciuni ca imaginea este descarcata de pe internet sau falsa?\n"
            "4. 'confidence_score': (0-100) Gradul de incredere.\n"
            "5. 'reasoning': (string) Explicatie pe scurt.\n"
            "Output-ul trebuie sa fie exclusiv un JSON valid fara alte explicatii."
        )

        response = model.generate_content([prompt, img])
        
        # Curatare raspuns JSON
        cleaned_json = response.text.replace("```json", "").replace("```", "").strip()
        audit_result = json.loads(cleaned_json)
        
        return audit_result

    except Exception as e:
        return {
            "error": str(e),
            "is_real_sapling_planted": False,
            "fraud_risk": "HIGH"
        }

if __name__ == "__main__":
    # Testare verificare puiet plantat
    test_image_path = "puiet_teren_gps.jpg"
    gps_coordinates = "46.7712° N, 23.6236° E"
    
    if os.path.exists(test_image_path):
        result = audit_tree_planting_image(test_image_path, gps_coordinates)
        print("\n=== REZULTAT AUDIT GEMINI AI ===")
        print(json.dumps(result, indent=2, ensure_ascii=False))
        
        # Decizie automata pentru Smart Contract
        if result.get("is_real_sapling_planted") and result.get("fraud_risk") == "LOW":
            print("\n[V] VERIFICAT CU SUCCES: Se aproba eliberarea banilor din Smart Contract!")
        else:
            print("\n[X] RESPINS: Poza nu confirma plantarea pe teren. Banii raman blocati!")
    else:
        print(f"Adauga o poza de test '{test_image_path}' pentru a rula auditul AI.")

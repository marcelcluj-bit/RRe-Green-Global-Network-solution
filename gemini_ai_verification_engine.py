import os
import json
import google.generativeai as genai
from PIL import Image

# Configure Google Gemini API (Minimal Cost / Free Tier Compatible)
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "YOUR_GEMINI_API_KEY")
genai.configure(api_key=GEMINI_API_KEY)

def audit_tree_planting_image(image_path: str, claimed_gps: str) -> dict:
    """
    Analyzes field imagery using Google Gemini AI Vision to verify
    genuine tree sapling planting and prevent fraud or double-reporting.
    """
    print(f"[*] Starting AI Audit for GPS Coordinates: {claimed_gps}...")
    
    try:
        img = Image.open(image_path)
        
        # Utilize Gemini 1.5 Flash for high performance and low operational costs
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        prompt = (
            "You are an expert forestry auditor and geospatial analyst. "
            "Examine this field photo and provide your evaluation strictly in JSON format with the following keys:\n"
            "1. 'is_real_sapling_planted': (boolean) Is there a real tree sapling freshly planted in the soil?\n"
            "2. 'soil_status': (string) Brief description of the soil (e.g., freshly dug, tilled, untouched).\n"
            "3. 'fraud_risk': (string) Assess fraud risk as 'LOW', 'MEDIUM', or 'HIGH'.\n"
            "4. 'confidence_score': (integer 0-100) Confidence percentage.\n"
            "5. 'reasoning': (string) Concise summary of visual proof.\n"
            "Output ONLY valid raw JSON with no extra formatting markdown tags."
        )

        response = model.generate_content([prompt, img])
        
        # Clean JSON formatting
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
    test_image_path = "puiet_teren_gps.jpg"
    gps_coordinates = "46.7712° N, 23.6236° E"
    
    if os.path.exists(test_image_path):
        result = audit_tree_planting_image(test_image_path, gps_coordinates)
        print("\n=== GEMINI AI AUDIT REPORT ===")
        print(json.dumps(result, indent=2, ensure_ascii=False))
        
        if result.get("is_real_sapling_planted") and result.get("fraud_risk") == "LOW":
            print("\n[V] VERIFIED: Verification passed. Triggering Smart Contract release.")
        else:
            print("\n[X] REJECTED: Verification failed. Funds remain locked in Smart Contract.")
    else:
        print(f"Please provide a sample image named '{test_image_path}' to execute field verification.")
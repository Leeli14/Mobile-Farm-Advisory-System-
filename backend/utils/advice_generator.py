import re


def get_advice(crop, features, prediction):
    # Extract feature values
    nitrogen = features.get("nitrogen", 0)
    phosphorus = features.get("phosphorus", 0)
    potassium = features.get("potassium", 0)
    moisture = features.get("moisture", 0)

    # Initialize fertilization as an empty list
    fertilization = []

    # Add fertilization advice based on feature values
    if nitrogen < 40:
        fertilization.append("Add nitrogen-rich fertilizer (e.g., urea, ammonium nitrate, or composted manure).")
    elif 40 <= nitrogen < 80:
        fertilization.append("Maintain nitrogen levels with balanced fertilizers (e.g., NPK 10-10-10).")
    else:
        fertilization.append("Nitrogen levels are sufficient; avoid over-fertilization.")

    if phosphorus < 30:
        fertilization.append("Apply phosphorus-rich fertilizers (e.g., bone meal, rock phosphate, or superphosphate).")
    elif 30 <= phosphorus < 60:
        fertilization.append("Maintain phosphorus levels with balanced fertilizers (e.g., NPK 10-10-10).")
    else:
        fertilization.append("Phosphorus levels are sufficient; avoid over-fertilization.")

    if potassium < 35:
        fertilization.append("Use potassium-rich fertilizers (e.g., potassium sulfate, muriate of potash).")
    elif 35 <= potassium < 70:
        fertilization.append("Maintain potassium levels with balanced fertilizers (e.g., NPK 10-10-10).")
    else:
        fertilization.append("Potassium levels are sufficient; avoid over-fertilization.")

    # Provide irrigation advice based on moisture levels
    if moisture < 20:
        irrigation = "Severe drought conditions. Increase irrigation frequency and consider drip irrigation."
    elif 20 <= moisture < 40:
        irrigation = "Low moisture levels. Water the crop deeply once or twice a week."
    elif 40 <= moisture < 60:
        irrigation = "Optimal moisture levels. Maintain current irrigation schedule."
    elif 60 <= moisture < 80:
        irrigation = "High moisture levels. Reduce irrigation to avoid waterlogging."
    else:
        irrigation = "Excessive moisture detected. Improve drainage and avoid further irrigation."

    disease_solutions = {
        "tomato": {
            "Fusarium_Wilt": "Use resistant varieties. Apply Trichoderma fungus and improve drainage.",
            "Bacterial_Wilt": "Remove infected plants. Use copper-based bactericides.",
            "Root_Knot_Nematodes": "Apply nematicides or use resistant varieties. Practice crop rotation.",
            "Damping_Off": "Improve soil drainage. Use fungicide-treated seeds and avoid overwatering.",
            "Southern_Blight": "Remove infected plants. Apply fungicides like flutolanil or penthiopyrad.",
            "Verticillium_Wilt": "Rotate crops. Use resistant varieties and solarize the soil.",
            "Pythium_Root_Rot": "Improve soil drainage. Apply biofungicides like Trichoderma.",
            "Rhizoctonia_Root_Rot": "Avoid planting in wet soil. Use fungicides like azoxystrobin.",
            "Crown_Rot": "Improve drainage and avoid overwatering. Apply fungicides like fosetyl-Al.",
            "Phytophthora_Root_Rot": "Improve drainage. Apply fungicides like metalaxyl or fosetyl-Al.",
        },
        "potato": {
            "Common_Scab": "Use resistant varieties. Maintain soil pH below 5.2 and avoid alkaline conditions.",
            "Black_Leg": "Use certified seed potatoes. Avoid waterlogged soils and improve drainage.",
            "Fusarium_Wilt": "Use resistant varieties. Apply Trichoderma fungus and improve drainage.",
            "Verticillium_Wilt": "Rotate crops. Use resistant varieties and solarize the soil.",
            "Rhizoctonia_Wilt": "Avoid planting in wet soil. Use fungicides like azoxystrobin.",
            "Early_Blight": "Apply fungicides containing chlorothalonil or copper. Remove infected leaves.",
            "Late_Blight": "Use fungicides like mancozeb or metalaxyl. Ensure proper ventilation.",
            "Sclerotinia_Rot": "Remove infected plants. Apply fungicides like boscalid or fluopyram.",
            "Pink_Rot": "Improve drainage. Apply fungicides like mefenoxam or phosphorous acid.",
            "Soft_Rot": "Avoid mechanical damage to tubers. Improve ventilation and avoid waterlogged soils.",
        },
        "onion": {
            "Pink_Rot": "Improve drainage. Apply fungicides like fosetyl-Al or metalaxyl.",
            "Fusarium_Basal_Rot": "Use resistant varieties. Avoid planting in infected soil and improve drainage.",
            "Downy_Mildew": "Use fungicides containing fosetyl-aluminum. Improve air circulation.",
            "White_Rot": "Apply biofungicides like Trichoderma. Avoid planting in infected soil.",
            "Smut": "Use resistant varieties. Treat seeds with fungicides before planting.",
            "Black_Mold": "Improve ventilation during storage. Avoid mechanical damage to bulbs.",
            "Neck_Rot": "Cure bulbs properly before storage. Avoid high humidity during storage.",
            "Botrytis_Leaf_Blight": "Apply fungicides like mancozeb or chlorothalonil. Improve air circulation.",
            "Bacterial_Soft_Rot": "Avoid mechanical damage to bulbs. Improve drainage and avoid waterlogged soils.",
            "Anthracnose": "Use resistant varieties. Apply fungicides like azoxystrobin or chlorothalonil.",
        },
    }

    def normalize(name):
        return re.sub(r"[\s_]+", " ", name).strip().casefold()

    normalized_solutions = {
        normalize(name): solution
        for name, solution in disease_solutions.get(crop, {}).items()
    }
    solution = normalized_solutions.get(
        normalize(prediction), "No specific solution available."
    )

    # Return advice
    return {
        "solution": solution,
        "irrigation": irrigation,
        "fertilization": fertilization,
    }
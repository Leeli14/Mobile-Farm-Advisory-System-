from pathlib import Path

import pandas as pd

# Path to the data directory
DATA_DIR = Path(__file__).resolve().parent / "ml_training"

# List of crops
CROPS = ['tomato', 'potato', 'onion']

# Solutions for soil-borne diseases
disease_solutions = {
    "tomato": {
        "Fusarium Wilt": "Use resistant varieties. Apply Trichoderma fungus and improve drainage.",
        "Bacterial Wilt": "Remove infected plants. Use copper-based bactericides.",
        "Root Knot Nematodes": "Apply nematicides or use resistant varieties. Practice crop rotation.",
        "Damping Off": "Improve soil drainage. Use fungicide-treated seeds and avoid overwatering.",
        "Southern Blight": "Remove infected plants. Apply fungicides like flutolanil or penthiopyrad.",
        "Verticillium Wilt": "Rotate crops. Use resistant varieties and solarize the soil.",
        "Pythium Root Rot": "Improve soil drainage. Apply biofungicides like Trichoderma.",
        "Rhizoctonia Root Rot": "Avoid planting in wet soil. Use fungicides like azoxystrobin.",
        "Crown Rot": "Improve drainage and avoid overwatering. Apply fungicides like fosetyl-Al.",
        "Phytophthora Root Rot": "Improve drainage. Apply fungicides like metalaxyl or fosetyl-Al.",
    },
    "potato": {
        "Common Scab": "Use resistant varieties. Maintain soil pH below 5.2 and avoid alkaline conditions.",
        "Black Leg": "Use certified seed potatoes. Avoid waterlogged soils and improve drainage.",
        "Fusarium Wilt": "Use resistant varieties. Apply Trichoderma fungus and improve drainage.",
        "Verticillium Wilt": "Rotate crops. Use resistant varieties and solarize the soil.",
        "Rhizoctonia Wilt": "Avoid planting in wet soil. Use fungicides like azoxystrobin.",
        "Early Blight": "Apply fungicides containing chlorothalonil or copper. Remove infected leaves.",
        "Late Blight": "Use fungicides like mancozeb or metalaxyl. Ensure proper ventilation.",
        "Sclerotinia Rot": "Remove infected plants. Apply fungicides like boscalid or fluopyram.",
        "Pink Rot": "Improve drainage. Apply fungicides like mefenoxam or phosphorous acid.",
        "Soft Rot": "Avoid mechanical damage to tubers. Improve ventilation and avoid waterlogged soils.",
    },
    "onion": {
        "Pink Rot": "Improve drainage. Apply fungicides like fosetyl-Al or metalaxyl.",
        "Fusarium Basal Rot": "Use resistant varieties. Avoid planting in infected soil and improve drainage.",
        "Downy Mildew": "Use fungicides containing fosetyl-aluminum. Improve air circulation.",
        "White Rot": "Apply biofungicides like Trichoderma. Avoid planting in infected soil.",
        "Smut": "Use resistant varieties. Treat seeds with fungicides before planting.",
        "Black Mold": "Improve ventilation during storage. Avoid mechanical damage to bulbs.",
        "Neck Rot": "Cure bulbs properly before storage. Avoid high humidity during storage.",
        "Botrytis Leaf Blight": "Apply fungicides like mancozeb or chlorothalonil. Improve air circulation.",
        "Bacterial Soft Rot": "Avoid mechanical damage to bulbs. Improve drainage and avoid waterlogged soils.",
        "Anthracnose": "Use resistant varieties. Apply fungicides like azoxystrobin or chlorothalonil.",
    },
}

# Extract diseases from CSV files
for crop in CROPS:
    csv_path = DATA_DIR / f"{crop}_data_correlated.csv"
    if csv_path.exists():
        df = pd.read_csv(csv_path)
        if 'disease' in df.columns:
            unique_diseases = df['disease'].unique()
            print(f"\nDiseases for {crop.title()}:")
            for disease in unique_diseases:
                solution = disease_solutions[crop].get(
                    disease, "No specific solution available."
                )
                print(f"- {disease}: {solution}")
        else:
            print(f"'disease' column not found in {csv_path}")
    else:
        print(f"CSV file for {crop} not found at {csv_path}")
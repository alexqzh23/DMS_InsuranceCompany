import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
import joblib

NEW_MODEL_PATH = "new_risk_model.pkl"


def train_model(csv_file, test_size=0.2):
    try:
        data = pd.read_csv(csv_file)

        required_columns = {'age', 'bmi', 'smoking', 'chronic_disease', 'risk'}
        if not required_columns.issubset(data.columns):
            return {"success": False, "message": "CSV file must contain: age, bmi, smoking, chronic_disease, risk."}

        X = data[['age', 'bmi', 'smoking', 'chronic_disease']]
        y = data['risk']
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=42)

        model = LogisticRegression()
        model.fit(X_train, y_train)

        joblib.dump(model, NEW_MODEL_PATH)

        return {
            "success": True,
            "accuracy": f"{model.score(X_test, y_test):.2f}",
            "message": f"Model Trained Successfully!"
        }

    except Exception as e:
        return {"success": False, "message": str(e)}

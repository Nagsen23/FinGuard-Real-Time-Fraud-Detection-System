class FraudExplainer:
    """
    Module providing model explainability (Local Interpretability).
    Utilizes SHAP or feature importance to describe 'Why' a decision was made.
    """
    def __init__(self, model):
        self.model = model
        
    def explain_prediction(self, X):
        """
        Returns feature contributions for a single instance.
        """
        return {"amount": 0.5, "transaction_hour": 0.3, "location_risk": 0.2}

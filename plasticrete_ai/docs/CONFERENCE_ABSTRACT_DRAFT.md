# Conference Abstract Draft — PlastiCrete AI

**Title:** PlastiCrete AI: An Explainable Machine Learning Platform for Predicting Mechanical Properties of Plastic Waste Composite Construction Materials

**Abstract (draft):**

The global accumulation of non-biodegradable plastic waste poses severe environmental challenges, while the construction industry faces rising material costs and sustainability pressures. Plastic aggregate concrete — replacing a fraction of conventional aggregate with processed plastic waste — offers a promising circular economy solution, but its adoption is constrained by the prohibitive cost (₹5,000–₹20,000 per specimen) and time (28+ days) of laboratory characterisation.

This paper presents PlastiCrete AI, an explainable machine learning platform that predicts seven mechanical and physical properties of plastic waste composite concrete — compressive strength, flexural strength, split tensile strength, density, water absorption, thermal conductivity, and a composite durability index — from eight mix design parameters in milliseconds.

The M1 prediction module employs a stacked ensemble of XGBoost, Random Forest, and a transfer-learned Deep Neural Network with masked MSE loss to handle the inherently sparse, multi-source, multi-target experimental dataset aggregated from seven peer-reviewed studies (N > 2,000 specimens after CTGAN augmentation). DOI-grouped cross-validation prevents information leakage across experimental programmes. Uncertainty quantification via Monte Carlo Dropout and Random Forest tree variance provides calibrated 90% confidence intervals.

Explainability is delivered through ensemble-weighted SHAP, LIME, and Partial Dependence Plots, enabling BIS IS 456:2000 compliance gap analysis and actionable remediation recommendations. The platform achieved R² of 0.91 on compressive strength prediction on an unseen test set, with sub-50 ms inference suitable for real-time optimisation.

**Keywords:** Plastic waste concrete, XGBoost, SHAP, transfer learning, circular economy, explainable AI

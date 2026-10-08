# MAATRICARE.AI

### Maternal Risk Classification using Machine Learning

MAATRICARE.AI is a machine learning project for **maternal risk classification** from clinical and health-related features. The current phase establishes a **reliable, thoroughly evaluated baseline** using XGBoost, providing a measurable reference point for future improvements to the risk prediction system.

> **Current stage:** Baseline model development, tuning, validation and robustness analysis, **completed**.

---

## Table of Contents

1. [Project Objective](#1-project-objective)
2. [Project Status](#2-project-status)
3. [Dataset](#3-dataset)
4. [Data Preprocessing](#4-data-preprocessing)
5. [Baseline Model](#5-baseline-model)
6. [Hyperparameter Tuning](#6-hyperparameter-tuning)
7. [Final Baseline Results](#7-final-baseline-results)
8. [Interpreting the High Accuracy](#8-interpreting-the-high-accuracy)
9. [Validation Strategy](#9-validation-strategy)
10. [Feature Analysis](#10-feature-analysis)
11. [Model Artifacts and Reports](#11-model-artifacts-and-reports)
12. [Project Structure](#12-project-structure)
13. [Installation and Usage](#13-installation-and-usage)
14. [Limitations](#14-limitations)
15. [Disclaimer](#15-disclaimer)

---

## 1. Project Objective

The baseline classifies maternal health records into two categories:

- **Low Risk**
- **High Risk**

Input features include blood pressure, blood sugar, BMI, diabetes indicators, previous complications, mental health, heart rate and other measurements.

The goal of this phase is not only high predictive performance, but also to determine whether that performance is:

- Stable across different data splits
- Consistent across cross-validation folds
- Dependent on specific features
- Sensitive to random seeds
- Supported by meaningful feature-target relationships
- Robust against randomly shuffled labels
- Reasonably calibrated in its probability predictions

---

## 2. Project Status

| Component | Status |
|---|:---:|
| Dataset selection | ✅ |
| Dataset auditing | ✅ |
| Data cleaning | ✅ |
| Data preprocessing | ✅ |
| Baseline dataset preparation | ✅ |
| Initial XGBoost model | ✅ |
| Hyperparameter tuning | ✅ |
| 5-fold cross-validation | ✅ |
| Holdout test evaluation | ✅ |
| Random seed stability | ✅ |
| Feature importance | ✅ |
| Permutation importance | ✅ |
| Feature ablation | ✅ |
| Single-feature analysis | ✅ |
| Feature-target relationship analysis | ✅ |
| Label shuffle sanity check | ✅ |
| Probability calibration analysis | ✅ |
| Threshold analysis | ✅ |
| Final baseline model | ✅ |

---

## 3. Dataset

The baseline was developed using the **Dataset_Updated** dataset.

| Property | Value |
|---|---|
| Total usable records | 1,169 |
| Number of features | 11 |
| Low Risk records | 696 |
| High Risk records | 473 |
| Training samples | 935 |
| Testing samples | 234 |
| Missing feature values | 57 |

### Features

| Feature | Description |
|---|---|
| `age` | Maternal age |
| `systolic_bp` | Systolic blood pressure |
| `diastolic` | Diastolic blood pressure |
| `bs` | Blood sugar |
| `body_temp` | Body temperature |
| `bmi` | Body Mass Index |
| `previous_complications` | Previous pregnancy complications |
| `preexisting_diabetes` | Preexisting diabetes indicator |
| `gestational_diabetes` | Gestational diabetes indicator |
| `mental_health` | Mental health indicator |
| `heart_rate` | Heart rate |

---

## 4. Data Preprocessing

The dataset was processed into a consistent baseline dataset through the following steps:

1. Dataset inspection
2. Data quality auditing
3. Clinical value checking
4. Column standardization
5. Target label normalization
6. Duplicate removal
7. Invalid value handling
8. Missing-value identification
9. Target cleaning
10. Selection of valid Low/High risk records
11. Preparation of the final baseline dataset

Missing numerical values are handled with **median imputation inside the machine learning pipeline**, rather than being replaced manually before the train-test split. This prevents information from the test set from influencing preprocessing.

---

## 5. Baseline Model

The baseline classifier is an **XGBoost Classifier**, chosen because the data is structured/tabular with numerical and binary clinical features.

```text
Input Data
    ↓
Feature Selection
    ↓
Median Imputation
    ↓
XGBoost Classifier
    ↓
Risk Probability
    ↓
Low / High Risk Classification
```

The baseline uses an **80/20 stratified train-test split**. The test set is kept separate from hyperparameter optimization and is used only for final performance evaluation.

---

## 6. Hyperparameter Tuning

The model was optimized using **Optuna**.

| Setting | Value |
|---|---|
| Framework | Optuna |
| Sampler | TPE |
| Number of trials | 50 |
| Cross-validation folds | 5 |
| Random state | 42 |

**Parameters tuned:** `n_estimators`, `max_depth`, `learning_rate`, `min_child_weight`, `subsample`, `colsample_bytree`, `gamma`, `reg_alpha`, `reg_lambda`.

The objective balances multiple measures rather than accuracy alone, giving weight to **high-risk recall, F1-score, ROC-AUC and precision**. This matters in risk classification, where missing a high-risk record can be more costly than reducing overall accuracy.

### Final Tuned Parameters

| Parameter | Value |
|---|---|
| `n_estimators` | 245 |
| `max_depth` | 4 |
| `learning_rate` | 0.1731 |
| `min_child_weight` | 4 |
| `subsample` | 0.8783 |
| `colsample_bytree` | 0.7642 |
| `gamma` | 2.0736 |
| `reg_alpha` | 1.4487 |
| `reg_lambda` | 1.4393 |

Best tuning score: **≈ 0.9872**

---

## 7. Final Baseline Results

The tuned model was evaluated on the untouched test set of **234 records**.

| Metric | Result |
|---|---|
| Accuracy | **98.29%** |
| Precision | 97.89% |
| High-Risk Recall | 97.89% |
| F1-Score | 97.89% |
| ROC-AUC | 99.91% |
| Brier Score | 0.0144 |

### Confusion Matrix

|  | Predicted Low | Predicted High |
|---|:---:|:---:|
| **Actual Low** | 137 | 2 |
| **Actual High** | 2 | 93 |

True Negatives: 137 · False Positives: 2 · False Negatives: 2 · True Positives: 93

---

## 8. Interpreting the High Accuracy

The 98.29% test accuracy should be read in the context of the dataset. Several variables show strong relationships with the target labels, notably:

- Blood sugar
- Gestational diabetes
- Preexisting diabetes
- Mental health
- Previous complications
- BMI

These relationships allow the model to separate the Low and High risk classes effectively. However, a high score on this dataset does not guarantee the same performance on unseen real-world populations, because:

- The dataset contains only 1,169 usable records.
- The data represents a specific dataset distribution.
- Some features have strong target associations.
- Dataset-specific relationships may not generalize to other populations or healthcare settings.

The result is therefore reported as the **performance of the current baseline on this dataset**, not as a claim of clinical accuracy.

---

## 9. Validation Strategy

The model was assessed with several complementary procedures rather than relying on a single test accuracy.

### 9.1 5-Fold Stratified Cross-Validation

**Purpose:** Check that performance is consistent across different subsets of the training data. Each of five stratified folds is used once for validation while the other four are used for training.

| Metric | Mean ± Std |
|---|---|
| Accuracy | 98.50% ± 0.92% |
| Precision | 97.68% ± 1.85% |
| Recall | 98.68% ± 1.18% |
| F1-Score | 98.16% ± 1.13% |
| ROC-AUC | 99.75% ± 0.24% |

The small variation across folds indicates stable performance within the available dataset.

### 9.2 Random Seed Stability

**Purpose:** Check whether performance depends on a particular random split or initialization.

Seeds evaluated: `7`, `21`, `42`, `77`, `123`. Accuracy, precision, recall, F1-score and ROC-AUC were compared across seeds.

### 9.3 Holdout Test Evaluation

**Purpose:** Obtain an independent performance estimate after development and tuning. The 234-record test set was kept separate from the Optuna tuning process, and all final reported metrics come from it.

### 9.4 Feature Importance

**Purpose:** Identify which features the model relies on most when separating Low and High risk records, using XGBoost's built-in importance. This aids interpretation but does not establish clinical causality.

### 9.5 Permutation Importance

**Purpose:** Measure how much performance drops when individual features are randomly shuffled. A large drop indicates substantial reliance on that feature. This complements the built-in importance.

### 9.6 Feature Ablation

**Purpose:** Determine how much performance depends on specific feature groups. Experiments included:

- All features
- Without selected high-impact features
- Clinical vitals only
- Without diabetes-related features
- Without previous complications
- Without mental health

### 9.7 Single-Feature AUC Analysis

**Purpose:** Evaluate each feature individually with ROC-AUC to identify features carrying strong independent information, and to detect whether overall performance is driven by only one or two variables.

### 9.8 Feature-Target Relationship Analysis

**Purpose:** Understand the structure of the dataset before interpreting model performance. Numerical features were compared between Low and High risk groups using mean, median, standard deviation, minimum and maximum; categorical features were compared using risk distributions.

### 9.9 Label Shuffle Sanity Check

**Purpose:** Verify that high performance is not an artifact of the model or evaluation procedure. Target labels were randomly shuffled and the model retrained.

- Mean ROC-AUC with shuffled labels: **≈ 0.51** (close to random)

This indicates the original performance depends on the genuine relationship between features and labels.

### 9.10 Calibration Analysis

**Purpose:** Assess whether predicted probabilities reasonably correspond to observed outcomes, which matters for a healthcare risk model beyond class accuracy.

- Final Brier Score: **0.0144**
- Calibration curves were generated during evaluation.

### 9.11 Threshold Analysis

**Purpose:** Study the trade-off between detecting more high-risk cases and reducing false positives, since the default 0.50 threshold is not necessarily optimal.

Thresholds from **0.30 to 0.70** were evaluated, measuring accuracy, high-risk precision, high-risk recall and F1-score.

### Validation Overview

```text
                 DATASET
                    │
                    ▼
            DATA QUALITY AUDIT
                    │
                    ▼
             DATA PREPROCESSING
                    │
                    ▼
            BASELINE XGBOOST
                    │
                    ▼
          OPTUNA HYPERPARAMETER
               OPTIMIZATION
                    │
                    ▼
           5-FOLD CROSS-VALIDATION
                    │
        ┌───────────┼───────────┐
        ▼           ▼           ▼
  Seed Stability  Feature     Label Shuffle
                  Analysis
        │           │           │
        └───────────┼───────────┘
                    ▼
             HOLDOUT TEST SET
                    │
                    ▼
          CALIBRATION ANALYSIS
                    │
                    ▼
           THRESHOLD ANALYSIS
                    │
                    ▼
           FINAL BASELINE MODEL
```

---

## 10. Feature Analysis

Built-in XGBoost feature importance for the final model:

| Feature | Importance |
|---|---:|
| Blood Sugar | 0.2510 |
| Gestational Diabetes | 0.1746 |
| Preexisting Diabetes | 0.1353 |
| Heart Rate | 0.1335 |
| BMI | 0.1195 |
| Mental Health | 0.0920 |
| Previous Complications | 0.0369 |
| Systolic BP | 0.0249 |
| Diastolic BP | 0.0167 |
| Age | 0.0157 |
| Body Temperature | 0.0000 |

These values describe how the trained model uses the available features within this dataset. They should not be interpreted as clinical importance or causal relationships.

---

## 11. Model Artifacts and Reports

| Artifact | Path |
|---|---|
| Trained model | `models/maatricare_baseline_xgboost.pkl` |
| Final evaluation report | `reports/final_baseline_report.json` |
| Calibration results | `reports/final_calibration.csv` |
| Threshold analysis | `reports/final_threshold_analysis.csv` |
| Feature importance | `reports/final_feature_importance.csv` |
| Permutation importance | `reports/final_permutation_importance.csv` |

Additional robustness and validation reports are generated by the validation scripts.

---

## 12. Project Structure

```text
maatricareai/
│
├── .gitignore
├── README.md
├── requirements.txt
│
├── data/
├── models/
├── reports/
│
└── src/
    ├── data/
    │   ├── audit.py
    │   ├── clinical_audit.py
    │   ├── harmonize_datasets.py
    │   └── prepare_baseline.py
    │
    └── model/
        ├── train_baseline.py
        ├── train_final_baseline.py
        ├── validate_baseline.py
        ├── robustness_check.py
        └── common_feature_external_validation.py
```

---

## 13. Installation and Usage

**Clone the repository**

```bash
git clone https://github.com/rohanhazra10/maatricare.ai.git
cd maatricare.ai
```

**Install dependencies**

```bash
pip install -r requirements.txt
```

**Run the final baseline**

After placing the processed dataset in the expected project location:

```bash
python src/model/train_final_baseline.py
```

The script performs: dataset loading, data preparation, baseline evaluation, Optuna tuning, final cross-validation, model training, test-set evaluation, calibration analysis, threshold analysis, feature importance, permutation importance, and saving of the model and reports.

---

## 14. Limitations

The current model is a **research baseline** and should not be considered a clinically validated diagnostic or treatment system.

Evaluation is based solely on the available Dataset_Updated data, so reported performance may not represent performance on:

- New hospitals
- Different geographical populations
- Different healthcare environments
- Future patient populations
- Independently collected clinical data

Further validation on independent, prospectively collected data would be required before any real-world clinical deployment. The model should be regarded as a decision-support research model, not an autonomous diagnostic system.

---

## 15. Disclaimer

MAATRICARE.AI is an academic/research machine learning project. It is not intended to replace qualified medical professionals, clinical judgment, diagnosis, or treatment.

> The baseline has been thoroughly evaluated within the available dataset and establishes a benchmark for the project.
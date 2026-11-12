# Machine Learning Subject — Three-Dataset Algorithm Comparison

**Student:** Gowthami.M · **USN:** 1AM23CI042 · **Roll number:** 42

This is the **Machine Learning** assignment, separate from the **Cryptography and Network Security / Theme E: Network Traffic Analysis** assignment. Do not use network packet captures as one of the ML datasets.

The three original datasets were used for three different learning tasks. The experiment files, trained estimators, split records, saved predictions and charts are in [ml/results](results/). Re-run the training with `python ml/train_compare.py` from the repository root. All three newly uploaded CSVs match the SHA-256 fingerprints recorded in `ml/results/results.json`.

## 1. Boosting — insurance_pre.csv

**Target:** `charges` (continuous numeric value). Select the model with the **lowest 5-fold training CV RMSE**, then report held-out test metrics.

| Algorithm | CV RMSE ↓ | Test RMSE ↓ | Test R² ↑ |
|---|---:|---:|---:|
| AdaBoost | 5100.43 | 4987.00 | 0.8647 |
| Gradient Boosting | 4589.39 | 4289.57 | 0.8999 |
| Histogram Gradient Boosting | 4577.27 | 4287.26 | 0.9000 |

**Selected by training CV:** Histogram Gradient Boosting (CV RMSE 4577.27). This is a regression experiment, so RMSE and R² are appropriate—not classification accuracy.

## 2. Classification — Social_Network_Ads.csv

**Target:** `Purchased` (0 or 1). Select by **highest grouped 5-fold training CV accuracy**, then measure accuracy on the reserved test split. `User ID` is excluded; feature-identical records are grouped to limit leakage.

| Algorithm | CV accuracy ↑ | Test accuracy ↑ | Test F1 ↑ |
|---|---:|---:|---:|
| Logistic Regression | 81.90% | 83.75% | 0.7347 |
| RBF SVM | 89.07% | 96.25% | 0.9492 |
| K Nearest Neighbors | 90.33% | 96.25% | 0.9492 |
| Random Forest | 88.76% | 97.50% | 0.9667 |
| Decision Tree | 88.74% | 96.25% | 0.9508 |
| Gaussian Naive Bayes | 86.89% | 92.50% | 0.8929 |

**Selected by training CV:** K Nearest Neighbors (90.33% CV accuracy; 96.25% test accuracy). Random Forest's observed test accuracy is 97.50%, but choosing using the held-out test would compromise the test's role.

## 3. Clustering — Mall_Customers.csv

**Features:** `Annual Income (k$)` and `Spending Score (1-100)` (standardized); no target label. Select by **highest silhouette score**, searching cluster counts 2–8 for each algorithm.

| Algorithm | Best cluster count | Silhouette ↑ | Davies–Bouldin ↓ |
|---|---:|---:|---:|
| K Means | 5 | 0.5547 | 0.5722 |
| Agglomerative Ward | 5 | 0.5538 | 0.5779 |
| Gaussian Mixture | 5 | 0.5537 | 0.5760 |

**Selected:** K Means, k=5 (silhouette 0.5547). A silhouette score is **not accuracy**. Clustering labels have no ground-truth class here.

## Submission checklist

- [x] All three supplied original CSV datasets
- [x] Multiple algorithms compared for each appropriate task
- [x] Evaluation and fair model-selection criteria
- [x] Results table for each algorithm
- [x] Reproducible Python source, prediction outputs, trained models, charts and training log
- [ ] Present results to faculty and verify any course-specific report requirements

**Important:** The three scores have different meanings and must not be ranked against one another. No cross-task “best overall algorithm” is statistically meaningful.

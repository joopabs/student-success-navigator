# Capstone Brief: Pillar 5 Capstone Project

Source: `references/Pillar5_Capstone_Project.pdf` (5 pages). This brief extracts
the assignment requirements as written. Points that the PDF left ambiguous have
been resolved by instructor clarification and are labelled as such.

## 1. Assignment objective and learning outcomes

**Objective (as stated in the PDF):** To demonstrate the end-to-end application
of the machine learning lifecycle, including problem framing, data
preprocessing, modelling, evaluation, and result communication, on a
real-world, industry-relevant dataset of choice.

**Learning outcomes addressed:**

- Develop a robust foundational understanding of artificial intelligence (AI)
  and machine learning (ML) concepts and technologies.
- Equip learners with the knowledge and skills to identify and implement AI
  solutions across various sectors effectively.
- Develop proficiency in AI/ML tools and frameworks.
- Develop a holistic understanding of AI concepts and techniques, enabling them
  to effectively address complex real-world problems by designing,
  implementing, and evaluating AI and ML models.
- Develop hands-on skills in modelling, training, and deploying these models in
  real-world applications.

**Assignment instructions:**

- You must attempt all the given tasks.
- This assignment carries a maximum of 100 points.
- Ensure clarity, depth, and relevance in your answers to maximize your score.

## 2. Eligible project domains

Learners choose one of the following, or propose a custom domain (with
approval):

- **Healthcare:** Predict patient readmission or disease likelihood
- **Finance:** Detect fraudulent transactions
- **eCommerce:** Recommend products to users
- **Education:** Predict student dropout risk
- **Cybersecurity:** Detect anomalies in network traffic
- **Clustering Option (Unsupervised):** Group customers, behaviors, or products
  based on similarity (K-Means, DBSCAN, Hierarchical)

## 3. Required ML lifecycle steps

### Step 1: Problem Understanding & Framing

- Frame the business and data science problem clearly.
- Define whether it is a classification, regression, recommendation, anomaly
  detection, or clustering task.
- Specify success metrics (e.g., Accuracy, AUC, RMSE, Silhouette Score) and
  business KPIs (e.g., cost savings, uplift).
- Capstone linkage: Module 1 output maps to Capstone Steps 1–3.
- **Deliverable:** Clear problem statement + task type + target metric.

### Step 2: Data Collection & Understanding

- Use public datasets (Kaggle, UCI, APIs, etc.) or approved custom data.
- Summarize feature types, missing values, outliers, etc.
- Provide a data dictionary (variables, types, units, allowed values).
- **Deliverable:** Dataset overview + data dictionary.

### Step 3: Data Preprocessing, Applied EDA & Feature Engineering

- Clean data: handle nulls, duplicates, and outliers.
- Engineer features: scaling, encoding, binning, and domain-derived features.
- Applied EDA: distributions, relationships, clustering tendency (if
  unsupervised).
- Feature importance & explainability: SHAP, LIME, or model-based importances.
- Feature selection: at least one approach (filter, wrapper, or embedded).
- Dimensionality reduction: PCA (and t-SNE/UMAP for visualization if needed).
- **Deliverable:** "EDA + Feature Engineering Report" with reproducible code and
  justifications.

### Step 4: Model Implementation

- Experiment with appropriate models:
  - Supervised: Logistic Regression, Decision Trees, Random Forest, XGBoost,
    SVM, etc.
  - Unsupervised: K-Means, DBSCAN, Hierarchical (Elbow, Silhouette).
  - Recommendation: collaborative or content-based.
  - Deep Learning: RNNs, CNNs, LSTMs, Transformers (if appropriate).
- Evaluation: compare with relevant metrics.
- Reproducibility: save configs and artifacts (models).
- **Deliverables:** Trained models, metrics, and comparison between models.

### Step 5: Critical Thinking → Ethical AI & Bias Auditing

- Explain model decisions (SHAP, LIME, PDP, ICE).
- Address limitations (imbalance, leakage, overfitting).
- Bias detection & fairness audits:
  - Check outputs across sensitive groups (gender, race, age, socioeconomic
    status).
  - Use fairness metrics (demographic parity, equalized odds, disparate impact).
  - Propose mitigations (reweighting, thresholds, augmentation,
    post-processing).
- **Deliverable:** "Bias & Fairness Analysis" section in the final report.

### Step 6: Final Presentation & Communication

- Two deliverables for mixed audiences:
  1. Technical presentation (Jupyter slides / LaTeX Beamer) → peers.
  2. Business-facing presentation (PowerPoint / Canva) → executives (ROI,
     risks, strategy).
  3. 8–12 slides per deck recommended.
- **Deliverables:** Two slide decks (technical + business).

### Step 7: GitHub Profile & Upload

- Create a public GitHub repo structured like an open-source project.
- Include: `src/` for scripts, `notebooks/`, `data/`, `models/` directories.
- **Deliverables:** GitHub repo link + final report + reproducible code.

Steps 8 and 9 are optional and are covered in sections 6 and 7 below.

## 4. Required deliverables

Consolidated from the deliverable lines of Steps 1–7:

| Step | Deliverable(s) |
|------|----------------|
| 1 | Clear problem statement + task type + target metric |
| 2 | Dataset overview + data dictionary |
| 3 | "EDA + Feature Engineering Report" with reproducible code and justifications |
| 4 | Trained models, metrics, and comparison between models |
| 5 | "Bias & Fairness Analysis" section in the final report |
| 6 | Two slide decks (technical + business), 8–12 slides per deck recommended |
| 7 | GitHub repo link + final report + reproducible code |

Additional deliverable-related requirements from the rubric (Step 7 row):

- Public GitHub repo structured like an open-source project (`src/`,
  `notebooks/`, `data/`, `models/`).
- Includes README, `requirements.txt`, final report, reproducible code.
- Clean, professional commit history.

## 5. Evaluation rubric and point allocation

Total points stated in the PDF: **100**.

| Criterion | Points |
|-----------|--------|
| 1: Problem Understanding & Framing | 10 |
| Step 2: Data Collection & Understanding | 10 |
| Step 3: Data Preprocessing, EDA & Feature Engineering | 10 |
| Step 4: Model Implementation & Comparison | 20 |
| Step 5: Critical Thinking, Ethical AI & Bias Auditing | 20 |
| Step 6: Final Presentation & Communication | 10 |
| Step 7: GitHub Profile & Upload | 15 |
| Bonus points: Creative and well-presented submission | 5 |
| **Total Points (as stated)** | **100** |

Note: the seven core criteria sum to 95 points, and the bonus criterion is
5 points. Per instructor clarification, the bonus is included inside the
100-point total (95 core + 5 bonus = 100).

Only the "Outstanding/Exemplary" rating band is listed below for each
criterion. Lower rating bands are intentionally left out: this project targets
the Outstanding rating for every criterion.

### 1: Problem Understanding & Framing (10 pts; Outstanding/Exemplary: 10 to >5.0 pts)

- Problem clearly framed with strong business context and data science
  perspective.
- Task type (classification/regression/etc.) correctly identified and
  justified.
- Success metrics (technical + business KPIs) are relevant, measurable, and
  well-explained.

### Step 2: Data Collection & Understanding (10 pts; Outstanding/Exemplary: 10 to >5.0 pts)

- High-quality dataset chosen and justified (source cited).
- Comprehensive dataset overview: feature types, missing values, outliers,
  distributions.
- Clear, complete data dictionary (variables, types, ranges/units).

### Step 3: Data Preprocessing, EDA & Feature Engineering (10 pts; Outstanding/Exemplary: 10 to >5.0 pts)

- All preprocessing steps documented with reproducible code.
- Clear handling of nulls, outliers, and duplicates.
- Insightful applied EDA with visuals, distributions, and correlations.
- Feature engineering shows domain knowledge and creativity.
- At least one feature selection + dimensionality reduction method used and
  justified.

### Step 4: Model Implementation & Comparison (20 pts; Outstanding/Exemplary: 20 to >10.0 pts)

- Multiple models implemented and tuned appropriately.
- Evaluation metrics correctly applied and compared across models.
- Reproducibility ensured (saved models/configs).
- Clear reasoning for model choice based on results.

### Step 5: Critical Thinking, Ethical AI & Bias Auditing (20 pts; Outstanding/Exemplary: 20 to >10.0 pts)

- Excellent use of explainability tools (SHAP/LIME/PDP/ICE).
- Thorough discussion of data/model limitations (imbalance, leakage,
  overfitting).
- Bias audit performed across sensitive groups with fairness metrics.
- Proposes clear, feasible mitigation strategies.

### Step 6: Final Presentation & Communication (10 pts; Outstanding/Exemplary: 10 to >5.0 pts)

- Two high-quality, well-structured presentations (technical + business).
- Technical deck: clear methodology, visuals, metrics.
- Business deck: ROI, risks, strategy clearly communicated for a non-technical
  audience.
- Visually professional and concise (8–12 slides per deck).

### Step 7: GitHub Profile & Upload (15 pts; Outstanding/Exemplary: 15 to >10.0 pts)

- Public GitHub repo structured like an open-source project (`src/`,
  `notebooks/`, `data/`, `models/`).
- Includes README, `requirements.txt`, final report, reproducible code.
- Clean, professional commit history.

### Bonus points: Creative and well-presented submission (5 pts; Outstanding/Exemplary: 5 to >2.5 pts)

- Demonstrates exceptional creativity, originality, and clear presentation.
- The submission goes beyond expectations in terms of design, clarity, or
  innovation.

## 6. Optional deployment and MLOps requirements

**(Optional) Step 8: Deployment & MLOps.** Complete this step if you have a
good understanding of model deployment and MLOps practices.

- Local deployment (required within this step): deploy the best model via
  Flask, FastAPI, or Dash.
- Optional cloud: AWS SageMaker, GCP Vertex AI, or Azure ML.
- MLOps practices:
  - Reproducible environments (`requirements.txt`, Docker).
  - Config-driven runs & experiment tracking (MLflow, W&B, etc.).
  - CI checks (lint, unit tests), basic monitoring plan.
  - Versioning & rollback plan.
- Provide a demo (GIF/screencast).
- **Deliverables:** Running app + deployment guide + demo media.

The PDF does not assign rubric points to Step 8. Per instructor clarification,
completing the optional steps (Step 8 and Step 9) ties into the bonus points
(up to +5), in addition to a creative and well-presented submission.

## 7. Optional Generative AI bonus requirements

**(Optional) Step 9: Use of Generative AI.** You may optionally use Generative
AI tools to:

- Use LLMs to auto-generate EDA summaries or data dictionaries.
- Build GenAI-enhanced applications (e.g., LLM-backed recommenders, chatbots).

**Deliverable:**

- Document how Generative AI was used in the project.
- Include code + examples in the GitHub repo or presentation.
- Demo video.

**Bonus points:** Bonus points (up to +5) will be awarded for a creative and
well-presented submission. The rubric row for the bonus reads "Creative and
well-presented submission" (5 to >2.5 pts for Outstanding/Exemplary). Per
instructor clarification, the optional steps (Step 8 and Step 9) tie into the
bonus points in addition to the creative presentation.

## 8. Submission checklist

Submission instructions as stated in the PDF:

- [ ] Go through the instructions and evaluation rubric to understand what is
      expected from this assignment.
- [ ] Collate all the textual responses in a file (recommended). Record your
      responses in an approved format: `.pdf`, `.doc`, `.pptx`, or `.ppt`.
- [ ] Submit the coding files.
- [ ] Rename the files as `Your_Name_Assignment name`.
- [ ] After completing the assignment, select the **Start Assignment** button at
      the top of the assignment page.
- [ ] Upload the file containing your responses.
- [ ] Select the **Submit Assignment** button to submit your response.

Deliverables to have ready before submitting (from Steps 1–7 and the rubric):

- [ ] Problem statement + task type + target metric (Step 1)
- [ ] Dataset overview + data dictionary (Step 2)
- [ ] "EDA + Feature Engineering Report" with reproducible code and
      justifications (Step 3)
- [ ] Trained models, metrics, and model comparison; saved configs and model
      artifacts (Step 4)
- [ ] "Bias & Fairness Analysis" section in the final report (Step 5)
- [ ] Technical slide deck and business slide deck, 8–12 slides each
      recommended (Step 6)
- [ ] Public GitHub repo link with `src/`, `notebooks/`, `data/`, `models/`,
      README, `requirements.txt`, final report, reproducible code, and a clean
      commit history (Step 7)

Optional items, if attempted:

- [ ] Running app + deployment guide + demo media (Step 8)
- [ ] Generative AI usage documentation + code/examples + demo video (Step 9)

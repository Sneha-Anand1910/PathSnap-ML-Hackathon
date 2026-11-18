# 🗺️ PathSnap – Intelligent GPS Map Matching

**Transforming noisy GPS trajectories into meaningful road-network paths using Machine Learning.**

PathSnap is a machine learning-powered GPS map matching system designed to align raw, noisy GPS observations with the most likely paths on a digital road network.

GPS devices often produce inaccurate location readings due to signal interference, urban obstacles, and measurement errors. PathSnap aims to solve this problem by combining data preprocessing, feature engineering, and machine learning-based classification to identify the most probable road segments corresponding to a vehicle's actual journey.

---

## 🚀 Project Overview

Raw GPS trajectories do not always accurately represent the roads travelled by a vehicle.

PathSnap addresses this challenge by processing GPS observations and using machine learning techniques to determine the most likely corresponding road-network segments.

The project combines an ML pipeline with an interactive web dashboard to make GPS trajectory analysis and map matching easier to understand and visualize.

## ✨ Key Features

- **GPS Data Preprocessing:** Cleaning and preparing raw trajectory data.
- **Feature Engineering:** Extracting useful information from GPS observations and road-network data.
- **Machine Learning Models:** Exploring multiple classification algorithms for road-segment prediction.
- **Map Matching:** Mapping GPS observations to likely road-network paths.
- **Interactive Dashboard:** A light-themed web interface for exploring trips and route analysis.
- **Model Evaluation:** Comparing machine learning models using performance metrics.

## 🧠 Machine Learning Approach

PathSnap explores five machine learning algorithms:

| Algorithm | Purpose |
|---|---|
| Logistic Regression | Baseline classification |
| K-Nearest Neighbors (KNN) | Neighbour-based classification |
| Decision Tree | Rule-based classification |
| Random Forest | Ensemble classification |
| Gradient Boosting | Boosted ensemble classification |

The models are intended to be evaluated using metrics such as:

- Accuracy
- Precision
- Recall
- F1-score

The final model selection will be based on comparative evaluation results.

## 🖥️ Interactive Dashboard

PathSnap includes a React-based dashboard designed to provide an accessible interface for exploring the map matching pipeline.

### Dashboard Modules

| Module | Description |
|---|---|
| Dashboard | Overview of the project and pipeline |
| Upload Trip | Interface for selecting GPS and road-network files |
| Map Matching | Interactive map for visualizing GPS observations and routes |
| Results | Trip analysis and predicted road-segment results |
| Model Performance | Model comparison and evaluation dashboard |

*Note: Some dashboard visualizations currently use illustrative/demo data. Live ML predictions and backend integration are under development.*

## ⚙️ Technology Stack

**Frontend**
- React.js
- Vite
- Tailwind CSS
- Lucide React
- Leaflet / OpenStreetMap

**Machine Learning & Data Processing**
- Python
- Pandas
- NumPy
- Scikit-learn

**Development Tools**
- Git & GitHub
- Visual Studio Code
- Google Colab

## 📂 Project Structure

```text
PathSnap-ML-Hackathon/
│
├── frontend/
│   ├── src/
│   │   ├── App.jsx
│   │   ├── App.css
│   │   ├── index.css
│   │   ├── main.jsx
│   │   └── assets/
│   │
│   └── package.json
│
├── src/
│   └── preprocessing/
│
├── results/
│
├── README.md
└── .gitignore
```

*The structure above provides a high-level overview and may evolve as development progresses.*

## 💻 Getting Started

### Prerequisites

Make sure you have installed:

- Node.js and npm
- Python 3.x
- Git

### 1. Clone the repository

```bash
git clone <YOUR_GITHUB_REPOSITORY_URL>
```

### 2. Navigate to the project

```bash
cd PathSnap-ML-Hackathon
```

### 3. Set up the frontend

```bash
cd frontend
npm install
```

### 4. Start the development server

```bash
npm run dev
```

Open the local URL displayed in your terminal to explore the PathSnap dashboard.

## 🔄 Project Workflow

```text
Raw GPS Trajectory Data
          |
          v
   Data Preprocessing
          |
          v
   Feature Engineering
          |
          v
   Candidate Road Segments
          |
          v
   ML Model Prediction
          |
          v
    Map Matching
          |
          v
   Route Visualization
          |
          v
   Model Evaluation
```

## 🔮 Future Scope

- Integrating the trained ML models with the web dashboard.
- Enabling real-time GPS trajectory processing.
- Displaying actual predicted road segments and matched routes.
- Implementing dynamic model performance comparisons.
- Improving prediction accuracy and handling noisy GPS observations.
- Expanding support for larger road networks and trajectory datasets.

## 🎯 Project Objective

The ultimate goal of PathSnap is to bridge the gap between raw GPS data and meaningful geographical information through machine learning.

By combining intelligent data processing, predictive modelling, and interactive visualization, PathSnap aims to make GPS map matching more accessible, interpretable, and efficient.

---

**Built with 💙 by Team PathSnap**

*Machine Learning Hackathon Project | 2026*

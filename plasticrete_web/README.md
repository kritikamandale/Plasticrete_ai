# PlastiCrete Web Interface

Modern, interactive dashboard and civil engineering studio for **PlastiCrete.ai**, built with **React 19**, **TypeScript**, **Vite**, **Tailwind CSS v4**, and **Recharts**.

---

## 🚀 Features

- **Interactive Mix Studio:** Adjust 8 mix parameters (plastic type, replacement %, particle size, w/c ratio, additives, curing) with immediate visual feedback.
- **Real-Time Property Prediction:** View 7 mechanical/physical concrete properties with 90% confidence interval error bars.
- **Multi-Objective Optimizer:** Explore Pareto-optimal formulations balancing strength, embodied carbon, and cost.
- **Sustainability & Standards Compliance:** Live LCA carbon accounting (kg CO₂e/m³ saved) and automated compliance checking against Indian Standards (`IS 456`, `IS 2185`, `IS 15658`, `IS 383`).
- **Application Recommender:** Classifies structural vs. non-structural readiness and retrieves scientific literature analogues.
- **Model Explainability:** TreeSHAP contribution plots illustrating the impact of each ingredient on predicted performance.
- **Audit-Ready PDF Export:** One-click download of technical certification reports generated via the M5 engine.

---

## 🛠️ Development Setup

```bash
# Navigate to web directory
cd plasticrete_web

# Install dependencies
npm install

# Start Vite development server
npm run dev
```

The application will be accessible at `http://localhost:5173`.

### Build for Production
```bash
npm run build
npm run preview
```

---

## 🔌 API Connection

The frontend connects to the PlastiCrete FastAPI backend running by default at `http://localhost:8000`. You can configure the backend URL via environment variables in `.env`:

```env
VITE_API_BASE_URL=http://localhost:8000
```

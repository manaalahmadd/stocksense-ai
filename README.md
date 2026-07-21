# StockSense AI 🧠📦

> AI-powered inventory intelligence for retail store owners. Stop stockouts. Stop dead stock.

**Live Demo:** [stocksense-ai-frontend-gamma.vercel.app](https://stocksense-ai-frontend-gamma.vercel.app)  
**API:** [stocksense-ai-6enu.onrender.com](https://stocksense-ai-6enu.onrender.com)

---

## What It Does

StockSense AI connects to your Shopify store and tells you exactly what to reorder and when — using machine learning trained on your sales history.

Instead of showing you a chart, it says:

> *"USB Cable will run out in 4 days. Your supplier lead time is 3 days. Order 150 units NOW."*

---

## Features

- **ML Demand Forecasting** — Facebook Prophet model predicts daily demand per SKU for the next 30 days, accounting for weekly seasonality
- **AI Reorder Recommendations** — Plain-English alerts with urgency tiers (CRITICAL / WARNING / OK)
- **Shopify Integration** — OAuth-based connection, syncs products and inventory automatically
- **CSV Upload** — Import sales history from any source
- **AI Chat Agent** — Ask questions like "What should I stock before Diwali?" (powered by Claude API)
- **Razorpay Billing** — Subscription plans with payment verification
- **User Auth** — JWT-based registration and login via FastAPI-Users
- **Real-time Dashboard** — Next.js frontend showing live reorder status across all SKUs

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | FastAPI (Python 3.12) |
| Database | PostgreSQL (via SQLAlchemy) |
| ML Forecasting | Facebook Prophet |
| AI Agent | Anthropic Claude API |
| Frontend | Next.js 16 + Tailwind CSS |
| Payments | Razorpay |
| Auth | FastAPI-Users + JWT |
| Shopify | OAuth 2.0 + REST API |
| Deployment | Render (backend) + Vercel (frontend) |

---

## Project Structure

```
stocksense-ai/
├── api/
│   ├── main.py              # FastAPI app, all routes
│   ├── models.py            # SQLAlchemy models (Store, Product, Sale, Subscription)
│   ├── forecasting.py       # Prophet demand forecasting engine
│   ├── reorder.py           # Reorder recommendation logic
│   ├── agent.py             # Claude AI agent (mock + real mode)
│   ├── billing.py           # Razorpay order creation and verification
│   ├── shopify_integration.py # Shopify OAuth + product sync
│   ├── auth.py              # FastAPI-Users JWT authentication
│   ├── seed.py              # Development seed script
│   └── requirements.txt
├── frontend/
│   └── app/
│       ├── page.tsx         # Landing page
│       ├── dashboard/       # Protected inventory dashboard
│       ├── login/           # Login page
│       ├── register/        # Register page
│       └── pricing/         # Pricing page (Razorpay checkout)
└── .gitignore
```

---

## Local Development

### Prerequisites
- Python 3.10+
- Node.js 18+
- PostgreSQL (or SQLite for local dev)

### Backend

```bash
cd api
python -m venv venv
.\venv\Scripts\Activate.ps1  # Windows
pip install -r requirements.txt

# Create .env file
DATABASE_URL=sqlite:///./stocksense.db
RAZORPAY_KEY_ID=your_key
RAZORPAY_KEY_SECRET=your_secret
SHOPIFY_CLIENT_ID=your_client_id
SHOPIFY_CLIENT_SECRET=your_client_secret
ANTHROPIC_API_KEY=your_key  # optional, enables real Claude agent

uvicorn main:app --reload
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

### Seed test data

```bash
cd api
python seed.py
```

---

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| POST | `/auth/register` | Register new user |
| POST | `/auth/jwt/login` | Login, returns JWT |
| GET | `/api/v1/dashboard/{store_id}` | All products + reorder status |
| GET | `/api/v1/forecasts/{product_id}` | 30-day demand forecast |
| GET | `/api/v1/reorder/{product_id}` | Reorder recommendation |
| POST | `/api/v1/agent/{store_id}` | Chat with AI agent |
| POST | `/api/v1/upload/{store_id}` | Upload sales CSV |
| GET | `/api/v1/shopify/install` | Start Shopify OAuth |
| POST | `/api/v1/shopify/sync/{store_id}` | Sync Shopify products |
| POST | `/api/v1/billing/create-order` | Create Razorpay order |
| POST | `/api/v1/billing/verify-payment` | Verify payment + activate subscription |

Full interactive docs: [stocksense-ai-6enu.onrender.com/docs](https://stocksense-ai-6enu.onrender.com/docs)

---

## How the Forecasting Works

1. Pull last 90 days of sales history per SKU from PostgreSQL
2. Fit a Facebook Prophet model with weekly seasonality
3. Predict daily demand for next 30 days with confidence intervals
4. Walk forward day-by-day depleting stock to find stockout date
5. Compare stockout date vs supplier lead time to determine urgency
6. Generate plain-English recommendation with suggested order quantity

**Cold start fallback:** If < 14 days of data, uses simple moving average.

---

## Environment Variables

| Variable | Description |
|---|---|
| `DATABASE_URL` | PostgreSQL connection string |
| `RAZORPAY_KEY_ID` | Razorpay API key (test or live) |
| `RAZORPAY_KEY_SECRET` | Razorpay secret key |
| `SHOPIFY_CLIENT_ID` | Shopify app client ID |
| `SHOPIFY_CLIENT_SECRET` | Shopify app client secret |
| `ANTHROPIC_API_KEY` | Optional — enables real Claude agent |
| `SECRET_KEY` | JWT signing secret |

---

## Pricing

| Plan | Price | SKUs |
|---|---|---|
| Starter | ₹4,900/mo | Up to 500 |
| Growth | ₹14,900/mo | Up to 5,000 |

---

## Built By

**Manaal Ahmad** — 3rd year B.Tech CS student at ADGITM, Delhi (IP University)

Built this as a side project while preparing for CAT and solving LeetCode.

- GitHub: [@manaalahmadd](https://github.com/manaalahmadd)
- LinkedIn: [Manaal Ahmad](https://linkedin.com/in/manaalahmadd)

---

## License

MIT

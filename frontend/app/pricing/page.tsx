"use client";

import { useState, useEffect } from "react";

const API = "https://stocksense-ai-6enu.onrender.com";

declare global {
  interface Window {
    Razorpay: any;
  }
}

export default function PricingPage() {
  const [loading, setLoading] = useState<string | null>(null);
  const [userEmail, setUserEmail] = useState<string>("");

  useEffect(() => {
    const script = document.createElement("script");
    script.src = "https://checkout.razorpay.com/v1/checkout.js";
    script.async = true;
    document.body.appendChild(script);

    const token = localStorage.getItem("token");
    if (!token) {
      window.location.href = "/login";
      return;
    }

    const email = localStorage.getItem("userEmail") || "";
    setUserEmail(email);
  }, []);

  async function handleSubscribe(plan: string) {
    if (!userEmail) {
      alert("Could not get your email. Please log out and log in again.");
      return;
    }

    setLoading(plan);

    try {
      const res = await fetch(`${API}/api/v1/billing/create-order`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ plan, email: userEmail }),
      });

      const order = await res.json();

      const options = {
        key: order.key_id,
        amount: order.amount,
        currency: order.currency,
        name: "StockSense AI",
        description: order.plan_name,
        order_id: order.order_id,
        handler: async function (response: any) {
          const verify = await fetch(`${API}/api/v1/billing/verify-payment`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              razorpay_payment_id: response.razorpay_payment_id,
              razorpay_order_id: response.razorpay_order_id,
              razorpay_signature: response.razorpay_signature,
              email: userEmail,
              plan,
            }),
          });

          const result = await verify.json();
          if (result.status === "success") {
            window.location.href = "/?subscribed=true";
          }
        },
        prefill: { email: userEmail },
        theme: { color: "#2563eb" },
      };

      const rzp = new window.Razorpay(options);
      rzp.open();
    } catch (err) {
      alert("Something went wrong. Please try again.");
    } finally {
      setLoading(null);
    }
  }

  const plans = [
    {
      id: "starter",
      name: "Starter",
      price: "₹4,900",
      period: "/month",
      description: "Perfect for small stores",
      features: [
        "Up to 500 SKUs",
        "AI reorder recommendations",
        "CSV data upload",
        "Weekly demand forecasts",
        "Email support",
      ],
    },
    {
      id: "growth",
      name: "Growth",
      price: "₹14,900",
      period: "/month",
      description: "For growing businesses",
      features: [
        "Up to 5,000 SKUs",
        "Real-time reorder alerts",
        "Chat with AI agent",
        "Daily demand forecasts",
        "Priority support",
      ],
      highlighted: true,
    },
  ];

  return (
    <main className="min-h-screen bg-gray-50 py-16 px-4">
      <div className="max-w-4xl mx-auto">
        <div className="text-center mb-12">
          <h1 className="text-3xl font-bold text-gray-900 mb-3">
            Simple, transparent pricing
          </h1>
          <p className="text-gray-500">
            Stop stockouts. Stop dead stock. Start with a 14-day free trial.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
          {plans.map((plan) => (
            <div
              key={plan.id}
              className={`bg-white rounded-xl border p-8 shadow-sm ${
                (plan as any).highlighted
                  ? "border-blue-500 ring-2 ring-blue-500"
                  : "border-gray-200"
              }`}
            >
              {(plan as any).highlighted && (
                <div className="text-xs font-semibold text-blue-600 uppercase tracking-wide mb-3">
                  Most Popular
                </div>
              )}
              <h2 className="text-xl font-bold text-gray-900">{plan.name}</h2>
              <p className="text-gray-500 text-sm mt-1">{plan.description}</p>
              <div className="mt-4 mb-6">
                <span className="text-4xl font-bold text-gray-900">
                  {plan.price}
                </span>
                <span className="text-gray-500">{plan.period}</span>
              </div>

              <ul className="space-y-3 mb-8">
                {plan.features.map((feature) => (
                  <li key={feature} className="flex items-center gap-2 text-sm text-gray-700">
                    <span className="text-green-500 font-bold">✓</span>
                    {feature}
                  </li>
                ))}
              </ul>

              <button
                onClick={() => handleSubscribe(plan.id)}
                disabled={loading === plan.id}
                className={`w-full py-3 rounded-lg text-sm font-medium transition ${
                  (plan as any).highlighted
                    ? "bg-blue-600 text-white hover:bg-blue-700"
                    : "bg-gray-900 text-white hover:bg-gray-800"
                } disabled:opacity-50`}
              >
                {loading === plan.id ? "Processing..." : "Get started"}
              </button>
            </div>
          ))}
        </div>

        <p className="text-center text-gray-400 text-sm mt-8">
          <a href="/" className="hover:text-gray-600">← Back to dashboard</a>
        </p>
      </div>
    </main>
  );
}
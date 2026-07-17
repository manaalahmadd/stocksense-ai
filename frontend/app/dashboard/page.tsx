"use client";

import { useEffect, useState } from "react";

type ReorderInfo = {
  product_id: number;
  product_name: string;
  current_stock: number;
  avg_daily_demand: number;
  supplier_lead_time_days: number;
  days_until_stockout: number | null;
  needs_reorder: boolean;
  urgency: "critical" | "warning" | "ok";
  suggested_order_qty: number;
  reasoning: string;
};

type DashboardResponse = {
  store_id: number;
  products: ReorderInfo[];
};

type ChatMessage = {
  role: "user" | "agent";
  text: string;
};

const urgencyStyles: Record<string, string> = {
  critical: "bg-red-100 text-red-800 border-red-300",
  warning: "bg-yellow-100 text-yellow-800 border-yellow-300",
  ok: "bg-green-100 text-green-800 border-green-300",
};

const SHOPIFY_INSTALL_URL = `https://stocksense-test-yaeryvw1.myshopify.com/admin/oauth/authorize?client_id=6e10cff2860a5814ef9b350b4a0aacdf&scope=read_orders,read_products,read_inventory&redirect_uri=https://stocksense-ai-6enu.onrender.com/api/v1/shopify/callback`;

export default function Dashboard() {
  const [data, setData] = useState<DashboardResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [sending, setSending] = useState(false);

  useEffect(() => {
    const token = localStorage.getItem("token");
    if (!token) {
      window.location.href = "/login";
      return;
    }

    fetch("https://stocksense-ai-6enu.onrender.com/api/v1/dashboard/2")
      .then((res) => {
        if (!res.ok) throw new Error("Failed to fetch dashboard data");
        return res.json();
      })
      .then((json) => {
        setData(json);
        setLoading(false);
      })
      .catch((err) => {
        setError(err.message);
        setLoading(false);
      });
  }, []);

  async function sendMessage() {
    if (!input.trim() || sending) return;
    const userMessage: ChatMessage = { role: "user", text: input };
    setMessages((prev) => [...prev, userMessage]);
    setInput("");
    setSending(true);
    try {
      const res = await fetch("https://stocksense-ai-6enu.onrender.com/api/v1/agent/2", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question: userMessage.text }),
      });
      const json = await res.json();
      setMessages((prev) => [...prev, { role: "agent", text: json.answer }]);
    } catch {
      setMessages((prev) => [...prev, { role: "agent", text: "Error: could not reach the agent." }]);
    } finally {
      setSending(false);
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <p className="text-gray-500">Loading dashboard...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <p className="text-red-500">Error: {error}. Is your backend running?</p>
      </div>
    );
  }

  return (
    <main className="min-h-screen bg-gray-50 p-8">
      <div className="max-w-5xl mx-auto">
        <h1 className="text-2xl font-bold text-gray-900 mb-1">StockSense AI</h1>
        <div className="flex items-center justify-between mb-8">
          <p className="text-gray-500">Inventory overview — Demo Mart</p>
          <div className="flex items-center gap-4">
            <a href="/pricing" className="text-sm text-blue-600 hover:underline font-medium">
              Upgrade plan
            </a>
            <button
              onClick={() => {
                localStorage.removeItem("token");
                window.location.href = "/login";
              }}
              className="text-sm text-gray-500 hover:text-gray-700"
            >
              Sign out
            </button>
          </div>
        </div>

        <div className="space-y-4 mb-10">
          {!data?.products?.length && (
            <div className="bg-white border rounded-lg p-5 text-gray-500 text-sm">
              No products yet. Upload a CSV to get started.
            </div>
          )}
          {data?.products?.map((product) => (
            <div key={product.product_id} className="bg-white border rounded-lg p-5 shadow-sm">
              <div className="flex items-start justify-between">
                <div>
                  <h2 className="text-lg font-semibold text-gray-900">{product.product_name}</h2>
                  <p className="text-sm text-gray-500">
                    Current stock: {product.current_stock} units · Avg demand: {product.avg_daily_demand}/day
                  </p>
                </div>
                <span className={`text-xs font-medium px-3 py-1 rounded-full border ${urgencyStyles[product.urgency]}`}>
                  {product.urgency.toUpperCase()}
                </span>
              </div>
              <p className="text-gray-700 mt-3 text-sm">{product.reasoning}</p>
              {product.needs_reorder && (
                <div className="mt-3 bg-blue-50 border border-blue-200 rounded-md px-4 py-2 text-sm text-blue-800">
                  Suggested order quantity: <strong>{product.suggested_order_qty} units</strong>
                </div>
              )}
            </div>
          ))}
        </div>

        <div className="bg-white border rounded-lg p-5 shadow-sm mb-6">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="font-semibold text-gray-900">Connect your Shopify store</h2>
              <p className="text-sm text-gray-500 mt-1">
                Automatically sync your sales data from Shopify in real time.
              </p>
            </div>
            <a href={SHOPIFY_INSTALL_URL} className="bg-green-600 text-white text-sm font-medium px-4 py-2 rounded-md hover:bg-green-700">
              Connect Shopify
            </a>
          </div>
        </div>

        <div className="bg-white border rounded-lg shadow-sm">
          <div className="px-5 py-4 border-b">
            <h2 className="font-semibold text-gray-900">Ask your inventory agent</h2>
            <p className="text-xs text-gray-500">e.g. &quot;What should I reorder this week?&quot;</p>
          </div>
          <div className="p-5 space-y-3 max-h-80 overflow-y-auto">
            {messages.length === 0 && (
              <p className="text-sm text-gray-400">No messages yet — ask a question below.</p>
            )}
            {messages.map((msg, i) => (
              <div key={i} className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}>
                <div className={`max-w-[80%] rounded-lg px-4 py-2 text-sm ${msg.role === "user" ? "bg-blue-600 text-white" : "bg-gray-100 text-gray-800"}`}>
                  {msg.text}
                </div>
              </div>
            ))}
            {sending && (
              <div className="flex justify-start">
                <div className="bg-gray-100 text-gray-500 text-sm rounded-lg px-4 py-2">Thinking...</div>
              </div>
            )}
          </div>
          <div className="p-4 border-t flex gap-2">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && sendMessage()}
              placeholder="Ask about your inventory..."
              className="flex-1 border rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
            <button
              onClick={sendMessage}
              disabled={sending}
              className="bg-blue-600 text-white text-sm px-4 py-2 rounded-md hover:bg-blue-700 disabled:opacity-50"
            >
              Send
            </button>
          </div>
        </div>
      </div>
    </main>
  );
}
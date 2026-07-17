"use client";

export default function LandingPage() {
  return (
    <main className="min-h-screen bg-white">
      {/* Nav */}
      <nav className="flex items-center justify-between px-8 py-4 border-b">
        <span className="text-xl font-bold text-gray-900">StockSense AI</span>
        <div className="flex items-center gap-4">
          <a href="/pricing" className="text-sm text-gray-600 hover:text-gray-900">Pricing</a>
          <a href="/login" className="text-sm text-gray-600 hover:text-gray-900">Sign in</a>
          <a href="/register" className="bg-blue-600 text-white text-sm font-medium px-4 py-2 rounded-md hover:bg-blue-700">
            Get started free
          </a>
        </div>
      </nav>

      {/* Hero */}
      <section className="max-w-4xl mx-auto px-8 py-24 text-center">
        <div className="inline-block bg-blue-50 text-blue-700 text-xs font-semibold px-3 py-1 rounded-full mb-6">
          AI-Powered Inventory Intelligence
        </div>
        <h1 className="text-5xl font-bold text-gray-900 leading-tight mb-6">
          Stop stockouts.<br />Stop dead stock.
        </h1>
        <p className="text-xl text-gray-500 mb-10 max-w-2xl mx-auto">
          StockSense AI tells store owners exactly what to reorder and when — using machine learning trained on your sales data.
        </p>
        <div className="flex items-center justify-center gap-4">
          <a href="/register" className="bg-blue-600 text-white font-medium px-8 py-3 rounded-lg hover:bg-blue-700 text-lg">
            Start free trial
          </a>
          <a href="/pricing" className="text-gray-600 font-medium px-8 py-3 rounded-lg border hover:bg-gray-50 text-lg">
            See pricing
          </a>
        </div>
        <p className="text-sm text-gray-400 mt-4">No credit card required · 14-day free trial</p>
      </section>

      {/* Features */}
      <section className="bg-gray-50 py-20">
        <div className="max-w-5xl mx-auto px-8">
          <h2 className="text-3xl font-bold text-gray-900 text-center mb-12">
            Everything you need to optimize inventory
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            {[
              {
                icon: "📈",
                title: "Demand Forecasting",
                desc: "Prophet ML model predicts your daily demand for the next 30 days, accounting for weekly patterns and seasonality.",
              },
              {
                icon: "🤖",
                title: "AI Reorder Alerts",
                desc: "Get plain-English recommendations: 'You'll run out of Item X in 4 days. Order 120 units now.'",
              },
              {
                icon: "🛍️",
                title: "Shopify Integration",
                desc: "Connect your Shopify store in one click. Sales data syncs automatically — no CSV uploads needed.",
              },
              {
                icon: "⚡",
                title: "Real-time Dashboard",
                desc: "See all your SKUs, current stock levels, and urgency status at a glance. Critical items highlighted instantly.",
              },
              {
                icon: "💬",
                title: "Chat with AI Agent",
                desc: "Ask questions like 'What should I stock up on before Diwali?' and get data-backed answers.",
              },
              {
                icon: "📊",
                title: "Multi-product Support",
                desc: "Track hundreds of SKUs simultaneously. Each product gets its own forecast and reorder calculation.",
              },
            ].map((feature) => (
              <div key={feature.title} className="bg-white rounded-xl p-6 shadow-sm border">
                <div className="text-3xl mb-4">{feature.icon}</div>
                <h3 className="font-semibold text-gray-900 mb-2">{feature.title}</h3>
                <p className="text-gray-500 text-sm">{feature.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Social proof */}
      <section className="py-20 max-w-4xl mx-auto px-8 text-center">
        <h2 className="text-3xl font-bold text-gray-900 mb-4">
          Built for Indian retail store owners
        </h2>
        <p className="text-gray-500 text-lg mb-12">
          Whether you run a Shopify store or a local shop — StockSense AI works with your data.
        </p>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          {[
            { stat: "30 days", label: "Demand forecast horizon" },
            { stat: "< 1 min", label: "Time to connect Shopify" },
            { stat: "₹0", label: "To get started" },
          ].map((item) => (
            <div key={item.label} className="text-center">
              <div className="text-4xl font-bold text-blue-600 mb-2">{item.stat}</div>
              <div className="text-gray-500 text-sm">{item.label}</div>
            </div>
          ))}
        </div>
      </section>

      {/* CTA */}
      <section className="bg-blue-600 py-20 text-center">
        <h2 className="text-3xl font-bold text-white mb-4">
          Ready to stop guessing your inventory?
        </h2>
        <p className="text-blue-100 mb-8 text-lg">
          Join store owners using AI to make smarter reorder decisions.
        </p>
        <a href="/register" className="bg-white text-blue-600 font-semibold px-8 py-3 rounded-lg hover:bg-blue-50 text-lg">
          Start your free trial
        </a>
      </section>

      {/* Footer */}
      <footer className="py-8 text-center text-gray-400 text-sm border-t">
        © 2026 StockSense AI · Built for Indian retailers
      </footer>
    </main>
  );
}
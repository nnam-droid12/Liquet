import React, { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'

// ── Animated counter ───────────────────────────────────────────────────────────

function Counter({ target, duration = 1400, suffix = '', prefix = '' }) {
  const [value, setValue] = useState(0)
  useEffect(() => {
    if (!target) return
    const start = Date.now()
    const tick = () => {
      const elapsed = Date.now() - start
      const progress = Math.min(elapsed / duration, 1)
      const eased = 1 - Math.pow(1 - progress, 3)
      setValue(Math.round(eased * target))
      if (progress < 1) requestAnimationFrame(tick)
    }
    requestAnimationFrame(tick)
  }, [target, duration])
  return <span>{prefix}{value.toLocaleString()}{suffix}</span>
}

// ── Gate pill ─────────────────────────────────────────────────────────────────

function GatePill({ type }) {
  if (type === 'LIQUET') {
    return (
      <div className="flex items-center gap-2 bg-emerald-500/10 border border-emerald-500/30 rounded-full px-4 py-2">
        <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
        <span className="text-emerald-300 font-bold text-sm tracking-widest">LIQUET</span>
        <span className="text-emerald-400/60 text-xs">it is clear</span>
      </div>
    )
  }
  return (
    <div className="flex items-center gap-2 bg-amber-500/10 border border-amber-500/30 rounded-full px-4 py-2">
      <span className="w-2 h-2 rounded-full bg-amber-400" />
      <span className="text-amber-300 font-bold text-sm tracking-widest">NON LIQUET</span>
      <span className="text-amber-400/60 text-xs">it is not clear</span>
    </div>
  )
}

// ── Feature card ──────────────────────────────────────────────────────────────

function FeatureCard({ icon, title, subtitle, description, accent }) {
  const accentMap = {
    purple: 'border-purple-500/20 hover:border-purple-400/40',
    blue:   'border-blue-500/20 hover:border-blue-400/40',
    rose:   'border-rose-500/20 hover:border-rose-400/40',
  }
  const iconBg = {
    purple: 'bg-purple-500/10 text-purple-300',
    blue:   'bg-blue-500/10 text-blue-300',
    rose:   'bg-rose-500/10 text-rose-300',
  }
  const tagColor = {
    purple: 'bg-purple-500/15 text-purple-300 border-purple-500/25',
    blue:   'bg-blue-500/15 text-blue-300 border-blue-500/25',
    rose:   'bg-rose-500/15 text-rose-300 border-rose-500/25',
  }
  return (
    <div className={`bg-slate-800/50 backdrop-blur border rounded-2xl p-6 transition-all duration-300 ${accentMap[accent]}`}>
      <div className={`w-12 h-12 rounded-xl flex items-center justify-center text-2xl mb-4 ${iconBg[accent]}`}>
        {icon}
      </div>
      <div className={`inline-block text-xs font-mono px-2 py-0.5 rounded border mb-3 ${tagColor[accent]}`}>
        {subtitle}
      </div>
      <h3 className="text-white font-bold text-lg mb-2">{title}</h3>
      <p className="text-slate-400 text-sm leading-relaxed">{description}</p>
    </div>
  )
}

// ── Stat card ─────────────────────────────────────────────────────────────────

function StatCard({ label, value, suffix, prefix, description }) {
  return (
    <div className="text-center">
      <div className="text-4xl font-black text-white mb-1">
        <Counter target={value} suffix={suffix} prefix={prefix} />
      </div>
      <div className="text-blue-300 font-medium text-sm mb-1">{label}</div>
      {description && (
        <div className="text-slate-500 text-xs">{description}</div>
      )}
    </div>
  )
}

// ── Main ──────────────────────────────────────────────────────────────────────

export default function Landing() {
  const [stats, setStats] = useState(null)

  useEffect(() => {
    fetch('/api/stats')
      .then(r => r.ok ? r.json() : null)
      .then(data => setStats(data))
      .catch(() => {})
  }, [])

  const autoRate = stats ? Math.round(stats.auto_resolution_rate * 100) : 0
  const avgConf = stats ? Math.round(stats.avg_confidence * 100) : 0

  return (
    <div className="min-h-screen bg-slate-950 text-white">

      {/* ── Nav ──────────────────────────────────────────────────────────── */}
      <nav className="fixed top-0 inset-x-0 z-50 border-b border-white/5 bg-slate-950/80 backdrop-blur-xl">
        <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <span className="font-black text-2xl tracking-tight bg-gradient-to-r from-blue-400 to-cyan-300 bg-clip-text text-transparent">
              LIQUET
            </span>
            <span className="text-slate-500 text-xs font-mono hidden sm:block">
              Autonomous Dispute Resolution
            </span>
          </div>
          <Link
            to="/dashboard"
            className="bg-blue-600 hover:bg-blue-500 text-white text-sm font-semibold px-4 py-2 rounded-lg transition-colors"
          >
            Enter Platform →
          </Link>
        </div>
      </nav>

      {/* ── Hero ─────────────────────────────────────────────────────────── */}
      <section className="relative pt-32 pb-24 px-6 overflow-hidden">
        {/* Background glow */}
        <div className="absolute inset-0 overflow-hidden pointer-events-none">
          <div className="absolute top-1/3 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[800px] h-[400px] bg-blue-600/8 rounded-full blur-3xl" />
          <div className="absolute top-1/3 left-1/3 w-[400px] h-[400px] bg-purple-600/6 rounded-full blur-3xl" />
        </div>

        <div className="relative max-w-5xl mx-auto text-center">
          {/* Badge */}
          <div className="inline-flex items-center gap-2 bg-blue-500/10 border border-blue-500/20 rounded-full px-4 py-1.5 text-blue-300 text-xs font-mono mb-8">
            <span className="w-1.5 h-1.5 rounded-full bg-blue-400 animate-pulse" />
            QwenCloud Global AI Hackathon · Alibaba Cloud
          </div>

          {/* Title */}
          <h1 className="text-6xl sm:text-8xl font-black tracking-tight mb-6 leading-none">
            <span className="bg-gradient-to-r from-white via-blue-100 to-blue-300 bg-clip-text text-transparent">
              LIQUET
            </span>
          </h1>

          <p className="text-xl sm:text-2xl text-slate-300 font-medium mb-4 max-w-2xl mx-auto">
            The first AI arbitrator that knows when <em className="text-blue-300 not-italic font-bold">not</em> to decide.
          </p>

          <p className="text-slate-500 text-base mb-12 max-w-xl mx-auto leading-relaxed">
            Roman jurors declared <em>non liquet</em> — "it is not clear" — when evidence was insufficient
            for a just verdict. Liquet applies that same standard to marketplace disputes at scale.
          </p>

          {/* Gate pills */}
          <div className="flex items-center justify-center gap-4 mb-12 flex-wrap">
            <GatePill type="LIQUET" />
            <div className="text-slate-600 text-sm font-mono">vs</div>
            <GatePill type="NON_LIQUET" />
          </div>

          <div className="flex items-center justify-center gap-4 flex-wrap">
            <Link
              to="/dashboard"
              className="bg-blue-600 hover:bg-blue-500 text-white font-bold px-8 py-3.5 rounded-xl transition-colors text-base"
            >
              Enter the Platform
            </Link>
            <Link
              to="/new"
              className="border border-white/15 hover:border-white/30 text-slate-300 hover:text-white font-semibold px-8 py-3.5 rounded-xl transition-colors text-base"
            >
              Submit a Dispute
            </Link>
          </div>
        </div>
      </section>

      {/* ── Live stats ────────────────────────────────────────────────────── */}
      {stats && (
        <section className="py-16 px-6 border-y border-white/5 bg-white/2">
          <div className="max-w-4xl mx-auto">
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-8">
              <StatCard
                label="Disputes Processed"
                value={stats.total_disputes}
                description="since platform launch"
              />
              <StatCard
                label="Auto-Resolution Rate"
                value={autoRate}
                suffix="%"
                description="resolved without human review"
              />
              <StatCard
                label="Avg Confidence"
                value={avgConf}
                suffix="%"
                description="across all verdicts"
              />
              <StatCard
                label="Cases Escalated"
                value={stats.escalated}
                description="correctly sent to humans"
              />
            </div>
          </div>
        </section>
      )}

      {/* ── How it works ──────────────────────────────────────────────────── */}
      <section className="py-20 px-6">
        <div className="max-w-5xl mx-auto">
          <div className="text-center mb-16">
            <div className="text-blue-400 font-mono text-xs tracking-widest uppercase mb-3">
              The Decision Engine
            </div>
            <h2 className="text-4xl font-black text-white mb-4">
              Evidence in. Verdict out. Or not.
            </h2>
            <p className="text-slate-400 max-w-xl mx-auto">
              Liquet doesn't just auto-resolve disputes — it knows exactly when the evidence
              isn't strong enough to act, and says so.
            </p>
          </div>

          {/* Pipeline steps */}
          <div className="grid sm:grid-cols-4 gap-4">
            {[
              { step: '01', title: 'Evidence Intake', desc: 'Order records, carrier scans, photos, messages — all ingested via MCP tool calls', icon: '📂' },
              { step: '02', title: 'Multi-Pass Adjudication', desc: '3× shuffled verdict runs + adversarial skeptic challenge before any confidence score is accepted', icon: '⚖️' },
              { step: '03', title: 'LIQUET Gate', desc: 'Confidence ≥ threshold AND order value in range AND no hard contradictions → autonomous resolution', icon: '🔐' },
              { step: '04', title: 'Execute or Escalate', desc: 'LIQUET: refund/replace/deny issued instantly. NON LIQUET: full brief sent to human reviewer', icon: '✓' },
            ].map(({ step, title, desc, icon }) => (
              <div key={step} className="relative">
                <div className="bg-slate-800/40 border border-white/5 rounded-xl p-5">
                  <div className="text-3xl mb-3">{icon}</div>
                  <div className="text-blue-400 font-mono text-xs mb-2">{step}</div>
                  <div className="text-white font-bold text-sm mb-2">{title}</div>
                  <div className="text-slate-500 text-xs leading-relaxed">{desc}</div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── Three innovative features ─────────────────────────────────────── */}
      <section className="py-20 px-6 bg-gradient-to-b from-slate-950 to-slate-900">
        <div className="max-w-5xl mx-auto">
          <div className="text-center mb-16">
            <div className="text-purple-400 font-mono text-xs tracking-widest uppercase mb-3">
              Novel AI Techniques
            </div>
            <h2 className="text-4xl font-black text-white mb-4">
              Three features no dispute system has
            </h2>
            <p className="text-slate-400 max-w-xl mx-auto">
              Beyond standard LLM adjudication — mechanisms that catch overconfidence,
              circular reasoning, and pattern-based fraud.
            </p>
          </div>

          <div className="grid md:grid-cols-3 gap-6">
            <FeatureCard
              accent="purple"
              icon="👻"
              subtitle="Cross-dispute intelligence"
              title="Ghost Cases"
              description="Before each adjudication, Liquet queries all past disputes for the same seller and claim type. Recurring patterns are injected as synthetic evidence — giving the AI memory of who it's dealt with before."
            />
            <FeatureCard
              accent="blue"
              icon="🎲"
              subtitle="Variance-weighted confidence"
              title="Verdict Stability Scoring"
              description="The adjudicator runs 3× with evidence in shuffled orders. If the verdict changes across runs, the raw confidence was overestimated. Effective confidence = raw × stability factor. Unstable verdicts are blocked."
            />
            <FeatureCard
              accent="rose"
              icon="🔥"
              subtitle="Adversarial self-challenge"
              title="The Skeptic Pass"
              description="After reaching a verdict, a second LLM pass argues the opposite: finds the weakest evidence, the alternative reading. The adjudicator must rebut it. If it can't (rebuttal strength < 55%), the case is escalated."
            />
          </div>
        </div>
      </section>

      {/* ── MCP Architecture ──────────────────────────────────────────────── */}
      <section className="py-20 px-6">
        <div className="max-w-5xl mx-auto">
          <div className="text-center mb-16">
            <div className="text-cyan-400 font-mono text-xs tracking-widest uppercase mb-3">
              Technical Architecture
            </div>
            <h2 className="text-4xl font-black text-white mb-4">
              7 MCP tool servers. 2 Qwen models.
            </h2>
          </div>

          <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
            {[
              { name: 'order_service', desc: 'Purchase records & pricing' },
              { name: 'logistics_service', desc: 'Carrier scans & delivery' },
              { name: 'listing_service', desc: 'Product descriptions' },
              { name: 'comms_service', desc: 'Buyer–seller messages' },
              { name: 'vision_intake', desc: 'Photo evidence via qwen-vl-plus' },
              { name: 'policy_engine', desc: 'Platform rules & clauses' },
              { name: 'resolution_service', desc: 'Refund & replacement execution' },
            ].map(t => (
              <div key={t.name} className="bg-slate-800/30 border border-white/5 rounded-lg p-4">
                <div className="text-cyan-300 font-mono text-xs mb-1">{t.name}</div>
                <div className="text-slate-500 text-xs">{t.desc}</div>
              </div>
            ))}
            <div className="bg-blue-600/10 border border-blue-500/20 rounded-lg p-4">
              <div className="text-blue-300 font-mono text-xs mb-1">FastMCP (in-process)</div>
              <div className="text-slate-500 text-xs">Zero-latency, no network hop</div>
            </div>
          </div>

          <div className="flex items-center justify-center gap-6 text-sm text-slate-500 flex-wrap">
            <span className="flex items-center gap-1.5"><span className="w-2 h-2 rounded-full bg-blue-400" />qwen-plus (reasoning)</span>
            <span className="flex items-center gap-1.5"><span className="w-2 h-2 rounded-full bg-purple-400" />qwen-vl-plus (vision)</span>
            <span className="flex items-center gap-1.5"><span className="w-2 h-2 rounded-full bg-cyan-400" />FastAPI + SQLAlchemy</span>
            <span className="flex items-center gap-1.5"><span className="w-2 h-2 rounded-full bg-green-400" />React + Vite + Tailwind</span>
            <span className="flex items-center gap-1.5"><span className="w-2 h-2 rounded-full bg-orange-400" />Alibaba Cloud ECS (Singapore)</span>
          </div>
        </div>
      </section>

      {/* ── CTA ───────────────────────────────────────────────────────────── */}
      <section className="py-24 px-6">
        <div className="max-w-2xl mx-auto text-center">
          <div className="bg-gradient-to-b from-slate-800/60 to-slate-800/30 border border-white/8 rounded-3xl p-12">
            <div className="text-5xl mb-6">⚖️</div>
            <h2 className="text-3xl font-black text-white mb-4">
              See it adjudicate
            </h2>
            <p className="text-slate-400 mb-8">
              Submit a real dispute and watch the AI gather evidence, challenge its own verdict,
              check for seller history, and decide — or admit it can't.
            </p>
            <div className="flex items-center justify-center gap-4 flex-wrap">
              <Link
                to="/new"
                className="bg-blue-600 hover:bg-blue-500 text-white font-bold px-8 py-3.5 rounded-xl transition-colors"
              >
                Submit a Dispute
              </Link>
              <Link
                to="/dashboard"
                className="border border-white/15 hover:border-white/30 text-slate-300 hover:text-white font-semibold px-8 py-3.5 rounded-xl transition-colors"
              >
                View Dashboard
              </Link>
            </div>
          </div>
        </div>
      </section>

      {/* ── Footer ────────────────────────────────────────────────────────── */}
      <footer className="border-t border-white/5 py-8 px-6 text-center text-slate-600 text-xs">
        <div className="mb-2 font-mono">
          <em>liquet</em> (Latin) — "it is clear" &nbsp;·&nbsp; <em>non liquet</em> — "it is not clear"
        </div>
        <div>
          Liquet · QwenCloud Global AI Hackathon · Built on Alibaba Cloud QwenCloud
        </div>
      </footer>
    </div>
  )
}

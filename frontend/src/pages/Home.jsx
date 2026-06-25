import { useNavigate } from 'react-router-dom'
import { useAssessment } from '../context/AssessmentContext'
import { Zap, Building2, Cable, MapPin, BarChart3, ArrowRight, BookOpen } from 'lucide-react'

const STEPS = [
  { icon: Building2, label: 'Building',   desc: 'Geometry, location, LPS, materials',    to: '/building' },
  { icon: Cable,     label: 'Lines',      desc: 'Power & telecom service lines',          to: '/lines' },
  { icon: MapPin,    label: 'Risk Zones', desc: 'Zone-by-zone exposure & loss data',      to: '/zones' },
  { icon: BarChart3, label: 'Results',    desc: 'Risk, frequency & recommendations',      to: '/results' },
]

export default function Home() {
  const navigate = useNavigate()
  const { readiness } = useAssessment()

  return (
    <div>
      {/* Hero */}
      <div className="relative overflow-hidden rounded-3xl bg-gradient-to-br from-brand-600 via-brand-500 to-brand-300 p-10 mb-10 text-white shadow-lg">
        <div className="absolute top-0 right-0 w-64 h-64 bg-white/5 rounded-full -translate-y-1/2 translate-x-1/4" />
        <div className="absolute bottom-0 left-0 w-48 h-48 bg-white/5 rounded-full translate-y-1/3 -translate-x-1/4" />
        <div className="relative z-10">
          <div className="flex items-center gap-3 mb-5">
            <div className="w-12 h-12 bg-white/20 backdrop-blur rounded-2xl flex items-center justify-center">
              <Zap size={24} className="text-white" />
            </div>
            <div>
              <h1 className="text-3xl font-bold tracking-tight">LRAT</h1>
              <p className="text-brand-100 text-sm">Lightning Risk Assessment Tool</p>
            </div>
          </div>
          <p className="text-white/90 text-base max-w-lg leading-relaxed mb-7">
            A structured, IEC-based tool for assessing lightning risk, frequency of damage,
            and environmental consequences for buildings. Based on <strong>MS IEC 62305-2:2024</strong>.
          </p>
          <button
            onClick={() => navigate('/building')}
            className="flex items-center gap-2 bg-white text-brand-500 font-semibold px-6 py-3 rounded-xl hover:bg-brand-50 transition-all shadow-md"
          >
            Start New Assessment <ArrowRight size={16} />
          </button>
        </div>
      </div>

      {/* Workflow */}
      <h2 className="text-lg font-semibold text-slate-700 mb-4">Assessment Workflow</h2>
      <div className="grid grid-cols-2 gap-4 mb-10">
        {STEPS.map(({ icon: Icon, label, desc, to }, i) => {
          const done = readiness[label.toLowerCase().replace(' ', '')] || readiness[to.slice(1)]
          return (
            <button
              key={to}
              onClick={() => navigate(to)}
              className="card card-hover text-left flex items-start gap-4 group cursor-pointer"
            >
              <div className="w-10 h-10 bg-brand-50 rounded-xl flex items-center justify-center shrink-0 group-hover:bg-brand-100 transition-colors">
                <Icon size={18} className="text-brand-400" />
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 mb-1">
                  <span className="text-xs font-semibold text-slate-400">Step {i + 1}</span>
                  {done && <span className="badge-ok">Done</span>}
                </div>
                <p className="font-semibold text-slate-700 text-sm">{label}</p>
                <p className="text-xs text-slate-400 mt-0.5">{desc}</p>
              </div>
              <ArrowRight size={14} className="text-slate-300 group-hover:text-brand-400 transition-colors shrink-0 mt-1" />
            </button>
          )
        })}
      </div>

      {/* About */}
      <div className="card flex items-start gap-4">
        <BookOpen size={20} className="text-brand-300 shrink-0 mt-0.5" />
        <div>
          <p className="font-semibold text-slate-700 text-sm mb-1">Based on MS IEC 62305-2:2024</p>
          <p className="text-xs text-slate-500 leading-relaxed">
            This tool automates Annex A (N), Annex B (P), Annex C/D (L), and Annex E calculations.
            It calculates risk components R = N × P × L, compares against tolerable limits,
            identifies dominant contributors, and generates protection recommendations.
          </p>
        </div>
      </div>
    </div>
  )
}

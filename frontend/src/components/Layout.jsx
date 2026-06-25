import { Outlet, NavLink, useLocation, useNavigate } from 'react-router-dom'
import { useEffect, useRef, useState } from 'react'
import { useAssessment } from '../context/AssessmentContext'
import { Zap, Home, Building2, Cable, MapPin, BarChart3, CheckCircle2, Circle, Save, FolderOpen, FilePlus } from 'lucide-react'

const NAV = [
  { to: '/',         label: 'Home',         icon: Home },
  { to: '/building', label: 'Building',      icon: Building2 },
  { to: '/lines',    label: 'Lines',         icon: Cable },
  { to: '/zones',    label: 'Risk Zones',    icon: MapPin },
  { to: '/results',  label: 'Results',       icon: BarChart3 },
]

export default function Layout() {
  const location = useLocation()
  const navigate = useNavigate()
  const { readiness, clearAll, exportProject, importProject } = useAssessment()
  const fileInputRef = useRef(null)
  const [msg, setMsg] = useState('')

  // Scroll to top on route change
  useEffect(() => { window.scrollTo({ top: 0, behavior: 'instant' }) }, [location.pathname])

  const flash = (text) => { setMsg(text); setTimeout(() => setMsg(''), 2500) }

  const handleNew = () => {
    if (window.confirm('Start a new assessment? This will clear all current data.')) {
      clearAll()
      navigate('/')
      flash('New assessment started')
    }
  }

  const handleSave = () => {
    const name = window.prompt('Project name:', 'my_assessment')
    if (name) { exportProject(name); flash('Project saved') }
  }

  const handleLoadClick = () => fileInputRef.current?.click()

  const handleFileChosen = async (e) => {
    const file = e.target.files?.[0]
    if (!file) return
    try {
      await importProject(file)
      flash('Project loaded')
      navigate('/building')
    } catch (err) {
      flash('Error: ' + err.message)
    }
    e.target.value = '' // reset so same file can be reloaded
  }

  const stepStatus = {
    '/building': readiness.building,
    '/lines':    readiness.lines,
    '/zones':    readiness.zones,
    '/results':  readiness.results,
  }

  return (
    <div className="min-h-screen flex">
      {/* Sidebar */}
      <aside className="w-64 min-h-screen bg-white border-r border-slate-100 flex flex-col fixed top-0 left-0 z-20">
        {/* Logo */}
        <div className="px-6 py-6 border-b border-slate-100">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 bg-gradient-to-br from-brand-400 to-brand-600 rounded-xl flex items-center justify-center shadow-sm">
              <Zap size={18} className="text-white" />
            </div>
            <div>
              <p className="font-bold text-slate-800 text-sm leading-tight">LRAT</p>
              <p className="text-xs text-slate-400 leading-tight">IEC 62305-2:2024</p>
            </div>
          </div>
        </div>

        {/* Nav */}
        <nav className="flex-1 px-4 py-5 space-y-1">
          {NAV.map(({ to, label, icon: Icon }) => (
            <NavLink
              key={to}
              to={to}
              end={to === '/'}
              className={({ isActive }) =>
                `flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-all duration-150 group
                ${isActive
                  ? 'bg-brand-50 text-brand-600 shadow-sm'
                  : 'text-slate-500 hover:bg-slate-50 hover:text-slate-800'
                }`
              }
            >
              {({ isActive }) => (
                <>
                  <Icon size={16} className={isActive ? 'text-brand-500' : 'text-slate-400 group-hover:text-slate-600'} />
                  <span>{label}</span>
                  {to !== '/' && (
                    stepStatus[to]
                      ? <CheckCircle2 size={13} className="ml-auto text-teal-500" />
                      : <Circle size={13} className="ml-auto text-slate-200" />
                  )}
                </>
              )}
            </NavLink>
          ))}
        </nav>

        {/* Project actions */}
        <div className="px-4 py-4 border-t border-slate-100 space-y-1.5">
          <p className="text-xs text-slate-400 font-medium mb-2 uppercase tracking-wide">Project</p>
          <button onClick={handleSave}
            className="w-full flex items-center gap-2 px-3 py-2 rounded-lg text-xs font-medium text-slate-600 hover:bg-slate-50 transition-colors">
            <Save size={14} className="text-slate-400" /> Save to file
          </button>
          <button onClick={handleLoadClick}
            className="w-full flex items-center gap-2 px-3 py-2 rounded-lg text-xs font-medium text-slate-600 hover:bg-slate-50 transition-colors">
            <FolderOpen size={14} className="text-slate-400" /> Load from file
          </button>
          <button onClick={handleNew}
            className="w-full flex items-center gap-2 px-3 py-2 rounded-lg text-xs font-medium text-slate-600 hover:bg-brand-50 hover:text-brand-500 transition-colors">
            <FilePlus size={14} className="text-slate-400" /> New assessment
          </button>
          <input ref={fileInputRef} type="file" accept=".json,application/json"
            onChange={handleFileChosen} className="hidden" />
          {msg && <p className="text-[11px] text-teal-600 px-3 pt-1">{msg}</p>}
        </div>
      </aside>

      {/* Main content */}
      <main className="ml-64 flex-1 min-h-screen">
        <div className="max-w-4xl mx-auto px-8 py-10">
          <Outlet />
        </div>
      </main>
    </div>
  )
}

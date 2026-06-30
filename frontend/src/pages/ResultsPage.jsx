import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAssessment } from '../context/AssessmentContext'
import { PageHeader, InfoBox } from '../components/FormComponents'
import {
  CheckCircle2, XCircle, AlertTriangle, BarChart3,
  ChevronDown, ChevronUp, Download, RefreshCw, Loader2,
  Zap, Shield, ArrowRight, CheckCheck
} from 'lucide-react'

const fmt = (v) => {
  if (v === null || v === undefined) return '—'
  if (typeof v === 'number') {
    if (v === 0) return '0'
    return v.toExponential(3)
  }
  return String(v)
}

function RiskRatioBar({ value, limit }) {
  if (!value || !limit) return null
  const ratio = value / limit
  const pct = Math.min((ratio / 5) * 100, 100) // scale: 5x limit = full bar
  const ok = ratio <= 1
  return (
    <div className="mt-3">
      <div className="flex justify-between text-xs mb-1">
        <span className="text-slate-400">Risk ratio vs tolerable limit</span>
        <span className={`font-semibold ${ok ? 'text-teal-600' : 'text-brand-600'}`}>
          {ratio.toFixed(1)}×  {ok ? '✓ within limit' : '⚠ exceeds limit'}
        </span>
      </div>
      <div className="h-2.5 bg-slate-100 rounded-full overflow-hidden relative">
        {/* Limit line */}
        <div className="absolute top-0 bottom-0 w-0.5 bg-slate-400 z-10" style={{ left: `${(1/5)*100}%` }} />
        <div
          className={`h-full rounded-full transition-all duration-500 ${ok ? 'bg-teal-400' : 'bg-danger-500'}`}
          style={{ width: `${pct}%` }}
        />
      </div>
      <div className="flex justify-between text-[10px] text-slate-300 mt-0.5">
        <span>0</span>
        <span>Limit</span>
        <span>5× limit</span>
      </div>
    </div>
  )
}

function ContributionBar({ contributors }) {
  if (!contributors || contributors.length === 0) return null
  const colors = ['bg-brand-500', 'bg-amber-400', 'bg-blue-400', 'bg-teal-400']
  return (
    <div className="mt-3">
      <p className="text-xs text-slate-400 mb-2">Risk contribution breakdown</p>
      <div className="flex h-4 rounded-full overflow-hidden gap-0.5">
        {contributors.map((c, i) => (
          <div
            key={c.component}
            className={`${colors[i % colors.length]} flex items-center justify-center transition-all`}
            style={{ width: `${c.percent}%` }}
            title={`${c.component}: ${c.percent.toFixed(1)}%`}
          >
            {c.percent > 10 && <span className="text-[9px] text-white font-bold">{c.component}</span>}
          </div>
        ))}
        <div className="bg-slate-200 flex-1" title="Other components" />
      </div>
      <div className="flex flex-wrap gap-3 mt-2">
        {contributors.map((c, i) => (
          <div key={c.component} className="flex items-center gap-1.5">
            <div className={`w-2.5 h-2.5 rounded-full ${colors[i % colors.length]}`} />
            <span className="text-[11px] text-slate-600">{c.component} — {c.percent.toFixed(1)}%</span>
            <span className={`text-[10px] font-semibold px-1.5 rounded-full ${
              c.severity === 'Critical' ? 'bg-danger-50 text-danger-600' :
              c.severity === 'Significant' ? 'bg-amber-100 text-amber-600' :
              'bg-slate-100 text-slate-500'
            }`}>{c.severity}</span>
          </div>
        ))}
      </div>
    </div>
  )
}

function ActionButton({ action, zoneName, onApply, isApplying }) {
  const fmt = (v) => v != null ? v.toExponential(3) : '—'
  const overrideFields = Object.keys(action.overrides ?? {})
  const scopeLabel = overrideFields.includes('LPS_class')
    ? 'Building-level: recalculates all zones'
    : overrideFields.includes('equipotential_bonding_level')
      ? 'Line-level: may affect multiple zones'
      : 'Zone-level: applies to this zone'
  return (
    <div className="flex flex-col gap-1">
      <button
        onClick={() => onApply(zoneName, action)}
        disabled={isApplying}
        className={`flex flex-col items-start gap-0.5 px-3 py-2.5 rounded-lg text-xs font-semibold transition-all text-left
          ${action.is_sufficient
            ? action.is_minimum_needed
              ? 'bg-teal-500 hover:bg-teal-600 text-white shadow-sm'
              : 'bg-teal-100 hover:bg-teal-200 text-teal-800'
            : 'bg-white border border-slate-200 hover:border-brand-300 hover:bg-brand-50 text-slate-700'
          } disabled:opacity-50`}
      >
        <div className="flex items-center gap-1.5">
          {isApplying ? <Loader2 size={12} className="animate-spin" /> : <Shield size={12} />}
          {action.display}
          {action.is_minimum_needed && action.is_sufficient && (
            <span className="bg-white/20 text-[10px] px-1.5 py-0.5 rounded-full">✓ sufficient</span>
          )}
        </div>
        {action.estimated_r != null && (
          <span className={`text-[10px] font-normal ${action.is_sufficient ? 'text-white/80' : 'text-slate-400'}`}>
            Est. after: {fmt(action.estimated_r)}
            {action.is_sufficient ? ' ✓' : ' (still exceeds limit)'}
          </span>
        )}
        {(action.old_r != null || action.new_r != null || action.old_f != null || action.new_f != null) && (
          <span className={`text-[10px] font-normal ${action.is_sufficient ? 'text-white/80' : 'text-slate-400'}`}>
            R: {fmt(action.old_r)} -> {fmt(action.new_r)} | F: {fmt(action.old_f)} -> {fmt(action.new_f)}
          </span>
        )}
        {action.plan?.steps?.length > 1 && (
          <span className={`text-[10px] font-normal ${action.is_sufficient ? 'text-white/80' : 'text-slate-400'}`}>
            Plan steps: {action.plan.steps.map((step, i) => `${i + 1}. ${step.display}`).join(' | ')}
          </span>
        )}
        <span className={`text-[10px] font-normal ${action.is_sufficient ? 'text-white/80' : 'text-slate-400'}`}>
          {scopeLabel}
        </span>
      </button>
      {action.governing_note && (
        <p className={`text-[10px] px-2 py-1 rounded-lg flex items-start gap-1 ${
          action.spd_governed_by === 'frequency'
            ? 'bg-amber-50 text-amber-700'
            : 'bg-brand-50 text-brand-600'
        }`}>
          <span className="mt-0.5">ⓘ</span>
          {action.governing_note}
        </p>
      )}
    </div>
  )
}

function RecommendationCard({ rec, zoneName, onApply, isApplying }) {
  const [open, setOpen] = useState(true)
  return (
    <div className={`rounded-xl border overflow-hidden mb-3 ${
      rec.severity === 'Critical' ? 'border-danger-100' :
      rec.severity === 'Significant' ? 'border-amber-200' : 'border-slate-200'
    }`}>
      <button
        onClick={() => setOpen(o => !o)}
        className={`w-full flex items-center gap-3 px-4 py-3 text-left ${
          rec.severity === 'Critical' ? 'bg-danger-50' :
          rec.severity === 'Significant' ? 'bg-amber-50' : 'bg-slate-50'
        }`}
      >
        <span className={`text-xs font-bold px-2 py-0.5 rounded-full ${
          rec.severity === 'Critical' ? 'bg-danger-100 text-danger-600' :
          rec.severity === 'Significant' ? 'bg-amber-200 text-amber-700' :
          'bg-slate-200 text-slate-600'
        }`}>{rec.severity}</span>
        <span className="font-bold text-slate-700 text-sm">{rec.component}</span>
        <span className="text-xs text-slate-400">{rec.percent?.toFixed(1)}% contribution</span>
        <span className="text-xs text-slate-400 ml-2">Driver: {rec.probability_driver}</span>
        {open ? <ChevronUp size={13} className="ml-auto text-slate-400" /> : <ChevronDown size={13} className="ml-auto text-slate-400" />}
      </button>

      {open && (
        <div className="px-4 py-3 bg-white">
          <p className="text-xs text-slate-500 mb-3">{rec.summary}</p>
          {rec.actions && rec.actions.length > 0 && (
            <div>
              <p className="text-xs font-semibold text-slate-600 mb-2">Apply protection measure:</p>
              <div className="flex flex-wrap gap-2">
                {rec.actions.map((action, i) => (
                  <ActionButton
                    key={i}
                    action={action}
                    zoneName={zoneName}
                    onApply={onApply}
                    isApplying={isApplying}
                  />
                ))}
              </div>
              {rec.actions.some(a => a.note) && (
                <p className="text-[11px] text-slate-400 mt-2 italic">
                  ⓘ {rec.actions.find(a => a.note)?.note}
                </p>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  )
}

function RiskZoneResult({ zoneName, values, recommendations, onApply, isApplying }) {
  const ok = values.risk_status !== 'Protection required'
  const [showComponents, setShowComponents] = useState(false)

  return (
    <div className={`card mb-5 ${!ok ? 'border-danger-100' : 'border-teal-200'}`}>
      {/* Header banner */}
      <div className={`-mx-6 -mt-6 mb-5 px-6 py-4 rounded-t-2xl flex items-center justify-between ${
        ok ? 'bg-teal-50' : 'bg-danger-50'
      }`}>
        <div>
          <h3 className="font-bold text-slate-800 text-base">{zoneName}</h3>
          <p className="text-xs text-slate-400 mt-0.5">Risk Assessment</p>
        </div>
        <div className={`flex items-center gap-2 px-4 py-2 rounded-xl font-bold text-sm ${
          ok ? 'bg-teal-100 text-teal-700' : 'bg-danger-50 text-danger-600'
        }`}>
          {ok ? <CheckCircle2 size={16} /> : <XCircle size={16} />}
          {ok ? 'PROTECTED' : 'PROTECTION REQUIRED'}
        </div>
      </div>

      {/* Key metrics */}
      <div className="grid grid-cols-4 gap-3 mb-4">
        {[
          { label: 'L1 Risk', value: values.RL1 },
          { label: 'L2 Risk', value: values.RL2 },
          { label: 'Total Risk (R)', value: values.R_total, highlight: true },
          { label: 'Tolerable (RT)', value: values.RT },
        ].map(({ label, value, highlight }) => (
          <div key={label} className={`rounded-xl p-3 text-center ${highlight && !ok ? 'bg-danger-50 border border-danger-100' : 'bg-slate-50'}`}>
            <p className="text-xs text-slate-400 mb-1">{label}</p>
            <p className={`font-mono text-sm font-bold ${highlight && !ok ? 'text-danger-600' : 'text-slate-700'}`}>
              {fmt(value)}
            </p>
          </div>
        ))}
      </div>

      {/* Risk ratio bar */}
      <RiskRatioBar value={values.R_total} limit={values.RT} />

      {/* Contribution bar from recommendations */}
      {recommendations && recommendations.length > 0 && (
        <ContributionBar contributors={recommendations} />
      )}

      {/* Detailed components toggle */}
      <button
        onClick={() => setShowComponents(o => !o)}
        className="mt-4 text-xs text-slate-400 hover:text-slate-600 flex items-center gap-1"
      >
        {showComponents ? <ChevronUp size={12}/> : <ChevronDown size={12}/>}
        Detailed risk components
      </button>
      {showComponents && (
        <div className="mt-2 grid grid-cols-3 gap-1.5">
          {["RAT","RAD","RB1","RB2","RC1","RC2","RM1","RM2","RU","RV1","RV2","RW1","RW2","RZ1","RZ2"].map(k => (
            values[k] > 0 && (
              <div key={k} className="bg-slate-50 rounded-lg px-2 py-1.5 text-center">
                <p className="text-[10px] text-slate-400">{k}</p>
                <p className="font-mono text-xs text-slate-700">{fmt(values[k])}</p>
              </div>
            )
          ))}
        </div>
      )}

      {/* Recommendations */}
      {!ok && recommendations && recommendations.length > 0 && (
        <div className="mt-5 pt-4 border-t border-slate-100">
          <p className="text-sm font-bold text-slate-700 mb-3 flex items-center gap-2">
            <Shield size={14} className="text-danger-500" />
            Recommended Protection Measures
          </p>
          {recommendations.map((rec, i) => (
            <RecommendationCard
              key={i}
              rec={rec}
              zoneName={zoneName}
              onApply={onApply}
              isApplying={isApplying}
            />
          ))}
        </div>
      )}

      {ok && (
        <div className="mt-4 flex items-center gap-2 text-teal-600 text-xs font-medium">
          <CheckCheck size={14} />
          Risk is within the tolerable limit. No additional protection required for this zone.
        </div>
      )}
    </div>
  )
}

function FreqZoneResult({ zoneName, values, recommendations, onApply, isApplying }) {
  const [showComponents, setShowComponents] = useState(false)
  if (values.frequency_status === 'Not applicable') {
    return (
      <div className="card mb-3 flex items-center justify-between">
        <h3 className="font-bold text-slate-700 text-sm">{zoneName}</h3>
        <span className="text-xs text-slate-400 bg-slate-100 px-3 py-1 rounded-full">No internal systems</span>
      </div>
    )
  }
  const ok = values.frequency_status !== 'Protection required'
  return (
    <div className={`card mb-4 ${!ok ? 'border-danger-100' : 'border-teal-200'}`}>
      <div className="flex items-center justify-between mb-3">
        <div>
          <h3 className="font-bold text-slate-800 text-sm">{zoneName}</h3>
          <p className="text-xs text-slate-400">Frequency Assessment</p>
        </div>
        <div className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-bold ${
          ok ? 'bg-teal-100 text-teal-700' : 'bg-danger-50 text-danger-600'
        }`}>
          {ok ? <CheckCircle2 size={13} /> : <XCircle size={13} />}
          {ok ? 'Within Limit' : 'PROTECTION REQUIRED'}
        </div>
      </div>
      <div className="grid grid-cols-2 gap-3">
        <div className="bg-slate-50 rounded-xl p-3 text-center">
          <p className="text-xs text-slate-400 mb-1">Total Frequency (F)</p>
          <p className="font-mono text-sm font-bold text-slate-700">{fmt(values.F_total)}</p>
        </div>
        <div className="bg-slate-50 rounded-xl p-3 text-center">
          <p className="text-xs text-slate-400 mb-1">Tolerable (FT)</p>
          <p className="font-mono text-sm font-bold text-slate-700">{fmt(values.FT)}</p>
        </div>
      </div>
      <RiskRatioBar value={values.F_total} limit={values.FT} />

      {/* Frequency components */}
      <button
        onClick={() => setShowComponents(o => !o)}
        className="mt-3 text-xs text-slate-400 hover:text-slate-600 flex items-center gap-1"
      >
        {showComponents ? <ChevronUp size={12}/> : <ChevronDown size={12}/>}
        Frequency components
      </button>
      {showComponents && (
        <div className="mt-2 grid grid-cols-3 gap-1.5">
          {[
            ['FC', values.FC], ['FM', values.FM],
            ['FWP', values.FWP], ['FWT', values.FWT],
            ['FZP', values.FZP], ['FZT', values.FZT],
          ].map(([k, val]) => (
            <div key={k} className="bg-slate-50 rounded-lg px-2 py-1.5 text-center">
              <p className="text-[10px] text-slate-400">{k}</p>
              <p className="font-mono text-xs text-slate-700">{fmt(val)}</p>
            </div>
          ))}
        </div>
      )}

      {/* Frequency recommendations */}
      {!ok && recommendations && recommendations.length > 0 && (
        <div className="mt-5 pt-4 border-t border-slate-100">
          <p className="text-sm font-bold text-slate-700 mb-3 flex items-center gap-2">
            <Shield size={14} className="text-danger-500" />
            Recommended Protection Measures
          </p>
          {recommendations.map((rec, i) => (
            <RecommendationCard
              key={i}
              rec={rec}
              zoneName={zoneName}
              onApply={onApply}
              isApplying={isApplying}
            />
          ))}
        </div>
      )}

      {ok && (
        <div className="mt-3 flex items-center gap-2 text-teal-600 text-xs font-medium">
          <CheckCheck size={14} />
          Frequency is within the tolerable limit. No additional protection required.
        </div>
      )}
    </div>
  )
}

export default function ResultsPage() {
  const {
    buildingData,
    linesData,
    zonesData,
    results,
    baselineAssessment,
    appliedProtectionHistory,
    isCalculating,
    calcError,
    runCalculation,
    readiness,
    applyProtection,
  } = useAssessment()
  const [pdfLoading, setPdfLoading] = useState(null)
  const [applyingZone, setApplyingZone] = useState(null)

  const handleRun = async () => {
    try { await runCalculation() } catch (e) {}
  }

  const [applyMessage, setApplyMessage] = useState(null)

  const handleApply = async (zoneName, action) => {
    setApplyingZone(zoneName)
    setApplyMessage(null)
    try {
      const data = await applyProtection(zoneName, action)
      // Check the new status for this zone and show feedback
      const newStatus = data?.risk_results?.[zoneName]?.risk_status
      const affectedZones = data?.applied_summary?.affected_zones ?? []
      const otherAffectedZones = affectedZones.filter(name => name !== zoneName)
      const affectedText = otherAffectedZones.length
        ? ` This ${data?.applied_summary?.scope}-level change also affected: ${otherAffectedZones.join(', ')}.`
        : ''
      if (newStatus && newStatus !== 'Protection required') {
        setApplyMessage({ type: 'success', text: `Protection applied to ${zoneName}. Risk is now within the tolerable limit.${affectedText}` })
      } else {
        setApplyMessage({ type: 'info', text: `Protection applied to ${zoneName}. Risk reduced, but further measures may be needed.${affectedText}` })
      }
      // Scroll the results into view so the change is visible
      window.scrollTo({ top: 0, behavior: 'smooth' })
    } catch (e) {
      setApplyMessage({ type: 'error', text: 'Could not apply protection. Please try again.' })
    } finally {
      setApplyingZone(null)
    }
  }

  const handlePDF = async (mode = 'current') => {
    if (!results) return
    const useBaseline = mode === 'baseline' && baselineAssessment?.results
    const sourceResults = useBaseline ? baselineAssessment.results : results
    const payload = {
      building_data: useBaseline ? baselineAssessment.building_data : buildingData,
      lines_data: useBaseline ? baselineAssessment.lines_data : linesData,
      zones_data: useBaseline ? baselineAssessment.zones_data : zonesData,
      report_mode: useBaseline ? 'baseline' : appliedProtectionHistory?.length ? 'protected' : 'current',
      baseline_assessment: useBaseline ? null : baselineAssessment,
      applied_protection_history: useBaseline ? [] : appliedProtectionHistory,
      ...sourceResults,
    }

    setPdfLoading(mode)
    try {
      const res = await fetch('/api/generate-pdf', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      })
      if (!res.ok) throw new Error('PDF generation failed')
      const blob = await res.blob()
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = useBaseline ? 'lightning_risk_before_protection.pdf' : 'lightning_risk_after_protection.pdf'
      a.click()
      URL.revokeObjectURL(url)
    } catch (e) {
      alert('PDF error: ' + e.message)
    } finally {
      setPdfLoading(null)
    }
  }

  return (
    <div>
      <PageHeader
        title="Assessment Results"
        subtitle="Run the assessment and apply protection measures to reduce risk."
        step={4} totalSteps={4}
      />

      {/* Readiness */}
      <div className="card mb-6">
        <p className="text-sm font-semibold text-slate-600 mb-3">Assessment Readiness</p>
        <div className="grid grid-cols-3 gap-3">
          {[
            { label: 'Building', done: readiness.building, optional: false },
            { label: 'Lines',    done: readiness.lines,    optional: true },
            { label: 'Zones',    done: readiness.zones,    optional: false },
          ].map(({ label, done, optional }) => (
            <div key={label} className={`flex items-center gap-2 px-4 py-3 rounded-xl border text-sm font-medium
              ${done ? 'bg-teal-50 border-teal-200 text-teal-700' :
                optional ? 'bg-amber-50 border-amber-200 text-amber-600' :
                'bg-brand-50 border-brand-200 text-brand-600'}`}>
              {done ? <CheckCircle2 size={14}/> : <AlertTriangle size={14}/>}
              {label}
              {!done && <span className="ml-auto text-xs opacity-70">{optional ? 'optional' : 'required'}</span>}
            </div>
          ))}
        </div>
      </div>

      {/* Action buttons */}
      <div className="flex gap-3 mb-8">
        <button
          onClick={handleRun}
          disabled={isCalculating || !readiness.building || !readiness.zones}
          className="btn-primary flex items-center gap-2 flex-1 justify-center py-3"
        >
          {isCalculating
            ? <><Loader2 size={16} className="animate-spin"/>
                {applyingZone ? `Applying protection to ${applyingZone}...` : 'Running Assessment...'}
              </>
            : results
            ? <><RefreshCw size={16}/> Re-run Assessment</>
            : <><BarChart3 size={16}/> Run Assessment</>
          }
        </button>
        {results && (
          <>
            <button
              onClick={() => handlePDF('baseline')}
              disabled={!!pdfLoading || !baselineAssessment?.results}
              className="btn-secondary flex items-center gap-2 px-5"
              title="Generate the unprotected assessment PDF"
            >
              {pdfLoading === 'baseline' ? <Loader2 size={16} className="animate-spin"/> : <Download size={16}/>}
              Before PDF
            </button>
            <button
              onClick={() => handlePDF('current')}
              disabled={!!pdfLoading || !appliedProtectionHistory?.length}
              className={`btn-secondary flex items-center gap-2 px-5 ${
                !appliedProtectionHistory?.length ? 'opacity-50 cursor-not-allowed' : ''
              }`}
              title={
                appliedProtectionHistory?.length
                  ? 'Generate the protected assessment PDF'
                  : 'Apply a protection measure first'
              }
            >
              {pdfLoading === 'current' ? <Loader2 size={16} className="animate-spin"/> : <Download size={16}/>}
              After PDF
            </button>
          </>
        )}
      </div>

      {calcError && <InfoBox type="error">⚠ {calcError}</InfoBox>}

      {applyMessage && (
        <div className={`mb-4 px-4 py-3 rounded-xl text-sm font-medium flex items-center gap-2 ${
          applyMessage.type === 'success' ? 'bg-teal-50 text-teal-700 border border-teal-200'
          : applyMessage.type === 'error' ? 'bg-danger-50 text-danger-600 border border-danger-100'
          : 'bg-brand-50 text-brand-700 border border-brand-100'
        }`}>
          {applyMessage.type === 'success' ? <CheckCircle2 size={16}/> : applyMessage.type === 'error' ? <XCircle size={16}/> : <Shield size={16}/>}
          {applyMessage.text}
        </div>
      )}

      {results && (
        <>
          {/* Risk */}
          <div className="mb-8">
            <h2 className="text-lg font-bold text-slate-700 mb-4 flex items-center gap-2">
              <span className="w-7 h-7 bg-brand-100 rounded-lg flex items-center justify-center text-brand-500 text-xs font-bold">R</span>
              Risk Assessment
            </h2>
            {Object.entries(results.risk_results || {}).map(([zoneName, values]) => (
              <RiskZoneResult
                key={zoneName}
                zoneName={zoneName}
                values={values}
                recommendations={results.protection_recommendations?.[zoneName]}
                onApply={handleApply}
                isApplying={applyingZone === zoneName}
              />
            ))}
          </div>

          {/* Frequency */}
          <div className="mb-8">
            <h2 className="text-lg font-bold text-slate-700 mb-4 flex items-center gap-2">
              <span className="w-7 h-7 bg-teal-100 rounded-lg flex items-center justify-center text-teal-500 text-xs font-bold">F</span>
              Frequency Assessment
            </h2>
            {Object.entries(results.frequency_results || {}).map(([zoneName, values]) => (
              <FreqZoneResult
                key={zoneName}
                zoneName={zoneName}
                values={values}
                recommendations={results.frequency_recommendations?.[zoneName]}
                onApply={handleApply}
                isApplying={applyingZone === zoneName}
              />
            ))}
          </div>

          {/* Annex E */}
          {Object.values(results.annex_e_results || {}).some(v => v.RE_total > 0) && (
            <div className="mb-8">
              <h2 className="text-lg font-bold text-slate-700 mb-4 flex items-center gap-2">
                <span className="w-7 h-7 bg-amber-100 rounded-lg flex items-center justify-center text-amber-500 text-xs font-bold">E</span>
                Environmental Risk (Annex E)
              </h2>
              {Object.entries(results.annex_e_results || {}).filter(([,v]) => v.RE_total > 0).map(([zoneName, values]) => (
                <div key={zoneName} className="card mb-4">
                  <h3 className="font-bold text-slate-800 mb-3 text-sm">{zoneName}</h3>
                  <div className="grid grid-cols-3 gap-3">
                    {[['RE1', values.RE1], ['RE2', values.RE2], ['RE Total', values.RE_total]].map(([l, v]) => (
                      <div key={l} className="bg-slate-50 rounded-xl p-3 text-center">
                        <p className="text-xs text-slate-400 mb-1">{l}</p>
                        <p className="font-mono text-sm font-bold text-slate-700">{fmt(v)}</p>
                      </div>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          )}
        </>
      )}

      {!results && !isCalculating && (
        <div className="text-center py-16 text-slate-400">
          <BarChart3 size={40} className="mx-auto mb-3 opacity-30" />
          <p className="text-sm">No results yet. Click Run Assessment above.</p>
        </div>
      )}
    </div>
  )
}

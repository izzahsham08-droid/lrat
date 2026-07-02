import { useState } from 'react'
import { useAssessment } from '../context/AssessmentContext'
import { PageHeader, InfoBox } from '../components/FormComponents'
import {
  CheckCircle2, XCircle, AlertTriangle, BarChart3,
  ChevronDown, ChevronUp, Download, RefreshCw, Loader2,
  Shield, ArrowRight, CheckCheck, ListChecks
} from 'lucide-react'

const fmt = (v) => {
  if (v === null || v === undefined) return '—'
  if (typeof v === 'number') {
    if (v === 0) return '0'
    return v.toExponential(3)
  }
  return String(v)
}

// ---------------------------------------------------------------------------
// Small shared pieces
// ---------------------------------------------------------------------------

function RiskRatioBar({ value, limit }) {
  if (!value || !limit) return null
  const ratio = value / limit
  const pct = Math.min((ratio / 5) * 100, 100) // scale: 5x limit = full bar
  const ok = ratio <= 1
  return (
    <div className="mt-3">
      <div className="flex justify-between text-xs mb-1">
        <span className="text-slate-400">Ratio vs tolerable limit</span>
        <span className={`font-semibold ${ok ? 'text-teal-600' : 'text-brand-600'}`}>
          {ratio.toFixed(1)}×  {ok ? '✓ within limit' : '⚠ exceeds limit'}
        </span>
      </div>
      <div className="h-2.5 bg-slate-100 rounded-full overflow-hidden relative">
        <div className="absolute top-0 bottom-0 w-0.5 bg-slate-400 z-10" style={{ left: `${(1 / 5) * 100}%` }} />
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

// ---------------------------------------------------------------------------
// Risk Assessment — pure results, no recommendation UI mixed in
// ---------------------------------------------------------------------------

function RiskZoneResult({ zoneName, values }) {
  const ok = values.risk_status !== 'Protection required'
  const [showComponents, setShowComponents] = useState(false)

  return (
    <div className={`card mb-5 ${!ok ? 'border-danger-100' : 'border-teal-200'}`}>
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

      <RiskRatioBar value={values.R_total} limit={values.RT} />

      <button
        onClick={() => setShowComponents(o => !o)}
        className="mt-4 text-xs text-slate-400 hover:text-slate-600 flex items-center gap-1"
      >
        {showComponents ? <ChevronUp size={12} /> : <ChevronDown size={12} />}
        Detailed risk components
      </button>
      {showComponents && (
        <div className="mt-2 grid grid-cols-3 gap-1.5">
          {["RAT", "RAD", "RB1", "RB2", "RC1", "RC2", "RM1", "RM2", "RU", "RV1", "RV2", "RW1", "RW2", "RZ1", "RZ2"].map(k => (
            values[k] > 0 && (
              <div key={k} className="bg-slate-50 rounded-lg px-2 py-1.5 text-center">
                <p className="text-[10px] text-slate-400">{k}</p>
                <p className="font-mono text-xs text-slate-700">{fmt(values[k])}</p>
              </div>
            )
          ))}
        </div>
      )}

      {ok && (
        <div className="mt-4 flex items-center gap-2 text-teal-600 text-xs font-medium">
          <CheckCheck size={14} />
          Risk is within the tolerable limit for this zone.
        </div>
      )}
    </div>
  )
}

// ---------------------------------------------------------------------------
// Frequency Assessment — pure results
// ---------------------------------------------------------------------------

function FreqZoneResult({ zoneName, values }) {
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
      <div className={`-mx-6 -mt-6 mb-5 px-6 py-4 rounded-t-2xl flex items-center justify-between ${
        ok ? 'bg-teal-50' : 'bg-danger-50'
      }`}>
        <div>
          <h3 className="font-bold text-slate-800 text-base">{zoneName}</h3>
          <p className="text-xs text-slate-400 mt-0.5">Frequency Assessment</p>
        </div>
        <div className={`flex items-center gap-2 px-4 py-2 rounded-xl font-bold text-sm ${
          ok ? 'bg-teal-100 text-teal-700' : 'bg-danger-50 text-danger-600'
        }`}>
          {ok ? <CheckCircle2 size={16} /> : <XCircle size={16} />}
          {ok ? 'PROTECTED' : 'PROTECTION REQUIRED'}
        </div>
      </div>
      <div className="grid grid-cols-2 gap-3">
        <div className={`rounded-xl p-3 text-center ${!ok ? 'bg-danger-50 border border-danger-100' : 'bg-slate-50'}`}>
          <p className="text-xs text-slate-400 mb-1">Total Frequency (F)</p>
          <p className={`font-mono text-sm font-bold ${!ok ? 'text-danger-600' : 'text-slate-700'}`}>
            {fmt(values.F_total)}
          </p>
        </div>
        <div className="bg-slate-50 rounded-xl p-3 text-center">
          <p className="text-xs text-slate-400 mb-1">Tolerable (FT)</p>
          <p className="font-mono text-sm font-bold text-slate-700">{fmt(values.FT)}</p>
        </div>
      </div>
      <RiskRatioBar value={values.F_total} limit={values.FT} />

      <button
        onClick={() => setShowComponents(o => !o)}
        className="mt-3 text-xs text-slate-400 hover:text-slate-600 flex items-center gap-1"
      >
        {showComponents ? <ChevronUp size={12} /> : <ChevronDown size={12} />}
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

      {ok && (
        <div className="mt-3 flex items-center gap-2 text-teal-600 text-xs font-medium">
          <CheckCheck size={14} />
          Frequency is within the tolerable limit for this zone.
        </div>
      )}
      {ok && (
        <div className="mt-3 flex items-center gap-2 text-teal-600 text-xs font-medium">
          <CheckCheck size={14} />
          Frequency is within the tolerable limit for this zone.
        </div>
      )}
    </div>
  )
}

// ---------------------------------------------------------------------------
// Protection Plan — bottom of page. Shows the suggestion list BEFORE apply,
// then the protected outcome AFTER apply. One button, one action.
// ---------------------------------------------------------------------------

function SuggestedStep({ step, index }) {
  return (
    <div className="rounded-xl border border-slate-100 p-3 bg-white">
      <div className="flex items-start gap-3">
        <span className="w-6 h-6 shrink-0 rounded-full bg-brand-500 text-white text-xs font-bold flex items-center justify-center">
          {index + 1}
        </span>
        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-center gap-2">
            <p className="font-semibold text-sm text-slate-700">{step.display}</p>
            {step.scope && (
              <span className="text-[10px] uppercase tracking-wide px-2 py-0.5 rounded-full bg-slate-100 text-slate-500">
                {step.scope}-level
              </span>
            )}
          </div>
          {(step.affected_zones?.length || step.target_zones?.length) && (
            <p className="text-[11px] text-slate-400 mt-1">
              Affects: {(step.affected_zones || step.target_zones).join(', ')}
            </p>
          )}
          {step.controlled_components?.length > 0 && (
            <p className="text-[11px] text-slate-400 mt-1">
              Reduces: {step.controlled_components.join(', ')}
            </p>
          )}
          {step.engineering_reason && (
            <p className="text-[11px] text-slate-400 mt-1 italic">{step.engineering_reason}</p>
          )}
        </div>
      </div>
    </div>
  )
}

function FailedZoneChip({ zone, kind }) {
  const isFreq = kind === 'frequency'
  return (
    <div className={`rounded-xl border p-3 ${isFreq ? 'border-teal-100 bg-teal-50' : 'border-slate-100 bg-slate-50'}`}>
      <div className="flex items-center justify-between gap-3 mb-2">
        <p className="font-bold text-slate-700 text-sm">{zone.zone_name}</p>
        <p className={`font-mono text-xs ${isFreq ? 'text-teal-700' : 'text-danger-600'}`}>
          {isFreq ? `F ${fmt(zone.f_total)} / FT ${fmt(zone.ft)}` : `R ${fmt(zone.r_total)} / RT ${fmt(zone.rt)}`}
        </p>
      </div>
      <div className="flex flex-wrap gap-1.5">
        {zone.dominant_components?.map(c => (
          <span key={c.component} className={`text-[11px] px-2 py-1 rounded-full bg-white border ${isFreq ? 'border-teal-100' : 'border-slate-200'} text-slate-700`}>
            {c.component} {c.percent?.toFixed(1)}%
          </span>
        ))}
      </div>
    </div>
  )
}

function ProtectionPlanSection({ plan, appliedProtectionHistory, onApply, isApplying }) {
  const hasPlan = plan && plan.status === 'protection_required' &&
    (plan.failed_zones?.length || plan.failed_frequency_zones?.length)

  // Case 1: nothing was ever wrong, and nothing has been applied — no section needed.
  if (!hasPlan && !appliedProtectionHistory?.length) return null

  // Case 2: everything is now protected (either it always was, or a plan was applied).
  if (!hasPlan) {
    const lastApplied = appliedProtectionHistory[appliedProtectionHistory.length - 1]
    return (
      <div className="card border-teal-200">
        <div className="-mx-6 -mt-6 mb-5 px-6 py-4 rounded-t-2xl bg-teal-50 flex items-center gap-2">
          <CheckCircle2 size={18} className="text-teal-600" />
          <h2 className="text-lg font-bold text-slate-800">Protection Plan — All Zones Protected</h2>
        </div>
        <p className="text-sm text-slate-600 mb-4">
          Every zone is now within its tolerable risk and frequency limits.
        </p>
        {lastApplied?.action?.steps?.length > 0 && (
          <div>
            <p className="text-xs font-semibold text-slate-600 mb-2">Protection measures applied:</p>
            <div className="space-y-2">
              {lastApplied.action.steps.map((step, i) => (
                <SuggestedStep key={`${step.display}-${i}`} step={step} index={i} />
              ))}
            </div>
          </div>
        )}
      </div>
    )
  }

  // Case 3: protection is still required — show the suggestion list + apply button.
  const factorText = plan.dominant_control_factors?.length
    ? plan.dominant_control_factors.map(f => `${f.factor} (${f.label})`).join(', ')
    : 'No dominant control factor identified'

  return (
    <div className="card border-brand-100">
      <div className="-mx-6 -mt-6 mb-5 px-6 py-4 rounded-t-2xl bg-brand-50 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <ListChecks size={18} className="text-brand-500" />
          <div>
            <h2 className="text-lg font-bold text-slate-800">Protection Plan</h2>
            <p className="text-xs text-slate-500 mt-0.5">
              Worst zones and dominant components identified first, then protection measures simulated in scope order.
            </p>
          </div>
        </div>
      </div>

      <p className="text-sm text-slate-600 mb-4">{plan.summary}</p>

      <div className="grid md:grid-cols-2 gap-3 mb-5">
        {plan.failed_zones?.map(zone => (
          <FailedZoneChip key={zone.zone_name} zone={zone} kind="risk" />
        ))}
        {plan.failed_frequency_zones?.map(zone => (
          <FailedZoneChip key={`F-${zone.zone_name}`} zone={zone} kind="frequency" />
        ))}
      </div>

      <div className="rounded-xl border border-slate-100 bg-slate-50 p-4 mb-5">
        <p className="text-xs font-bold text-slate-700 mb-1">Main adjustable protection factors</p>
        <p className="text-xs text-slate-500">{factorText}</p>
      </div>

      {plan.recommended_steps?.length > 0 && (
        <div className="mb-5">
          <p className="text-sm font-bold text-slate-700 mb-3">Suggested protection strategy</p>
          <div className="space-y-2">
            {plan.recommended_steps.map((step, index) => (
              <SuggestedStep key={`${step.display}-${index}`} step={step} index={index} />
            ))}
          </div>
        </div>
      )}

      {plan.apply_action && (
        <button
          onClick={() => onApply('__plan__', plan.apply_action)}
          disabled={isApplying}
          className="w-full bg-brand-500 hover:bg-brand-600 disabled:opacity-50 text-white rounded-xl px-4 py-3 text-sm font-bold flex items-center justify-center gap-2"
        >
          {isApplying ? <Loader2 size={16} className="animate-spin" /> : <Shield size={16} />}
          Apply Recommended Plan and Re-run Assessment
        </button>
      )}
    </div>
  )
}

// ---------------------------------------------------------------------------
// Page
// ---------------------------------------------------------------------------

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
  const [applyMessage, setApplyMessage] = useState(null)

  const handleRun = async () => {
    setApplyMessage(null)
    try { await runCalculation() } catch (e) {}
  }

  const handleApply = async (zoneName, action) => {
    setApplyingZone(zoneName)
    setApplyMessage(null)
    try {
      const data = await applyProtection(zoneName, action)
      const stillRequired = Object.entries(data?.risk_results ?? {})
        .filter(([name]) => name !== 'Building_Total')
        .filter(([, values]) => values?.risk_status === 'Protection required')
        .map(([name]) => name)
      setApplyMessage({
        type: stillRequired.length ? 'info' : 'success',
        text: stillRequired.length
          ? `Protection plan applied and assessment rerun. Further measures may still be needed for: ${stillRequired.join(', ')}.`
          : 'Protection plan applied and assessment rerun. All zones are now within the tolerable risk limit.',
      })
      window.scrollTo({ top: 0, behavior: 'smooth' })
    } catch (e) {
      setApplyMessage({ type: 'error', text: 'Could not apply the protection plan. Please try again.' })
    } finally {
      setApplyingZone(null)
    }
  }

  const handlePDF = async () => {
    if (!results) return
    const payload = {
      building_data: buildingData,
      lines_data: linesData,
      zones_data: zonesData,
      risk_results: results.risk_results,
      frequency_results: results.frequency_results,
      annex_e_results: results.annex_e_results,
      protection_recommendations: results.protection_recommendations,
      frequency_recommendations: results.frequency_recommendations,
      protection_plan: results.protection_plan,
      baseline_assessment: baselineAssessment,
      applied_protection_history: appliedProtectionHistory,
    }

    setPdfLoading(true)
    try {
      const res = await fetch('/api/generate-pdf', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      })
      if (!res.ok) {
        let detail = 'PDF generation failed'
        try {
          const err = await res.json()
          console.error('PDF generation error (full detail):', err)
          detail = typeof err.detail === 'string'
            ? err.detail
            : JSON.stringify(err.detail || err)
        } catch {}
        throw new Error(detail)
      }
      const blob = await res.blob()
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = 'lightning_risk_report.pdf'
      a.click()
      URL.revokeObjectURL(url)
    } catch (e) {
      alert('PDF error: ' + e.message)
    } finally {
      setPdfLoading(false)
    }
  }

  return (
    <div>
      <PageHeader
        title="Assessment Results"
        subtitle="Run the assessment, review the risk and frequency results, then apply the recommended protection plan."
        step={4} totalSteps={4}
      />

      <div className="card mb-6">
        <p className="text-sm font-semibold text-slate-600 mb-3">Assessment Readiness</p>
        <div className="grid grid-cols-3 gap-3">
          {[
            { label: 'Building', done: readiness.building, optional: false },
            { label: 'Lines', done: readiness.lines, optional: true },
            { label: 'Zones', done: readiness.zones, optional: false },
          ].map(({ label, done, optional }) => (
            <div key={label} className={`flex items-center gap-2 px-4 py-3 rounded-xl border text-sm font-medium
              ${done ? 'bg-teal-50 border-teal-200 text-teal-700' :
                optional ? 'bg-amber-50 border-amber-200 text-amber-600' :
                  'bg-brand-50 border-brand-200 text-brand-600'}`}>
              {done ? <CheckCircle2 size={14} /> : <AlertTriangle size={14} />}
              {label}
              {!done && <span className="ml-auto text-xs opacity-70">{optional ? 'optional' : 'required'}</span>}
            </div>
          ))}
        </div>
      </div>

      <div className="flex gap-3 mb-8">
        <button
          onClick={handleRun}
          disabled={isCalculating || !readiness.building || !readiness.zones}
          className="btn-primary flex items-center gap-2 flex-1 justify-center py-3"
        >
          {isCalculating
            ? <><Loader2 size={16} className="animate-spin" />
              {applyingZone ? 'Applying protection plan...' : 'Running Assessment...'}
            </>
            : results
              ? <><RefreshCw size={16} /> Re-run Assessment</>
              : <><BarChart3 size={16} /> Run Assessment</>
          }
        </button>
        {results && (
          <button
            onClick={handlePDF}
            disabled={!!pdfLoading}
            className="btn-secondary flex items-center gap-2 px-5"
            title="Generate a report with both the unprotected and protected results"
          >
            {pdfLoading ? <Loader2 size={16} className="animate-spin" /> : <Download size={16} />}
            Download Report (PDF)
          </button>
        )}
      </div>

      {calcError && <InfoBox type="error">⚠ {calcError}</InfoBox>}

      {applyMessage && (
        <div className={`mb-4 px-4 py-3 rounded-xl text-sm font-medium flex items-center gap-2 ${
          applyMessage.type === 'success' ? 'bg-teal-50 text-teal-700 border border-teal-200'
            : applyMessage.type === 'error' ? 'bg-danger-50 text-danger-600 border border-danger-100'
              : 'bg-brand-50 text-brand-700 border border-brand-100'
        }`}>
          {applyMessage.type === 'success' ? <CheckCircle2 size={16} /> : applyMessage.type === 'error' ? <XCircle size={16} /> : <Shield size={16} />}
          {applyMessage.text}
        </div>
      )}

      {results && (
        <>
          {/* 1. Risk Assessment — raw results per zone */}
          <div className="mb-8">
            <h2 className="text-lg font-bold text-slate-700 mb-4 flex items-center gap-2">
              <span className="w-7 h-7 bg-brand-100 rounded-lg flex items-center justify-center text-brand-500 text-xs font-bold">R</span>
              Risk Assessment
            </h2>
            {Object.entries(results.risk_results || {}).map(([zoneName, values]) => (
              <RiskZoneResult key={zoneName} zoneName={zoneName} values={values} />
            ))}
          </div>

          {/* 2. Frequency Assessment — raw results per zone */}
          <div className="mb-8">
            <h2 className="text-lg font-bold text-slate-700 mb-4 flex items-center gap-2">
              <span className="w-7 h-7 bg-teal-100 rounded-lg flex items-center justify-center text-teal-500 text-xs font-bold">F</span>
              Frequency Assessment
            </h2>
            {Object.entries(results.frequency_results || {}).map(([zoneName, values]) => (
              <FreqZoneResult key={zoneName} zoneName={zoneName} values={values} />
            ))}
          </div>

          {/* 3. Annex E — unchanged */}
          {Object.values(results.annex_e_results || {}).some(v => v.RE_total > 0) && (
            <div className="mb-8">
              <h2 className="text-lg font-bold text-slate-700 mb-4 flex items-center gap-2">
                <span className="w-7 h-7 bg-amber-100 rounded-lg flex items-center justify-center text-amber-500 text-xs font-bold">E</span>
                Environmental Risk (Annex E)
              </h2>
              {Object.entries(results.annex_e_results || {}).filter(([, v]) => v.RE_total > 0).map(([zoneName, values]) => (
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

          {/* 4. Protection Plan — bottom of page, suggestion list before, protected state after */}
          <div className="mb-8">
            <ProtectionPlanSection
              plan={results.protection_plan}
              appliedProtectionHistory={appliedProtectionHistory}
              onApply={handleApply}
              isApplying={applyingZone === '__plan__'}
            />
          </div>
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

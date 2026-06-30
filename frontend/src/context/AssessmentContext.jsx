import React, { createContext, useContext, useState, useEffect } from 'react'

const AssessmentContext = createContext(null)
const STORAGE_KEY = 'lrat_assessment_v1'

// Load saved state from browser storage (runs once at startup)
function loadInitial() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    if (!raw) return null
    return JSON.parse(raw)
  } catch {
    return null
  }
}

function clone(value) {
  if (value === null || value === undefined) return value
  return JSON.parse(JSON.stringify(value))
}

export function AssessmentProvider({ children }) {
  const saved = loadInitial()

  const [buildingData, setBuildingData] = useState(saved?.buildingData ?? null)
  const [linesData, setLinesData]       = useState(saved?.linesData ?? [])
  const [zonesData, setZonesData]       = useState(saved?.zonesData ?? [])
  const [results, setResults]           = useState(saved?.results ?? null)
  const [baselineAssessment, setBaselineAssessment] = useState(saved?.baselineAssessment ?? null)
  const [appliedProtectionHistory, setAppliedProtectionHistory] = useState(saved?.appliedProtectionHistory ?? [])
  const [isCalculating, setIsCalculating] = useState(false)
  const [calcError, setCalcError]       = useState(null)

  // Auto-save to browser storage whenever data changes
  useEffect(() => {
    const payload = {
      buildingData,
      linesData,
      zonesData,
      results,
      baselineAssessment,
      appliedProtectionHistory,
    }
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(payload))
    } catch {
      // storage full or unavailable — ignore silently
    }
  }, [buildingData, linesData, zonesData, results, baselineAssessment, appliedProtectionHistory])

  const addZone = (zone) => setZonesData(prev => [...prev, zone])
  const updateZone = (index, zone) => setZonesData(prev => prev.map((z, i) => i === index ? zone : z))
  const deleteZone = (index) => setZonesData(prev => prev.filter((_, i) => i !== index))

  const addLine = (line) => setLinesData(prev => [...prev, line])
  const updateLine = (index, line) => setLinesData(prev => prev.map((l, i) => i === index ? line : l))
  const deleteLine = (index) => setLinesData(prev => prev.filter((_, i) => i !== index))

  // Clear everything (new assessment)
  const clearAll = () => {
    setBuildingData(null)
    setLinesData([])
    setZonesData([])
    setResults(null)
    setBaselineAssessment(null)
    setAppliedProtectionHistory([])
    setCalcError(null)
    try { localStorage.removeItem(STORAGE_KEY) } catch {}
  }

  // Export current project to a downloadable .json file
  const exportProject = (projectName = 'lrat_project') => {
    const payload = {
      meta: { savedAt: new Date().toISOString(), tool: 'LRAT', version: 1 },
      buildingData, linesData, zonesData,
    }
    const blob = new Blob([JSON.stringify(payload, null, 2)], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `${projectName}.lrat.json`
    a.click()
    URL.revokeObjectURL(url)
  }

  // Import a project from a chosen .json file
  const importProject = (file) => {
    return new Promise((resolve, reject) => {
      const reader = new FileReader()
      reader.onload = (e) => {
        try {
          const data = JSON.parse(e.target.result)
          setBuildingData(data.buildingData ?? null)
          setLinesData(data.linesData ?? [])
          setZonesData(data.zonesData ?? [])
          setResults(null)        // results must be recalculated for the loaded data
          setBaselineAssessment(null)
          setAppliedProtectionHistory([])
          setCalcError(null)
          resolve(true)
        } catch (err) {
          reject(new Error('Invalid project file'))
        }
      }
      reader.onerror = () => reject(new Error('Could not read file'))
      reader.readAsText(file)
    })
  }

  const makeAssessmentSnapshot = (building, lines, zones, assessmentResults) => ({
    capturedAt: new Date().toISOString(),
    building_data: clone(building),
    lines_data: clone(lines ?? []),
    zones_data: clone(zones ?? []),
    results: clone(assessmentResults),
  })

  const getChangedZones = (beforeSnapshot, afterSnapshot) => {
    const beforeRisk = beforeSnapshot?.results?.risk_results ?? {}
    const afterRisk = afterSnapshot?.results?.risk_results ?? {}
    const beforeFreq = beforeSnapshot?.results?.frequency_results ?? {}
    const afterFreq = afterSnapshot?.results?.frequency_results ?? {}
    const zoneNames = new Set([
      ...Object.keys(beforeRisk),
      ...Object.keys(afterRisk),
      ...Object.keys(beforeFreq),
      ...Object.keys(afterFreq),
    ])

    return [...zoneNames].filter(zoneName => {
      if (zoneName === 'Building_Total') return false
      const br = beforeRisk[zoneName] ?? {}
      const ar = afterRisk[zoneName] ?? {}
      const bf = beforeFreq[zoneName] ?? {}
      const af = afterFreq[zoneName] ?? {}
      return (
        br.R_total !== ar.R_total ||
        br.risk_status !== ar.risk_status ||
        bf.F_total !== af.F_total ||
        bf.frequency_status !== af.frequency_status
      )
    })
  }

  // Apply a protection measure or full protection plan to a specific zone and re-run.
  const applyProtection = async (zoneName, actionOrField, maybeValue) => {
    const BUILDING_LEVEL_FIELDS = ['LPS_class']
    const LINE_LEVEL_FIELDS = ['equipotential_bonding_level']
    const PEB_ORDER = ['none', 'III-IV', 'II', 'I']

    const action = (
      typeof actionOrField === 'object' && actionOrField !== null
        ? actionOrField
        : { field: actionOrField, value: maybeValue, overrides: { [actionOrField]: maybeValue } }
    )
    const overrides = action.overrides ?? { [action.field]: action.value }
    const overrideFields = Object.keys(overrides)
    const scope = overrideFields.some(field => BUILDING_LEVEL_FIELDS.includes(field))
      ? 'building'
      : overrideFields.some(field => LINE_LEVEL_FIELDS.includes(field))
        ? 'line'
        : 'zone'

    let updatedBuilding = buildingData
    let updatedZones = zonesData
    let updatedLines = linesData

    const zoneIndex = zonesData.findIndex(z => z.name === zoneName)
    if (zoneIndex === -1) return
    const beforeSnapshot = makeAssessmentSnapshot(buildingData, linesData, zonesData, results)

    const upgradePeb = (current, target) => {
      const currentIdx = PEB_ORDER.indexOf(current ?? 'none')
      const targetIdx = PEB_ORDER.indexOf(target ?? 'none')
      if (targetIdx < 0) return current
      if (currentIdx < 0) return target
      return targetIdx > currentIdx ? target : current
    }

    Object.entries(overrides).forEach(([field, value]) => {
      if (BUILDING_LEVEL_FIELDS.includes(field)) {
        updatedBuilding = { ...(updatedBuilding ?? {}), [field]: value }
      } else if (LINE_LEVEL_FIELDS.includes(field)) {
        updatedLines = updatedLines.map(l => ({
          ...l,
          [field]: field === 'equipotential_bonding_level'
            ? upgradePeb(l[field], value)
            : value,
        }))
      } else {
        updatedZones = updatedZones.map((z, i) => (
          i === zoneIndex ? { ...z, [field]: value } : z
        ))
      }
    })

    setBuildingData(updatedBuilding)
    setZonesData(updatedZones)
    setLinesData(updatedLines)

    // Re-run with updated data
    setIsCalculating(true)
    setCalcError(null)
    try {
      const res = await fetch('/api/calculate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          building_data: updatedBuilding,
          lines_data: updatedLines,
          zones_data: updatedZones,
        })
      })
      if (!res.ok) { const err = await res.json(); throw new Error(err.detail || 'Calculation failed') }
      const data = await res.json()
      const afterSnapshot = makeAssessmentSnapshot(updatedBuilding, updatedLines, updatedZones, data)
      const affectedZones = getChangedZones(beforeSnapshot, afterSnapshot)
      setResults(data)
      setBaselineAssessment(prev => prev ?? beforeSnapshot)
      setAppliedProtectionHistory(prev => [
        ...prev,
        {
          appliedAt: new Date().toISOString(),
          zone_name: zoneName,
          scope,
          affected_zones: affectedZones,
          action: clone(action),
          before: beforeSnapshot,
          after: afterSnapshot,
        },
      ])
      return { ...data, applied_summary: { scope, affected_zones: affectedZones } }
    } catch (e) {
      setCalcError(e.message)
      throw e
    } finally {
      setIsCalculating(false)
    }
  }

  const runCalculation = async () => {
    setIsCalculating(true)
    setCalcError(null)
    try {
      const res = await fetch('/api/calculate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          building_data: buildingData,
          lines_data: linesData,
          zones_data: zonesData,
        })
      })
      if (!res.ok) {
        const err = await res.json()
        throw new Error(err.detail || 'Calculation failed')
      }
      const data = await res.json()
      const baseline = makeAssessmentSnapshot(buildingData, linesData, zonesData, data)
      setResults(data)
      setBaselineAssessment(baseline)
      setAppliedProtectionHistory([])
      return data
    } catch (e) {
      setCalcError(e.message)
      throw e
    } finally {
      setIsCalculating(false)
    }
  }

  const readiness = {
    building: !!buildingData,
    lines: linesData.length > 0,
    zones: zonesData.length > 0,
    results: !!results,
  }

  return (
    <AssessmentContext.Provider value={{
      buildingData, setBuildingData,
      linesData, addLine, updateLine, deleteLine,
      zonesData, addZone, updateZone, deleteZone,
      results, setResults,
      baselineAssessment, appliedProtectionHistory,
      isCalculating, calcError,
      runCalculation, readiness,
      clearAll, exportProject, importProject,
      applyProtection,
    }}>
      {children}
    </AssessmentContext.Provider>
  )
}

export function useAssessment() {
  const ctx = useContext(AssessmentContext)
  if (!ctx) throw new Error('useAssessment must be used inside AssessmentProvider')
  return ctx
}

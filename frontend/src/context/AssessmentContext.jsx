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

export function AssessmentProvider({ children }) {
  const saved = loadInitial()

  const [buildingData, setBuildingData] = useState(saved?.buildingData ?? null)
  const [linesData, setLinesData]       = useState(saved?.linesData ?? [])
  const [zonesData, setZonesData]       = useState(saved?.zonesData ?? [])
  const [results, setResults]           = useState(saved?.results ?? null)
  const [isCalculating, setIsCalculating] = useState(false)
  const [calcError, setCalcError]       = useState(null)

  // Auto-save to browser storage whenever data changes
  useEffect(() => {
    const payload = { buildingData, linesData, zonesData, results }
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(payload))
    } catch {
      // storage full or unavailable — ignore silently
    }
  }, [buildingData, linesData, zonesData, results])

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
      setResults(data)
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
      isCalculating, calcError,
      runCalculation, readiness,
      clearAll, exportProject, importProject,
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

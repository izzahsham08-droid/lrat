import { useState } from 'react'
import { ChevronDown, ChevronUp, Info } from 'lucide-react'

export default function LossGuide() {
  const [open, setOpen] = useState(false)

  return (
    <div className="mb-5 border border-brand-100 rounded-xl overflow-hidden">
      <button
        type="button"
        onClick={() => setOpen(o => !o)}
        className="w-full flex items-center gap-2 px-4 py-3 bg-brand-50 hover:bg-brand-100 transition-colors text-left"
      >
        <Info size={15} className="text-brand-400 shrink-0" />
        <span className="text-sm font-semibold text-brand-600">Loss Selection Guide</span>
        <span className="text-xs text-slate-400 ml-1">— category types and what each loss means</span>
        {open
          ? <ChevronUp size={15} className="text-brand-400 ml-auto" />
          : <ChevronDown size={15} className="text-brand-400 ml-auto" />}
      </button>

      {open && (
        <div className="px-5 py-5 space-y-6 bg-white text-sm">

          {/* PART 1 — Category guide */}
          <div>
            <p className="font-semibold text-slate-700 mb-2">1. Choosing the Zone Loss Category</p>
            <p className="text-slate-500 text-xs mb-3">Pick one category per zone based on what the zone is used for (Table C.2):</p>
            <div className="space-y-2">
              <div className="flex gap-3 items-start">
                <span className="text-xs font-bold text-brand-500 bg-brand-50 px-2 py-0.5 rounded shrink-0 w-24 text-center">Very High</span>
                <span className="text-xs text-slate-600">Explosion-risk areas, ICUs, operating rooms, life-saving electrical equipment, or where internal-system failure can injure people or harm the environment.</span>
              </div>
              <div className="flex gap-3 items-start">
                <span className="text-xs font-bold text-amber-600 bg-amber-50 px-2 py-0.5 rounded shrink-0 w-24 text-center">High</span>
                <span className="text-xs text-slate-600">Reduced-mobility areas (hospital wards, prisons), control rooms, power stations, telecom centres, museums and cultural-heritage buildings.</span>
              </div>
              <div className="flex gap-3 items-start">
                <span className="text-xs font-bold text-teal-600 bg-teal-50 px-2 py-0.5 rounded shrink-0 w-24 text-center">Normal</span>
                <span className="text-xs text-slate-600">Buildings open to the public — churches, hotels, schools, offices, civic buildings, public entertainment, supermarkets.</span>
              </div>
              <div className="flex gap-3 items-start">
                <span className="text-xs font-bold text-slate-500 bg-slate-100 px-2 py-0.5 rounded shrink-0 w-24 text-center">Low</span>
                <span className="text-xs text-slate-600">Privately owned buildings — apartment houses, farmhouses.</span>
              </div>
            </div>
          </div>

          {/* PART 2 — Component meanings */}
          <div>
            <p className="font-semibold text-slate-700 mb-2">2. What Each Loss Component Means</p>
            <div className="bg-slate-50 rounded-lg p-3 mb-3">
              <p className="text-xs text-slate-600">
                <strong className="text-brand-500">Quick rule:</strong> Component ending in <strong>1</strong> = harm to <strong>people</strong>.
                Component ending in <strong>2</strong> = harm to the <strong>structure / service</strong>.
              </p>
            </div>
            <div className="space-y-1.5">
              {[
                ['LT', 'people', 'Injury to people from touch & step voltage'],
                ['LD', 'people', 'Injury to people from a direct lightning strike'],
                ['LF1', 'people', 'Injury to people caused by fire or explosion'],
                ['LF2', 'structure', 'Physical damage to the structure from fire or explosion'],
                ['LO1', 'people', 'Injury to people caused by internal system failure'],
                ['LO2', 'structure', 'Loss of service from internal system failure'],
              ].map(([code, who, desc]) => (
                <div key={code} className="flex items-center gap-3">
                  <span className="text-xs font-mono font-bold text-slate-700 w-10">{code}</span>
                  <span className={`text-[10px] font-semibold px-1.5 py-0.5 rounded shrink-0 w-16 text-center ${
                    who === 'people' ? 'bg-brand-50 text-brand-500' : 'bg-blue-50 text-blue-500'
                  }`}>{who}</span>
                  <span className="text-xs text-slate-600">{desc}</span>
                </div>
              ))}
            </div>
          </div>

        </div>
      )}
    </div>
  )
}

import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAssessment } from '../context/AssessmentContext'
import {
  PageHeader, SectionCard, FormField, NumberInput, SelectInput,
  CheckboxInput, RadioGroup, InfoBox
} from '../components/FormComponents'
import { Ruler, Zap, ShieldCheck, Layers, Network, Cable, Radio } from 'lucide-react'

const LOCATION_OPTIONS = [
  { value: 'surrounded_high', label: 'Surrounded by higher structures (CD = 0.25)' },
  { value: 'surrounded_same', label: 'Surrounded by same/smaller structures (CD = 0.5)' },
  { value: 'isolated',        label: 'Isolated — no nearby objects (CD = 1.0)' },
  { value: 'hilltop',         label: 'Isolated on hilltop or knoll (CD = 2.0)' },
]
const MATERIAL_OPTIONS = [
  { value: 'wood',                           label: 'Wood' },
  { value: 'masonry',                        label: 'Masonry' },
  { value: 'reinforced_concrete',            label: 'Reinforced Concrete' },
  { value: 'interconnected_metal_framework', label: 'Interconnected Metal Framework' },
]
const LPS_OPTIONS = [
  { value: 'I', label: 'Class I' }, { value: 'II', label: 'Class II' },
  { value: 'III', label: 'Class III' }, { value: 'IV', label: 'Class IV' },
]
const DENSITY_METHODS = [
  { value: 'NSG', label: 'Direct NSG (lightning ground strike-point density)' },
  { value: 'NG',  label: 'NG with correction factor k' },
  { value: 'NT',  label: 'NT satellite-based estimate' },
]

const DEFAULT = {
  name: '', L: null, W: null, H: null,
  structure_shape: 'rectangular', Hmin: null, Hp: null,
  location_type: null,
  density_method: 'NSG', NSG: null, NG: null, NT: null, k: 2,
  adjacent_structure: false, L_adj: null, W_adj: null, H_adj: null, CDJ: null,
  LPS_class: null, TWS: false, PTWS: null,
  extensive_metal_framework: false, reinforced_concrete_interconnected: false,
  metal_roof: false, complete_roof_protection: false,
  wall_material: null, roof_material: null,
  reinforcement_interconnected: false, unbonded_metal_parts: false,
  mesh_earth_termination: false, meshed_bonding_network: false, accessible_metal_installation: true,
  structure_shielding: false, wm1: null, continuous_metal_shield: false,
}

export default function BuildingPage() {
  const { buildingData, setBuildingData } = useAssessment()
  const navigate = useNavigate()
  const [form, setForm] = useState(buildingData || DEFAULT)
  const [saved, setSaved] = useState(!!buildingData)

  const set = (key) => (val) => setForm(f => ({ ...f, [key]: val }))

  const goToLines = () => {
    const payload = { ...form }
    if (form.density_method === 'NSG') { payload.NG = null; payload.NT = null }
    else if (form.density_method === 'NG') { payload.NSG = null; payload.NT = null }
    else { payload.NSG = null; payload.NG = null }
    setBuildingData(payload)
    setSaved(true)
    navigate('/lines')
  }

  return (
    <div>
      <PageHeader
        title="Building Information"
        subtitle="Enter the general structure information used for lightning risk assessment."
        step={1} totalSteps={4}
      />

      {saved && <InfoBox type="success">Building data saved. You can update it anytime.</InfoBox>}

      <SectionCard icon={<Ruler size={15} />} title="Building Geometry">
        <div className="grid grid-cols-3 gap-4 mb-4">
          <FormField label="Length (m)" required>
            <NumberInput value={form.L} onChange={set('L')} placeholder="e.g. 20" min={0} />
          </FormField>
          <FormField label="Width (m)" required>
            <NumberInput value={form.W} onChange={set('W')} placeholder="e.g. 40" min={0} />
          </FormField>
          <FormField label="Height (m)" required>
            <NumberInput value={form.H} onChange={set('H')} placeholder="e.g. 25" min={0} />
          </FormField>
        </div>
        <FormField label="Structure Shape">
          <div className="space-y-2">
            {[
              { value: 'rectangular', label: 'Rectangular' },
              { value: 'complex', label: 'Complex (different roof heights / protruding parts)' },
            ].map(o => (
              <label key={o.value} className="flex items-center gap-3 cursor-pointer group">
                <div
                  onClick={() => set('structure_shape')(o.value)}
                  className={`w-[18px] h-[18px] rounded-full border-2 flex items-center justify-center transition-all cursor-pointer
                    ${form.structure_shape === o.value ? 'border-brand-500' : 'border-slate-300'}`}>
                  {form.structure_shape === o.value && <div className="w-[8px] h-[8px] rounded-full bg-brand-500" />}
                </div>
                <span className="text-sm text-slate-700" onClick={() => set('structure_shape')(o.value)}>{o.label}</span>
              </label>
            ))}
          </div>
        </FormField>
        {form.structure_shape === 'complex' && (
          <div className="grid grid-cols-2 gap-4 mt-4 p-4 bg-brand-50 rounded-xl border border-brand-100">
            <FormField label="Minimum Height, Hmin (m)">
              <NumberInput value={form.Hmin} onChange={set('Hmin')} placeholder="e.g. 10" />
            </FormField>
            <FormField label="Protruding Height, Hp (m)">
              <NumberInput value={form.Hp} onChange={set('Hp')} placeholder="e.g. 25" />
            </FormField>
          </div>
        )}
        <div className="mt-4">
          <FormField label="Relative Location of Structure" required
            hint="Consider surrounding objects within approximately 3 × building height (3H).">
            <SelectInput value={form.location_type} onChange={set('location_type')} options={LOCATION_OPTIONS} />
          </FormField>
        </div>
      </SectionCard>

      <SectionCard icon={<Zap size={15} />} title="Lightning Environment">
        <FormField label="Lightning Density Input Method" required>
          <RadioGroup value={form.density_method} onChange={set('density_method')} options={DENSITY_METHODS} />
        </FormField>
        <div className="mt-4">
          {form.density_method === 'NSG' && (
            <FormField label="NSG — Lightning Ground Strike-Point Density (km⁻² yr⁻¹)" required>
              <NumberInput value={form.NSG} onChange={set('NSG')} placeholder="e.g. 4.0" />
            </FormField>
          )}
          {form.density_method === 'NG' && (
            <div className="grid grid-cols-2 gap-4">
              <FormField label="NG — Ground Flash Density" required>
                <NumberInput value={form.NG} onChange={set('NG')} placeholder="e.g. 2.0" />
              </FormField>
              <FormField label="Correction Factor, k" required>
                <NumberInput value={form.k} onChange={set('k')} placeholder="e.g. 2" />
              </FormField>
            </div>
          )}
          {form.density_method === 'NT' && (
            <FormField label="NT — Total Flash Density (satellite estimate)" required>
              <NumberInput value={form.NT} onChange={set('NT')} placeholder="e.g. 8.0" />
            </FormField>
          )}
        </div>
      </SectionCard>

      <SectionCard icon={<ShieldCheck size={15} />} title="Lightning Protection System">
        <FormField label="LPS Class" hint="Leave blank if no LPS is installed.">
          <SelectInput value={form.LPS_class} onChange={set('LPS_class')} options={LPS_OPTIONS} placeholder="No LPS" />
        </FormField>
        <div className="mt-4 space-y-3">
          <CheckboxInput checked={form.TWS} onChange={set('TWS')} label="Thunderstorm Warning System (TWS) present" />
          {form.TWS && (
            <FormField label="PTWS value">
              <NumberInput value={form.PTWS} onChange={set('PTWS')} placeholder="e.g. 0.1" min={0} />
            </FormField>
          )}
        </div>
      </SectionCard>

      <SectionCard icon={<Layers size={15} />} title="Structure Construction">
        <div className="grid grid-cols-2 gap-4 mb-4">
          <FormField label="Wall Material">
            <SelectInput value={form.wall_material} onChange={set('wall_material')} options={MATERIAL_OPTIONS} />
          </FormField>
          <FormField label="Roof Material">
            <SelectInput value={form.roof_material} onChange={set('roof_material')} options={MATERIAL_OPTIONS} />
          </FormField>
        </div>
        <div className="space-y-3">
          <CheckboxInput checked={form.reinforcement_interconnected} onChange={set('reinforcement_interconnected')}
            label="Reinforcement bars are sufficiently interconnected and earthed" />
          <CheckboxInput checked={form.unbonded_metal_parts} onChange={set('unbonded_metal_parts')}
            label="Significant unbonded metal protruding parts present" />
        </div>
      </SectionCard>

      <SectionCard icon={<Network size={15} />} title="Natural LPS Conditions">
        <div className="space-y-3">
          <CheckboxInput checked={form.extensive_metal_framework} onChange={set('extensive_metal_framework')}
            label="Extensive metal framework" />
          <CheckboxInput checked={form.reinforced_concrete_interconnected} onChange={set('reinforced_concrete_interconnected')}
            label="Reinforced concrete with interconnected reinforcing rods" />
          <CheckboxInput checked={form.metal_roof} onChange={set('metal_roof')} label="Metal roof" />
          <CheckboxInput checked={form.complete_roof_protection} onChange={set('complete_roof_protection')}
            label="Complete roof protection" />
        </div>
      </SectionCard>

      <SectionCard icon={<Cable size={15} />} title="Earthing & Bonding">
        <div className="space-y-3">
          <CheckboxInput checked={form.mesh_earth_termination} onChange={set('mesh_earth_termination')}
            label="Meshed earth termination system" />
          <CheckboxInput checked={form.meshed_bonding_network} onChange={set('meshed_bonding_network')}
            label="Meshed bonding network" />
          <CheckboxInput checked={form.accessible_metal_installation} onChange={set('accessible_metal_installation')}
            label="Accessible metal installations connected to LPS" />
        </div>
      </SectionCard>

      <SectionCard icon={<Radio size={15} />} title="Shielding">
        <CheckboxInput checked={form.structure_shielding} onChange={set('structure_shielding')}
          label="Structure electromagnetic shielding present" />
        {form.structure_shielding && (
          <div className="mt-4 space-y-3">
            <FormField label="Shield Mesh Width, wm1 (m)">
              <NumberInput value={form.wm1} onChange={set('wm1')} placeholder="e.g. 5.0" />
            </FormField>
            <CheckboxInput checked={form.continuous_metal_shield} onChange={set('continuous_metal_shield')}
              label="Continuous metal electromagnetic shield (≥ 0.1 mm)" />
          </div>
        )}
      </SectionCard>

      <div className="flex items-center justify-between mt-8 pt-6 border-t border-slate-100">
        <button onClick={() => navigate('/')} className="btn-secondary">← Home</button>
        <button onClick={goToLines} className="btn-primary">
          {saved ? 'Update & Continue' : 'Save & Continue'} →
        </button>
      </div>
    </div>
  )
}

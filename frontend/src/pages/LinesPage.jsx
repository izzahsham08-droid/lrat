import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAssessment } from '../context/AssessmentContext'
import {
  PageHeader, SectionCard, FormField, NumberInput, SelectInput,
  CheckboxInput, RadioGroup, NavButtons, InfoBox
} from '../components/FormComponents'
import { Plus, Pencil, Trash2, Cable, ChevronDown, ChevronUp } from 'lucide-react'

const BLANK_LINE = {
  name: '', service: null, external_cable: 'metallic',
  installation: null, type: null, environmental: null,
  LL: null, Uw: null, length_known: true,
  has_line_sections: false, sections: [],
  has_external_line: false, lightning_protective_routing: false,
  shielded: false, same_bonding_bar: false, multi_grounded_neutral: false,
  isolating_interface_protected: false, routing_precaution: false,
  mesh_bonding_network: false, equipotential_bonding_spd: false,
  equipotential_bonding_level: 'none', shield_resistance: null,
  adjacent_structure: false, L_adj: null, W_adj: null, H_adj: null, CDJ: null,
}

const BLANK_SECTION = {
  name: '', LL: null, installation: null, type: null, environmental: null,
  shielded: false, shield_resistance: 'unshielded',
}

function LineForm({ initial, onSave, onCancel }) {
  const [form, setForm] = useState(initial || BLANK_LINE)
  const set = (key) => (val) => setForm(f => ({ ...f, [key]: val }))

  const addSection = () => setForm(f => ({ ...f, sections: [...f.sections, { ...BLANK_SECTION }] }))
  const updateSection = (i, key, val) => setForm(f => ({
    ...f, sections: f.sections.map((s, idx) => idx === i ? { ...s, [key]: val } : s)
  }))
  const removeSection = (i) => setForm(f => ({ ...f, sections: f.sections.filter((_, idx) => idx !== i) }))

  const canSave = form.name && form.service && form.external_cable &&
    (form.has_line_sections
      ? form.sections.length > 0
      : (form.installation && form.type && form.environmental && (form.LL || form.length_known === false))) &&
    form.Uw

  return (
    <div className="space-y-5">
      <SectionCard title="Basic Information">
        <div className="grid grid-cols-2 gap-4">
          <FormField label="Line Name" required>
            <input className="input-field" value={form.name} onChange={e => set('name')(e.target.value)} placeholder="e.g. Main Power Line" />
          </FormField>
          <FormField label="Service Type" required>
            <SelectInput value={form.service} onChange={set('service')} options={[
              { value: 'power', label: 'Power Line' },
              { value: 'telecom', label: 'Telecommunication Line' },
            ]} />
          </FormField>
        </div>
        <div className="grid grid-cols-2 gap-4 mt-4">
          <FormField label="External Cable Type">
            <SelectInput value={form.external_cable} onChange={set('external_cable')} options={[
              { value: 'metallic',     label: 'Metallic cable' },
              { value: 'fibre_optic',  label: 'Fibre optic (not affected by lightning)' },
            ]} />
          </FormField>
          <FormField label="Impulse Withstand Voltage, Uw (kV)" required>
            <NumberInput value={form.Uw} onChange={set('Uw')} placeholder="e.g. 1.5" />
          </FormField>
        </div>
      </SectionCard>

      <SectionCard title="Line Characteristics">
        <CheckboxInput checked={form.has_line_sections} onChange={set('has_line_sections')}
          label="Divide line into sections (different installation types per segment)" />
        {form.has_line_sections && (
          <p className="text-xs text-slate-400 mt-1 ml-6">
            Use sections only if the same service has parts with different routing — for example an aerial
            section followed by a buried section, or an HV buried section followed by an LV buried section.
          </p>
        )}
        {!form.has_line_sections ? (
          <div className="mt-4 space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <FormField label="Installation Type" required>
                <SelectInput value={form.installation} onChange={set('installation')} options={[
                  { value: 'aerial',      label: 'Aerial (CI = 1)' },
                  { value: 'buried',      label: 'Buried (CI = 0.3)' },
                  { value: 'buried_mesh', label: 'Buried within meshed earth (CI = 0.01)' },
                ]} />
              </FormField>
              <FormField label="Line Type" required>
                <SelectInput value={form.type} onChange={set('type')} options={[
                  { value: 'lv_telecom_data_hv_with_transformer', label: 'LV / Telecom / HV with transformer (CT = 1)' },
                  { value: 'hv_transformer_separated',            label: 'HV with transformer separated (CT = 0.2)' },
                ]} />
              </FormField>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <FormField label="Environmental Factor" required>
                <SelectInput value={form.environmental} onChange={set('environmental')} options={[
                  { value: 'rural',        label: 'Rural (CE = 1)' },
                  { value: 'suburban',     label: 'Suburban (CE = 0.5)' },
                  { value: 'urban',        label: 'Urban (CE = 0.1)' },
                  { value: 'urban_dense',  label: 'Urban Dense (CE = 0.01)' },
                ]} />
              </FormField>
              <FormField label="Line Length, LL (m)" required={form.length_known !== false}>
                <NumberInput
                  value={form.length_known === false ? 1000 : form.LL}
                  onChange={set('LL')}
                  placeholder="e.g. 1000"
                  disabled={form.length_known === false}
                />
              </FormField>
            </div>
            <div className="-mt-1">
              <CheckboxInput
                checked={form.length_known === false}
                onChange={(checked) => set('length_known')(checked ? false : true)}
                label="I do not know the exact line length"
              />
              {form.length_known === false && (
                <p className="text-xs text-slate-400 ml-6 mt-1">
                  The tool uses the IEC simplified assumed length of 1000 m (Clause A.4). Replace it with an actual measured value if available.
                </p>
              )}
            </div>
          </div>
        ) : (
          <div className="mt-4 space-y-3">
            {form.sections.map((sec, i) => (
              <div key={i} className="bg-slate-50 rounded-xl p-4 border border-slate-100">
                <div className="flex items-center justify-between mb-3">
                  <span className="text-sm font-semibold text-slate-600">Section {i + 1}</span>
                  <button onClick={() => removeSection(i)} className="text-brand-400 hover:text-brand-600">
                    <Trash2 size={14} />
                  </button>
                </div>
                <div className="grid grid-cols-2 gap-3">
                  <FormField label="Section Name">
                    <input className="input-field" value={sec.name} onChange={e => updateSection(i, 'name', e.target.value)} placeholder={`Section ${i+1}`} />
                  </FormField>
                  <FormField label="Length (m)">
                    <NumberInput value={sec.LL} onChange={v => updateSection(i, 'LL', v)} placeholder="m" />
                  </FormField>
                  <FormField label="Installation">
                    <SelectInput value={sec.installation} onChange={v => updateSection(i, 'installation', v)} options={[
                      { value: 'aerial', label: 'Aerial' }, { value: 'buried', label: 'Buried' }, { value: 'buried_mesh', label: 'Buried mesh' },
                    ]} />
                  </FormField>
                  <FormField label="Line Type">
                    <SelectInput value={sec.type} onChange={v => updateSection(i, 'type', v)} options={[
                      { value: 'lv_telecom_data_hv_with_transformer', label: 'LV / Telecom / HV+T' },
                      { value: 'hv_transformer_separated', label: 'HV separated' },
                    ]} />
                  </FormField>
                  <FormField label="Environment">
                    <SelectInput value={sec.environmental} onChange={v => updateSection(i, 'environmental', v)} options={[
                      { value: 'rural', label: 'Rural' }, { value: 'suburban', label: 'Suburban' },
                      { value: 'urban', label: 'Urban' }, { value: 'urban_dense', label: 'Urban Dense' },
                    ]} />
                  </FormField>
                  <FormField label="Shield Resistance">
                    <SelectInput value={sec.shield_resistance} onChange={v => updateSection(i, 'shield_resistance', v)} options={[
                      { value: 'unshielded', label: 'Unshielded' },
                      { value: '5_to_20', label: '5–20 Ω/km' },
                      { value: '1_to_5', label: '1–5 Ω/km' },
                      { value: 'less_than_1', label: '< 1 Ω/km' },
                    ]} />
                  </FormField>
                </div>
              </div>
            ))}
            <button onClick={addSection} className="flex items-center gap-2 text-brand-500 hover:text-brand-600 text-sm font-medium">
              <Plus size={14} /> Add Section
            </button>
          </div>
        )}
      </SectionCard>

      <SectionCard title="Shielding, Grounding & Isolation">
        <p className="text-xs text-slate-400 mb-3">
          These affect CLD / CLI (Table B.9). If unsure, leave unticked — this gives a conservative (worst-case) result.
        </p>
        <div className="space-y-3">
          <CheckboxInput checked={form.has_external_line} onChange={set('has_external_line')}
            label="External conductive line exists"
            hint="Tick if a metallic conductive path enters the building. Untick for fibre optic or no external line (CLD = CLI = 0)." />
          <CheckboxInput checked={form.lightning_protective_routing} onChange={set('lightning_protective_routing')}
            label="Lightning protective routing (metallic conduit / protected routing)"
            hint="Tick if the line runs in a lightning-protective cable-duct, metallic conduit or metal tube bonded at both ends (CLD = 0)." />
          <CheckboxInput checked={form.shielded} onChange={set('shielded')}
            label="Shielded external line"
            hint="Tick if the external cable has a metallic shield." />
          {form.shielded && (
            <div className="ml-6 space-y-3">
              <CheckboxInput checked={form.same_bonding_bar} onChange={set('same_bonding_bar')}
                label="Shield bonded to same bonding bar as equipment"
                hint="If bonded at both ends to the same bonding bar as the equipment, CLI = 0." />
            </div>
          )}
          <CheckboxInput checked={form.multi_grounded_neutral} onChange={set('multi_grounded_neutral')}
            label="Multi-grounded neutral (power line)"
            hint="Tick for a multi-grounded neutral power line (CLI = 0.2)." />
          <CheckboxInput checked={form.isolating_interface_protected} onChange={set('isolating_interface_protected')}
            label="Protected / tested isolating interface"
            hint="Tick if a tested isolating interface is present (fibre isolation, isolation transformer, or opto-isolator) per IEC 62305-4 (CLD = 0)." />
        </div>
      </SectionCard>

      <SectionCard title="Equipotential Bonding">
        <CheckboxInput checked={form.equipotential_bonding_spd} onChange={set('equipotential_bonding_spd')}
          label="Equipotential bonding SPD installed at service entrance" />
        <div className="mt-4">
          <FormField label="Equipotential Bonding Protection Level">
            <SelectInput value={form.equipotential_bonding_level} onChange={set('equipotential_bonding_level')} options={[
              { value: 'none',   label: 'None (PEB = 1)' },
              { value: 'III-IV', label: 'Class III-IV (PEB = 0.05)' },
              { value: 'II',     label: 'Class II (PEB = 0.02)' },
              { value: 'I',      label: 'Class I (PEB = 0.01)' },
            ]} placeholder="Select level" />
          </FormField>
        </div>
        <div className="mt-3">
          <CheckboxInput checked={form.mesh_bonding_network} onChange={set('mesh_bonding_network')} label="Mesh bonding network at line entry" />
        </div>
      </SectionCard>

      <SectionCard title="Adjacent Structure (far end of line)">
        <CheckboxInput checked={form.adjacent_structure} onChange={set('adjacent_structure')}
          label="A structure is connected at the far end of this line" />
        {form.adjacent_structure && (
          <div className="mt-4 space-y-4">
            <p className="text-xs text-slate-400">
              Per Annex A Eq A.6, NDJ = NSG × ADJ × CDJ × CT × 10⁻⁶. CT is taken from this line's type.
            </p>
            <div className="grid grid-cols-3 gap-4">
              <FormField label="Length Lj (m)"><NumberInput value={form.L_adj} onChange={set('L_adj')} placeholder="0" /></FormField>
              <FormField label="Width Wj (m)"><NumberInput value={form.W_adj} onChange={set('W_adj')} placeholder="0" /></FormField>
              <FormField label="Height Hj (m)"><NumberInput value={form.H_adj} onChange={set('H_adj')} placeholder="0" /></FormField>
            </div>
            <FormField label="Adjacent Structure Location (CDJ)">
              <SelectInput value={form.CDJ} onChange={set('CDJ')} options={[
                { value: '0.25', label: 'Surrounded by higher structures (CDJ = 0.25)' },
                { value: '0.5',  label: 'Surrounded by same/smaller structures (CDJ = 0.5)' },
                { value: '1',    label: 'Isolated (CDJ = 1.0)' },
                { value: '2',    label: 'Hilltop (CDJ = 2.0)' },
              ]} placeholder="Select location" />
            </FormField>
          </div>
        )}
      </SectionCard>

      <div>
        {!canSave && (
          <p className="text-xs text-danger-500 mb-3">
            Please complete the required fields: Name, Service type, Cable type, Uw, and {form.has_line_sections ? 'at least one section' : 'Installation, Line type, Environmental factor and Line length'}.
          </p>
        )}
        <div className="flex gap-3">
          <button onClick={onCancel} className="btn-secondary">Cancel</button>
          <button onClick={() => onSave(form)} disabled={!canSave} className="btn-primary">
            Save Line
          </button>
        </div>
      </div>
    </div>
  )
}

export default function LinesPage() {
  const { linesData, addLine, updateLine, deleteLine } = useAssessment()
  const navigate = useNavigate()
  const [mode, setMode] = useState('list') // 'list' | 'add' | 'edit'
  const [editIndex, setEditIndex] = useState(null)

  const handleSave = (line) => {
    if (mode === 'edit') updateLine(editIndex, line)
    else addLine(line)
    setMode('list')
    setEditIndex(null)
  }

  return (
    <div>
      <PageHeader
        title="Line / Service Configuration"
        subtitle="Add power and telecommunication service lines connected to the building."
        step={2} totalSteps={4}
      />

      {mode === 'list' && (
        <>
          {linesData.length === 0 && (
            <InfoBox type="info">
              No service lines added yet. You may skip this step if no external lines are connected — line-related risk components will be zero.
            </InfoBox>
          )}

          {linesData.map((line, i) => (
            <div key={i} className="card card-hover mb-3 flex items-center gap-4">
              <div className="w-10 h-10 bg-brand-50 rounded-xl flex items-center justify-center shrink-0">
                <Cable size={16} className="text-brand-400" />
              </div>
              <div className="flex-1 min-w-0">
                <p className="font-semibold text-slate-700 text-sm">{line.name || `Line ${i+1}`}</p>
                <p className="text-xs text-slate-400 mt-0.5 capitalize">
                  {line.service} · {line.external_cable?.replace('_', ' ')} · {line.installation || 'sectioned'} · {line.LL ? `${line.LL}m` : 'multi-section'}
                </p>
              </div>
              <div className="flex gap-2">
                <button onClick={() => { setEditIndex(i); setMode('edit') }}
                  className="p-2 text-slate-400 hover:text-brand-500 hover:bg-brand-50 rounded-lg transition-colors">
                  <Pencil size={14} />
                </button>
                <button onClick={() => deleteLine(i)}
                  className="p-2 text-slate-400 hover:text-brand-600 hover:bg-brand-50 rounded-lg transition-colors">
                  <Trash2 size={14} />
                </button>
              </div>
            </div>
          ))}

          <button onClick={() => setMode('add')}
            className="w-full border-2 border-dashed border-brand-200 hover:border-brand-400 hover:bg-brand-50/50 rounded-xl py-4 flex items-center justify-center gap-2 text-brand-400 hover:text-brand-500 font-medium text-sm transition-all mt-2">
            <Plus size={16} /> Add Line
          </button>

          <NavButtons
            onBack={() => navigate('/building')}
            onNext={() => navigate('/zones')}
            nextLabel="Continue to Zones"
          />
        </>
      )}

      {(mode === 'add' || mode === 'edit') && (
        <>
          <div className="flex items-center gap-3 mb-6">
            <h2 className="text-lg font-semibold text-slate-700">
              {mode === 'edit' ? `Edit: ${linesData[editIndex]?.name || `Line ${editIndex+1}`}` : 'Add New Line'}
            </h2>
          </div>
          <LineForm
            initial={mode === 'edit' ? linesData[editIndex] : null}
            onSave={handleSave}
            onCancel={() => { setMode('list'); setEditIndex(null) }}
          />
        </>
      )}
    </div>
  )
}

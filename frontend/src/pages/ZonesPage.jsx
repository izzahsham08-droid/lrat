import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAssessment } from '../context/AssessmentContext'
import {
  PageHeader, SectionCard, FormField, NumberInput, SelectInput,
  CheckboxInput, MultiCheckbox, NavButtons, InfoBox
} from '../components/FormComponents'
import { Plus, Pencil, Trash2, MapPin } from 'lucide-react'
import LossGuide from '../components/LossGuide'

const BLANK_ZONE = {
  name: '',
  people_present: false, people_exposed_on_structure: false, people_in_LPS_area: false,
  internal_system_present: false,
  tz: null, te: null,
  floor_type: null, touch_protection: [],
  fire_risk: null, fire_protection: [],
  explosion_zone: false, lithium_battery_zone: false,
  explosion_zone_type: null, explosive_presence_per_year: null,
  negligible_extent: false, direct_strike_protected: false,
  metal_shelter: false, lps_protected: false,
  natural_lps_structure: false, internal_system_protected: false,
  internal_shielding: false, wm2: null, continuous_internal_shield: false,
  meshed_bonding_network: false,
  has_power_internal_system: false, has_telecom_internal_system: false,
  power_internal_wiring: null, telecom_internal_wiring: null,
  power_spd_level: 'none', power_use_custom_pspd: false, power_custom_pspd: null,
  telecom_spd_level: 'none', telecom_use_custom_pspd: false, telecom_custom_pspd: null,
  loss_category: null,
  LT_applicable: true, LD_applicable: false, LD_value_level: null,
  LF1_applicable: false, LF1_value_level: null,
  LF2_applicable: false, LF2_value_level: null,
  LO1_applicable: false, LO1_value_level: null,
  LO2_applicable: false, LO2_value_level: null,
  internal_system_hazard: false, environmental_hazard: false, pv_dc_fire_risk: false,
  annex_E_applicable: false, annex_E_scenario: null, annex_E_spread_area: null,
  annex_E_surrounding_types: [],
  fire_explosion_can_injure_surroundings: false, internal_failure_can_injure_surroundings: false,
  fire_explosion_can_damage_surroundings: false, internal_failure_can_damage_surroundings: false,
  RT: 1e-5, FT: 5e-2,
}

const SPD_OPTIONS = [
  { value: 'none',       label: 'No SPD (PSPD = 1)' },
  { value: 'III_IV',     label: 'SPD Class III / IV (PSPD = 0.05)' },
  { value: 'II',         label: 'SPD Class II (PSPD = 0.02)' },
  { value: 'I',          label: 'SPD Class I (PSPD = 0.01)' },
  { value: 'better_2_5', label: 'Better than LPL I — 2.5 kA (PSPD = 1×10⁻⁴)' },
  { value: 'better_3_75',label: 'Better than LPL I — 3.75 kA (PSPD = 5×10⁻⁵)' },
  { value: 'better_5',   label: 'Better than LPL I — 5 kA (PSPD = 1×10⁻⁵)' },
  { value: 'custom',     label: 'Custom PSPD (from Annex D investigation)' },
]

const KS3_OPTIONS = [
  { value: 'unshielded_no_routing_precaution', label: 'Unshielded — different routing, ≥0.5 m spacing, large building ~50 m² (KS3 = 1)' },
  { value: 'unshielded_routing_precaution',    label: 'Unshielded — same conduit ≤0.25 m, or small building ~25 m² (KS3 = 0.5)' },
  { value: 'unshielded_same_conduit',          label: 'Unshielded — same conduit ≤0.1 m, or small building ~10 m² (KS3 = 0.2)' },
  { value: 'unshielded_same_cable',            label: 'Unshielded — loop conductors in same cable, ~0.5 m² (KS3 = 0.01)' },
  { value: 'shielded_cable_bonded',            label: 'Shielded cables / metal conduits, bonded both ends (KS3 = 0.0001)' },
]

const LOSS_MAP = {
  very_high: { LF1: ['lower','upper'], LF2: ['lower','upper'], LO1: ['lower','upper'], LO2: ['lower','upper'] },
  high:      { LF1: ['lower','upper'], LF2: ['lower','upper'], LO1: ['lower','upper'], LO2: ['lower','upper'] },
  normal:    { LF1: ['lower','upper'], LF2: ['lower','upper'], LO1: ['lower','upper_note_e'], LO2: ['lower','upper_note_e'] },
  low:       { LF1: ['lower','upper'], LF2: ['lower','upper'], LO1: ['lower','upper_note_e'], LO2: ['lower','upper_note_e'] },
}

function ZoneForm({ initial, onSave, onCancel }) {
  const [form, setForm] = useState(initial ? { ...initial } : { ...BLANK_ZONE })
  const set = (key) => (val) => setForm(f => ({ ...f, [key]: val }))

  const lossOpts = form.loss_category ? LOSS_MAP[form.loss_category] : null

  const canSave = form.name && form.loss_category

  return (
    <div className="space-y-5">
      {/* General */}
      <SectionCard title="1. General Information">
        <FormField label="Zone Name" required>
          <input className="input-field" value={form.name} onChange={e => set('name')(e.target.value)} placeholder="e.g. Office Area, Roof, Electrical Room" />
        </FormField>
        <div className="grid grid-cols-2 gap-4 mt-4">
          <FormField label="Presence Time, tz (h/year)" hint="Hours people are present per year">
            <NumberInput value={form.tz} onChange={set('tz')} placeholder="e.g. 2000" />
          </FormField>
          <FormField label="Equipment Exposure Time, te (h/year)" hint="Hours equipment is in operation per year">
            <NumberInput value={form.te} onChange={set('te')} placeholder="e.g. 8760" />
          </FormField>
        </div>
        <div className="mt-4 space-y-3">
          <CheckboxInput checked={form.people_present} onChange={set('people_present')} label="People present in this zone" />
          {form.people_present && (
            <div className="ml-6 space-y-2">
              <CheckboxInput checked={form.people_exposed_on_structure} onChange={set('people_exposed_on_structure')} label="People may be exposed on the structure exterior (roof, facade)" />
              <CheckboxInput checked={form.people_in_LPS_area} onChange={set('people_in_LPS_area')} label="People are located within the LPS protected area" />
            </div>
          )}
          <CheckboxInput checked={form.internal_system_present} onChange={set('internal_system_present')} label="Internal electrical/electronic systems present" />
        </div>
      </SectionCard>

      {/* Touch protection */}
      <SectionCard title="2. Touch & Step Voltage Protection">
        <FormField label="Floor / Ground Surface Type" hint="Used for rt factor (Table B.2)">
          <SelectInput value={form.floor_type} onChange={set('floor_type')} options={[
            { value: 'agricultural', label: 'Agricultural soil (rt = 0.01)' },
            { value: 'concrete',     label: 'Concrete (rt = 0.01)' },
            { value: 'marble',       label: 'Marble (rt = 0.001)' },
            { value: 'ceramic',      label: 'Ceramic (rt = 0.001)' },
            { value: 'gravel',       label: 'Gravel (rt = 0.0001)' },
            { value: 'moquette',     label: 'Moquette (rt = 0.0001)' },
            { value: 'carpet',       label: 'Carpet (rt = 0.0001)' },
            { value: 'asphalt',      label: 'Asphalt (rt = 0.00001)' },
            { value: 'linoleum',     label: 'Linoleum (rt = 0.00001)' },
            { value: 'wood',         label: 'Wood (rt = 0.00001)' },
            { value: 'thick_insulation', label: 'Thick insulating layer (rt = 0)' },
          ]} />
        </FormField>
        <div className="mt-4">
          <p className="label">Touch & Step Voltage Protection Measures (Pam)</p>
          <MultiCheckbox
            values={form.touch_protection}
            onChange={set('touch_protection')}
            options={[
              { value: 'warning_notice',           label: 'Warning notice (Pam = 0.1)' },
              { value: 'electrical_insulation',    label: 'Electrical insulation of exposed parts (Pam = 0.01)' },
              { value: 'soil_equipotentialization',label: 'Effective soil equipotentialization (Pam = 0.01)' },
              { value: 'access_restriction',       label: 'Physical access restriction (Pam = 0)' },
            ]}
          />
        </div>
      </SectionCard>

      {/* Fire */}
      <SectionCard title="3. Fire & Explosion Risk">
        <div className="grid grid-cols-2 gap-4 mb-4">
          <FormField label="Fire Risk Level (rf)">
            <SelectInput value={form.fire_risk} onChange={set('fire_risk')} options={[
              { value: 'none',     label: 'None (rf = 0)' },
              { value: 'low',     label: 'Low (rf = 0.001)' },
              { value: 'ordinary',label: 'Ordinary (rf = 0.01)' },
              { value: 'high',    label: 'High (rf = 0.1)' },
            ]} />
          </FormField>
        </div>
        <p className="label mb-2">Fire Protection Measures (rP)</p>
        <MultiCheckbox
          values={form.fire_protection}
          onChange={set('fire_protection')}
          options={[
            { value: 'extinguishers',           label: 'Fire extinguishers (rP = 0.5)' },
            { value: 'hydrants',                label: 'Hydrants (rP = 0.5)' },
            { value: 'manual_alarm',            label: 'Manual alarm (rP = 0.5)' },
            { value: 'fire_compartments',       label: 'Fire compartments (rP = 0.5)' },
            { value: 'escape_route',            label: 'Escape routes (rP = 0.5)' },
            { value: 'automatic_alarm',         label: 'Automatic alarm (rP = 0.2)' },
            { value: 'automatic_extinguishing', label: 'Automatic extinguishing (rP = 0.2)' },
          ]}
        />
        <div className="divider" />
        <div className="space-y-3">
          <CheckboxInput checked={form.explosion_zone} onChange={set('explosion_zone')} label="Explosion risk zone" />
          {form.explosion_zone && (
            <div className="ml-6 space-y-3">
              <FormField label="Explosion Zone Classification">
                <SelectInput value={form.explosion_zone_type} onChange={set('explosion_zone_type')} options={[
                  { value: 'zone_0',        label: 'Zone 0 — Continuous explosive atmosphere (rf = 1)' },
                  { value: 'zone_1',        label: 'Zone 1 — Likely explosive atmosphere (rf = 0.1)' },
                  { value: 'zone_2',        label: 'Zone 2 — Unlikely explosive atmosphere (rf = 0.001)' },
                  { value: 'zone_20',       label: 'Zone 20 — Combustible dust, continuous (rf = 1)' },
                  { value: 'zone_21',       label: 'Zone 21 — Combustible dust, likely (rf = 0.1)' },
                  { value: 'zone_22',       label: 'Zone 22 — Combustible dust, unlikely (rf = 0.001)' },
                  { value: 'solid_explosive',label: 'Solid explosive (rf = 1)' },
                ]} />
              </FormField>
              <FormField label="Explosive presence time (h/year)" hint="Leave blank if always present">
                <NumberInput value={form.explosive_presence_per_year} onChange={set('explosive_presence_per_year')} placeholder="h/year" />
              </FormField>
              <p className="text-xs font-medium text-slate-600 mt-2">Conditions that reduce explosion risk (Note 7):</p>
              <div className="space-y-2">
                {[
                  ['negligible_extent','Negligible extent of explosive atmosphere'],
                  ['direct_strike_protected','Hazardous area cannot be hit by direct strike'],
                  ['metal_shelter','Hazardous area enclosed in metallic shelter'],
                  ['lps_protected','Hazardous area protected by LPS'],
                  ['natural_lps_structure','Structure acts as natural LPS'],
                  ['internal_system_protected','Internal systems protected against overvoltages'],
                ].map(([key, label]) => (
                  <CheckboxInput key={key} checked={form[key]} onChange={set(key)} label={label} />
                ))}
              </div>
            </div>
          )}
          <CheckboxInput checked={form.lithium_battery_zone} onChange={set('lithium_battery_zone')}
            label="Lithium battery zone (rP forced to 1)" />
        </div>
      </SectionCard>

      {/* Shielding & Wiring */}
      <SectionCard title="4. Zone Shielding & Internal Wiring">
        <div className="space-y-3 mb-4">
          <CheckboxInput checked={form.internal_shielding} onChange={set('internal_shielding')} label="Zone / internal shielding exists" />
          {form.internal_shielding && (
            <div className="ml-6 space-y-3">
              <FormField label="Shield Mesh Width, wm2 (m)">
                <NumberInput value={form.wm2} onChange={set('wm2')} placeholder="e.g. 5.0" />
              </FormField>
              <CheckboxInput checked={form.continuous_internal_shield} onChange={set('continuous_internal_shield')} label="Continuous internal metal shield" />
              <CheckboxInput checked={form.meshed_bonding_network} onChange={set('meshed_bonding_network')} label="Meshed bonding network inside zone" />
            </div>
          )}
        </div>
        {form.internal_system_present && (
          <>
            <div className="divider" />
            <p className="text-xs text-slate-400 mb-3">
              Indicate which metallic internal systems exist in this zone. If a service is metal-free fibre optic
              both externally and internally (e.g. hospital telecom), leave it unticked — it is neglected.
              If the external line is fibre but internal wiring is metallic copper (e.g. office telecom), tick it.
            </p>
            <div className="space-y-4">
              <div>
                <CheckboxInput checked={form.has_power_internal_system} onChange={set('has_power_internal_system')} label="Metallic power internal system present" />
                {form.has_power_internal_system && (
                  <div className="ml-6 mt-2">
                    <FormField label="Power Internal Wiring (KS3)">
                      <SelectInput value={form.power_internal_wiring} onChange={set('power_internal_wiring')} options={KS3_OPTIONS} />
                    </FormField>
                  </div>
                )}
              </div>
              <div>
                <CheckboxInput checked={form.has_telecom_internal_system} onChange={set('has_telecom_internal_system')} label="Metallic telecom internal system present" />
                {form.has_telecom_internal_system && (
                  <div className="ml-6 mt-2">
                    <FormField label="Telecom Internal Wiring (KS3)">
                      <SelectInput value={form.telecom_internal_wiring} onChange={set('telecom_internal_wiring')} options={KS3_OPTIONS} />
                    </FormField>
                  </div>
                )}
              </div>
            </div>
          </>
        )}
      </SectionCard>

      {/* SPD */}
      <SectionCard title="5. Internal System SPD Protection">
        <InfoBox type="info">
          SPD protection is set per zone. Values follow Annex B Table B.7 (power) and B.8 (telecom).
          If you have performed a detailed Annex D investigation, choose "Custom PSPD" to enter your own value.
        </InfoBox>
        <div className="grid grid-cols-2 gap-6">
          <div>
            <p className="label mb-3">Power System SPD</p>
            <FormField label="SPD Level">
              <SelectInput value={form.power_spd_level} onChange={set('power_spd_level')} options={SPD_OPTIONS} placeholder="Select level" />
            </FormField>
            {form.power_spd_level === 'custom' && (
              <div className="mt-3">
                <FormField label="Custom Power PSPD Value"
                  hint="Enter a value between 0 and 1 obtained from an Annex D / IEC 62305-4 investigation.">
                  <NumberInput value={form.power_custom_pspd} onChange={v => { set('power_use_custom_pspd')(true); set('power_custom_pspd')(v) }} placeholder="e.g. 0.0003" min={0} max={1} step={0.00001} />
                </FormField>
              </div>
            )}
          </div>
          <div>
            <p className="label mb-3">Telecom System SPD</p>
            <FormField label="SPD Level">
              <SelectInput value={form.telecom_spd_level} onChange={set('telecom_spd_level')} options={SPD_OPTIONS} placeholder="Select level" />
            </FormField>
            {form.telecom_spd_level === 'custom' && (
              <div className="mt-3">
                <FormField label="Custom Telecom PSPD Value"
                  hint="Enter a value between 0 and 1 obtained from an Annex D / IEC 62305-4 investigation.">
                  <NumberInput value={form.telecom_custom_pspd} onChange={v => { set('telecom_use_custom_pspd')(true); set('telecom_custom_pspd')(v) }} placeholder="e.g. 0.0003" min={0} max={1} step={0.00001} />
                </FormField>
              </div>
            )}
          </div>
        </div>
      </SectionCard>

      {/* Loss */}
      <SectionCard title="6. Loss Classification (Annex C)">
        <LossGuide />
        <FormField label="Zone Loss Category" required>
          <SelectInput value={form.loss_category} onChange={set('loss_category')} options={[
            { value: 'very_high', label: 'Very High Loss — Explosion risk, ICU, life-saving systems' },
            { value: 'high',      label: 'High Loss — Hospitals, control rooms, power stations' },
            { value: 'normal',    label: 'Normal — Offices, hotels, schools, public buildings' },
            { value: 'low',       label: 'Low — Residential, farmhouses, private buildings' },
          ]} />
        </FormField>
        {form.loss_category && (
          <div className="mt-4 space-y-3">
            <div className="divider" />
            <p className="text-xs font-semibold text-slate-500 uppercase tracking-wide">Applicable Loss Components</p>
            <p className="text-xs text-slate-400 mb-2">Tick the loss components that apply. Each uses the maximum value from Table C.2 for the selected category (IEC recommended default).</p>
            <CheckboxInput checked={form.LT_applicable} onChange={set('LT_applicable')} label="LT — Injury to living beings (touch/step voltage)" />
            <CheckboxInput checked={form.LD_applicable} onChange={set('LD_applicable')} label="LD — Injury due to direct strike" />
            <CheckboxInput checked={form.LF1_applicable} onChange={set('LF1_applicable')} label="LF1 — Injury to people due to fire/explosion" />
            <CheckboxInput checked={form.LF2_applicable} onChange={set('LF2_applicable')} label="LF2 — Physical damage to structure due to fire/explosion" />
            <CheckboxInput checked={form.LO1_applicable} onChange={set('LO1_applicable')} label="LO1 — Injury to people due to internal system failure" />
            <CheckboxInput checked={form.LO2_applicable} onChange={set('LO2_applicable')} label="LO2 — Loss of service due to internal system failure" />
          </div>
        )}
      </SectionCard>

      {/* Special */}
      <SectionCard title="7. Special Hazard & Environmental Conditions">
        <div className="space-y-3 mb-4">
          <CheckboxInput checked={form.internal_system_hazard} onChange={set('internal_system_hazard')}
            label="Internal system failure may cause hazard (Note e condition)"
            hint="Tick if equipment failure can directly injure people or create a dangerous condition — e.g. hospital life-support, explosion control, emergency safety, or pollution control systems." />
          <CheckboxInput checked={form.environmental_hazard} onChange={set('environmental_hazard')}
            label="Environmental hazard present"
            hint="Tick if lightning-related damage can release chemical, biological, radioactive, toxic, or polluting material." />
          <CheckboxInput checked={form.pv_dc_fire_risk} onChange={set('pv_dc_fire_risk')}
            label="PV DC fire risk present"
            hint="Tick if the zone contains PV DC circuits where surge-related equipment failure may start or propagate fire." />
        </div>
        <div className="divider" />
        <CheckboxInput checked={form.annex_E_applicable} onChange={set('annex_E_applicable')}
          label="Consequences may affect areas outside the structure (Annex E)"
          hint="Tick if fire, explosion, toxic fumes, water pollution, soil pollution, or other effects can spread outside the building. Additional Annex E environmental loss assessment then applies." />
        {form.annex_E_applicable && (
          <div className="mt-4 space-y-4">
            <FormField label="Environmental Damage Scenario">
              <SelectInput value={form.annex_E_scenario} onChange={set('annex_E_scenario')} options={[
                { value: 'explosion_overpressure', label: 'Explosion overpressure' },
                { value: 'thermal_flux',           label: 'Thermal flux' },
                { value: 'toxic_fumes',            label: 'Toxic fumes' },
                { value: 'soil_pollution',         label: 'Soil pollution' },
                { value: 'water_pollution',        label: 'Water pollution' },
                { value: 'radioactive_material',   label: 'Radioactive material' },
              ]} />
            </FormField>
            <FormField label="Spread Area">
              <SelectInput value={form.annex_E_spread_area} onChange={set('annex_E_spread_area')} options={[
                { value: 'inside_site_fence',  label: 'Effects confined within site fence' },
                { value: 'outside_site_fence', label: 'Effects may extend outside site fence' },
              ]} />
            </FormField>
            <div className="space-y-2">
              <CheckboxInput checked={form.fire_explosion_can_injure_surroundings} onChange={set('fire_explosion_can_injure_surroundings')} label="Fire or explosion can injure people outside the structure" />
              <CheckboxInput checked={form.internal_failure_can_injure_surroundings} onChange={set('internal_failure_can_injure_surroundings')} label="Internal system failure can injure people outside" />
              <CheckboxInput checked={form.fire_explosion_can_damage_surroundings} onChange={set('fire_explosion_can_damage_surroundings')} label="Fire or explosion can damage surrounding environment" />
              <CheckboxInput checked={form.internal_failure_can_damage_surroundings} onChange={set('internal_failure_can_damage_surroundings')} label="Internal system failure can damage surrounding environment" />
            </div>
          </div>
        )}
      </SectionCard>

      <div className="flex gap-3">
        <button onClick={onCancel} className="btn-secondary">Cancel</button>
        <button onClick={() => onSave(form)} disabled={!canSave} className="btn-primary">
          Save Zone
        </button>
      </div>
    </div>
  )
}

export default function ZonesPage() {
  const { zonesData, addZone, updateZone, deleteZone } = useAssessment()
  const navigate = useNavigate()
  const [mode, setMode] = useState('list')
  const [editIndex, setEditIndex] = useState(null)

  const handleSave = (zone) => {
    if (mode === 'edit') updateZone(editIndex, zone)
    else addZone(zone)
    setMode('list')
    setEditIndex(null)
  }

  return (
    <div>
      <PageHeader
        title="Risk Zones"
        subtitle="Define each zone of the building with its specific exposure, protection, and loss data."
        step={3} totalSteps={4}
      />

      {mode === 'list' && (
        <>
          {zonesData.length === 0 && (
            <InfoBox type="warning">No zones added yet. At least one zone is required to run the assessment.</InfoBox>
          )}

          {zonesData.map((zone, i) => (
            <div key={i} className="card card-hover mb-3 flex items-center gap-4">
              <div className="w-10 h-10 bg-brand-50 rounded-xl flex items-center justify-center shrink-0">
                <MapPin size={16} className="text-brand-400" />
              </div>
              <div className="flex-1 min-w-0">
                <p className="font-semibold text-slate-700 text-sm">{zone.name || `Zone ${i+1}`}</p>
                <p className="text-xs text-slate-400 mt-0.5">
                  {zone.loss_category?.replace('_',' ')} loss · {zone.people_present ? 'people present' : 'no people'} · {zone.internal_system_present ? 'internal systems' : 'no internal systems'}
                </p>
              </div>
              <div className="flex gap-2">
                <button onClick={() => { setEditIndex(i); setMode('edit') }}
                  className="p-2 text-slate-400 hover:text-brand-500 hover:bg-brand-50 rounded-lg transition-colors">
                  <Pencil size={14} />
                </button>
                <button onClick={() => deleteZone(i)}
                  className="p-2 text-slate-400 hover:text-brand-600 hover:bg-brand-50 rounded-lg transition-colors">
                  <Trash2 size={14} />
                </button>
              </div>
            </div>
          ))}

          <button onClick={() => setMode('add')}
            className="w-full border-2 border-dashed border-brand-200 hover:border-brand-400 hover:bg-brand-50/50 rounded-xl py-4 flex items-center justify-center gap-2 text-brand-400 hover:text-brand-500 font-medium text-sm transition-all mt-2">
            <Plus size={16} /> Add Zone
          </button>

          <NavButtons
            onBack={() => navigate('/lines')}
            onNext={() => navigate('/results')}
            nextLabel="Go to Results"
            nextDisabled={zonesData.length === 0}
          />
        </>
      )}

      {(mode === 'add' || mode === 'edit') && (
        <>
          <div className="flex items-center gap-3 mb-6">
            <h2 className="text-lg font-semibold text-slate-700">
              {mode === 'edit' ? `Edit: ${zonesData[editIndex]?.name || `Zone ${editIndex+1}`}` : 'Add New Zone'}
            </h2>
          </div>
          <ZoneForm
            initial={mode === 'edit' ? zonesData[editIndex] : null}
            onSave={handleSave}
            onCancel={() => { setMode('list'); setEditIndex(null) }}
          />
        </>
      )}
    </div>
  )
}

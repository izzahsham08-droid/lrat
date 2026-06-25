import { ChevronDown } from 'lucide-react'

export function FormField({ label, hint, required, children }) {
  return (
    <div className="space-y-1.5">
      <label className="label">
        {label}
        {required && <span className="text-brand-400 ml-1">*</span>}
      </label>
      {children}
      {hint && <p className="text-xs text-slate-400">{hint}</p>}
    </div>
  )
}

export function TextInput({ value, onChange, placeholder, type = 'text', min, step, ...props }) {
  return (
    <input
      type={type}
      value={value ?? ''}
      onChange={e => onChange(type === 'number' ? (e.target.value === '' ? null : Number(e.target.value)) : e.target.value)}
      placeholder={placeholder}
      min={min}
      step={step}
      className="input-field"
      {...props}
    />
  )
}

export function NumberInput({ value, onChange, placeholder, min = 0, step = 'any', ...props }) {
  return (
    <input
      type="number"
      value={value ?? ''}
      onChange={e => onChange(e.target.value === '' ? null : Number(e.target.value))}
      placeholder={placeholder ?? ''}
      min={min}
      step={step}
      className={`input-field ${props.disabled ? 'bg-slate-50 text-slate-400 cursor-not-allowed' : ''}`}
      {...props}
    />
  )
}

export function SelectInput({ value, onChange, options, placeholder = 'Select...', ...props }) {
  // options: [{value, label}]
  return (
    <div className="relative">
      <select
        value={value ?? ''}
        onChange={e => onChange(e.target.value === '' ? null : e.target.value)}
        className={`input-field appearance-none pr-10 ${!value ? 'text-slate-400' : 'text-slate-800'}`}
        {...props}
      >
        <option value="">{placeholder}</option>
        {options.map(o => (
          <option key={o.value} value={o.value}>{o.label}</option>
        ))}
      </select>
      <ChevronDown size={15} className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 pointer-events-none" />
    </div>
  )
}

export function CheckboxInput({ checked, onChange, label, hint }) {
  return (
    <label className="flex items-start gap-3 cursor-pointer group">
      <div className="relative mt-0.5">
        <input
          type="checkbox"
          checked={!!checked}
          onChange={e => onChange(e.target.checked)}
          className="sr-only"
        />
        <div className={`w-4.5 h-4.5 w-[18px] h-[18px] rounded-[5px] border-2 flex items-center justify-center transition-all
          ${checked ? 'bg-brand-500 border-brand-500' : 'border-slate-300 bg-white group-hover:border-brand-300'}`}>
          {checked && (
            <svg width="10" height="8" viewBox="0 0 10 8" fill="none">
              <path d="M1 4L3.5 6.5L9 1" stroke="white" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"/>
            </svg>
          )}
        </div>
      </div>
      <div>
        <span className="text-sm text-slate-700 font-medium">{label}</span>
        {hint && <p className="text-xs text-slate-400 mt-0.5">{hint}</p>}
      </div>
    </label>
  )
}

export function RadioGroup({ value, onChange, options }) {
  return (
    <div className="space-y-2">
      {options.map(o => (
        <label key={o.value} className="flex items-center gap-3 cursor-pointer group">
          <div className={`w-[18px] h-[18px] rounded-full border-2 flex items-center justify-center transition-all
            ${value === o.value ? 'border-brand-500' : 'border-slate-300 group-hover:border-brand-300'}`}>
            {value === o.value && <div className="w-[8px] h-[8px] rounded-full bg-brand-500" />}
          </div>
          <span className="text-sm text-slate-700">{o.label}</span>
        </label>
      ))}
    </div>
  )
}

export function MultiCheckbox({ values = [], onChange, options }) {
  const toggle = (val) => {
    if (values.includes(val)) onChange(values.filter(v => v !== val))
    else onChange([...values, val])
  }
  return (
    <div className="space-y-2">
      {options.map(o => (
        <CheckboxInput
          key={o.value}
          checked={values.includes(o.value)}
          onChange={() => toggle(o.value)}
          label={o.label}
          hint={o.hint}
        />
      ))}
    </div>
  )
}

export function SectionCard({ title, icon, children, accent = false }) {
  return (
    <div className={`card mb-5 ${accent ? 'border-brand-100' : ''}`}>
      {title && (
        <div className="section-title">
          {icon && (
            <span className="w-7 h-7 rounded-lg bg-brand-50 text-brand-500 flex items-center justify-center shrink-0">
              {icon}
            </span>
          )}
          {title}
        </div>
      )}
      {children}
    </div>
  )
}

export function PageHeader({ title, subtitle, step, totalSteps }) {
  return (
    <div className="mb-8">
      {step && (
        <div className="flex items-center gap-2 mb-3">
          <span className="text-xs font-semibold text-brand-400 uppercase tracking-widest">
            Step {step} of {totalSteps}
          </span>
          <div className="flex-1 h-1 bg-slate-100 rounded-full overflow-hidden">
            <div
              className="h-full bg-gradient-to-r from-brand-400 to-brand-500 rounded-full transition-all duration-500"
              style={{ width: `${(step / totalSteps) * 100}%` }}
            />
          </div>
        </div>
      )}
      <h1 className="text-2xl font-bold text-slate-800">{title}</h1>
      {subtitle && <p className="text-slate-500 mt-1.5 text-sm">{subtitle}</p>}
    </div>
  )
}

export function NavButtons({ onBack, onNext, backLabel, nextLabel = 'Save & Continue', nextDisabled }) {
  return (
    <div className="flex items-center justify-between mt-8 pt-6 border-t border-slate-100">
      {onBack ? (
        <button onClick={onBack} className="btn-secondary">← {backLabel || 'Back'}</button>
      ) : <div />}
      {onNext && (
        <button onClick={onNext} disabled={nextDisabled} className="btn-primary">
          {nextLabel} →
        </button>
      )}
    </div>
  )
}

export function InfoBox({ children, type = 'info' }) {
  const styles = {
    info:    'bg-blue-50 border-blue-200 text-blue-700',
    warning: 'bg-amber-50 border-amber-200 text-amber-700',
    success: 'bg-teal-50 border-teal-200 text-teal-700',
    error:   'bg-danger-50 border-danger-100 text-danger-600',
  }
  return (
    <div className={`text-sm px-4 py-3 rounded-xl border ${styles[type]} mb-4`}>
      {children}
    </div>
  )
}

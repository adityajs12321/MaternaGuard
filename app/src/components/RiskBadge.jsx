const configs = {
  low: { label: 'Low Risk', class: 'bg-emerald-100 text-emerald-800 border border-emerald-200' },
  mid: { label: 'Mid Risk', class: 'bg-amber-100 text-amber-800 border border-amber-200' },
  high: { label: 'High Risk', class: 'bg-rose-100 text-rose-800 border border-rose-200' },
};

export default function RiskBadge({ level = 'low', size = 'sm' }) {
  const cfg = configs[level] || configs.low;
  return (
    <span className={`inline-flex items-center px-2.5 py-1 rounded-full font-medium whitespace-nowrap ${cfg.class} ${size === 'lg' ? 'text-base' : 'text-xs'}`}>
      {cfg.label}
    </span>
  );
}
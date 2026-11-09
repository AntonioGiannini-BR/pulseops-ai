interface KpiCardProps {
  title: string
  value: number | string
  description: string
  icon: string
  color: 'blue' | 'purple' | 'green' | 'orange'
}

export default function KpiCard({
  title,
  value,
  description,
  icon,
  color,
}: KpiCardProps) {
  return (
    <article className="kpi-card">
      <div className="kpi-top">
        <span>{title}</span>

        <span
          className={`kpi-icon k-${color}`}
          aria-hidden="true"
        >
          {icon}
        </span>
      </div>

      <div className="kpi-value">{value}</div>

      <div className="kpi-foot">{description}</div>
    </article>
  )
}

import {
  PieChart,
  Pie,
  Cell,
  Tooltip,
  ResponsiveContainer,
} from 'recharts'

import type { DashboardDistribution } from '../types/api'

interface PriorityChartProps {
  distribution: DashboardDistribution | null
}

const priorityConfig = [
  { key: 'baixa', name: 'Baixa', color: '#3B82F6' },
  { key: 'media', name: 'Média', color: '#F59E0B' },
  { key: 'alta', name: 'Alta', color: '#F97316' },
  { key: 'critica', name: 'Crítica', color: '#EF4444' },
] as const

export default function PriorityChart({
  distribution,
}: PriorityChartProps) {
  if (!distribution) {
    return <p>Carregando prioridades...</p>
  }

  const data = priorityConfig.map((priority) => ({
    name: priority.name,
    value: distribution.por_prioridade[priority.key],
    color: priority.color,
  }))

  const total = data.reduce(
    (sum, item) => sum + item.value,
    0,
  )

  return (
    <div className="chart-card">
      <div className="chart-header">
        <h3>Chamados por prioridade</h3>
        <p>Distribuição por nível de urgência</p>
      </div>

      <div
        style={{
          width: '100%',
          height: 280,
          position: 'relative',
        }}
      >
        <ResponsiveContainer width="100%" height="100%">
          <PieChart>
            <Pie
              data={data}
              dataKey="value"
              nameKey="name"
              cx="50%"
              cy="50%"
              innerRadius={75}
              outerRadius={105}
              paddingAngle={3}
              stroke="none"
            >
              {data.map((item) => (
                <Cell
                  key={item.name}
                  fill={item.color}
                />
              ))}
            </Pie>

            <Tooltip />
          </PieChart>
        </ResponsiveContainer>

        <div
          style={{
            position: 'absolute',
            top: '50%',
            left: '50%',
            transform: 'translate(-50%, -50%)',
            textAlign: 'center',
            pointerEvents: 'none',
          }}
        >
          <strong
            style={{
              display: 'block',
              fontSize: 30,
              color: '#0F172A',
            }}
          >
            {total}
          </strong>

          <span
            style={{
              fontSize: 12,
              color: '#64748B',
            }}
          >
            Chamados
          </span>
        </div>
      </div>

      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(2, 1fr)',
          gap: 12,
          marginTop: 12,
        }}
      >
        {data.map((item) => (
          <div
            key={item.name}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: 8,
              fontSize: 13,
              color: '#475569',
            }}
          >
            <span
              style={{
                width: 10,
                height: 10,
                borderRadius: '50%',
                backgroundColor: item.color,
              }}
            />

            <span>{item.name}</span>

            <strong style={{ marginLeft: 'auto' }}>
              {item.value}
            </strong>
          </div>
        ))}
      </div>
    </div>
  )
}

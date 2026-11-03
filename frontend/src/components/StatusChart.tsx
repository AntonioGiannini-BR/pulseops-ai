import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from 'recharts'

import type { DashboardDistribution } from '../types/api'

interface StatusChartProps {
  distribution: DashboardDistribution | null
}

const statusConfig = [
  { key: 'aberto', name: 'Abertos', color: '#3B82F6' },
  { key: 'em_triagem', name: 'Em triagem', color: '#8B5CF6' },
  { key: 'em_atendimento', name: 'Em atendimento', color: '#6366F1' },
  { key: 'resolvido', name: 'Resolvidos', color: '#10B981' },
  { key: 'fechado', name: 'Fechados', color: '#64748B' },
] as const

export default function StatusChart({
  distribution,
}: StatusChartProps) {
  if (!distribution) {
    return <p>Carregando distribuição dos chamados...</p>
  }

  const data = statusConfig.map((status) => ({
    name: status.name,
    total: distribution.por_status[status.key],
    color: status.color,
  }))

  return (
    <div className="chart-card">
      <div className="chart-header">
        <h3>Chamados por status</h3>
        <p>Distribuição atual dos chamados da operação</p>
      </div>

      <div style={{ width: '100%', height: 300 }}>
        <ResponsiveContainer width="100%" height="100%">
          <BarChart
            data={data}
            layout="vertical"
            margin={{ top: 10, right: 25, left: 20, bottom: 10 }}
          >
            <CartesianGrid
              strokeDasharray="3 3"
              horizontal={false}
              stroke="#E2E8F0"
            />

            <XAxis
              type="number"
              allowDecimals={false}
              tick={{ fill: '#64748B', fontSize: 12 }}
            />

            <YAxis
              dataKey="name"
              type="category"
              width={110}
              tick={{ fill: '#64748B', fontSize: 12 }}
            />

            <Tooltip
              formatter={(value) => [value, 'Chamados']}
            />

            <Bar
              dataKey="total"
              radius={[0, 6, 6, 0]}
              barSize={22}
            >
              {data.map((item) => (
                <Cell
                  key={item.name}
                  fill={item.color}
                />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  )
}

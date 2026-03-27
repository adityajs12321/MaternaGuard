import { format } from 'date-fns';
import { Heart, Activity, Thermometer, Droplets } from 'lucide-react';
import RiskBadge from './RiskBadge';
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts';

export default function PatientDetail({ patient, logs }) {
  const latest = logs[0];

  const chartData = [...logs].reverse().slice(-10).map(l => ({
    date: format(new Date(l.original_timestamp), 'MMM d'),
    systolic: l.sbp,
    diastolic: l.dbp,
  }));

  return (
    <div className="space-y-6">
      {/* Profile info */}
      <div className="grid grid-cols-2 gap-3 text-sm">
        <div><span className="text-muted-foreground">ABHA:</span> <span className="font-medium">{patient.abha_id || 'Not Provided'}</span></div>
        <div><span className="text-muted-foreground">Device:</span> <span className="font-medium">{patient.latest_device_id}</span></div>
        <div><span className="text-muted-foreground">Entries:</span> <span className="font-medium">{patient.total_assessments}</span></div>
        <div><span className="text-muted-foreground">High-Risk:</span> <span className="font-medium">{patient.high_risk_count}</span></div>
      </div>

      {/* Latest vitals */}
      {latest && (
        <div>
          <h3 className="text-sm font-semibold mb-3 text-foreground">Latest Vitals</h3>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            {[
              { label: 'BP', value: `${latest.sbp}/${latest.dbp}`, icon: Heart, color: 'text-red-500' },
              { label: 'HR', value: latest.heart_rate ? `${latest.heart_rate} bpm` : '—', icon: Activity, color: 'text-primary' },
              { label: 'Temp', value: latest.body_temp ? `${latest.body_temp}°C` : '—', icon: Thermometer, color: 'text-orange-500' },
              { label: 'Sugar', value: latest.blood_sugar ? `${latest.blood_sugar} mmol/L` : '—', icon: Droplets, color: 'text-blue-500' },
            ].map(({ label, value, icon: Icon, color }) => (
              <div key={label} className="bg-muted/40 rounded-xl p-3 text-center">
                <Icon className={`w-4 h-4 mx-auto mb-1 ${color}`} />
                <p className="text-xs text-muted-foreground">{label}</p>
                <p className="text-sm font-semibold">{value}</p>
              </div>
            ))}
          </div>
          <div className="mt-2 flex items-center gap-2">
            <RiskBadge level={latest.risk_level} />
            <span className="text-xs text-muted-foreground">as of {format(new Date(latest.original_timestamp), 'MMM d, h:mm a')}</span>
          </div>
        </div>
      )}

      {/* BP Chart */}
      {chartData.length > 1 && (
        <div>
          <h3 className="text-sm font-semibold mb-3 text-foreground">Blood Pressure Trend</h3>
          <ResponsiveContainer width="100%" height={160}>
            <LineChart data={chartData}>
              <XAxis dataKey="date" tick={{ fontSize: 11 }} />
              <YAxis tick={{ fontSize: 11 }} domain={['auto', 'auto']} />
              <Tooltip />
              <Line type="monotone" dataKey="systolic" stroke="hsl(var(--primary))" strokeWidth={2} dot={false} />
              <Line type="monotone" dataKey="diastolic" stroke="hsl(var(--chart-2))" strokeWidth={2} dot={false} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      )}

      {/* Recent logs */}
      {logs.length > 0 && (
        <div>
          <h3 className="text-sm font-semibold mb-3 text-foreground">Recent Assessments</h3>
          <div className="space-y-2 max-h-48 overflow-y-auto">
            {logs.slice(0, 10).map(log => (
              <div key={log.id} className="flex items-center justify-between py-2 border-b border-border last:border-0">
                <div>
                  <p className="text-xs font-medium">{format(new Date(log.original_timestamp), 'MMM d, yyyy h:mm a')}</p>
                  <p className="text-xs text-muted-foreground">Top feature: {log.top_feature || 'n/a'}</p>
                </div>
                <div className="flex items-center gap-2">
                  {log.sbp && (
                    <span className="text-xs text-muted-foreground">{log.sbp}/{log.dbp}</span>
                  )}
                  <RiskBadge level={log.risk_level} />
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
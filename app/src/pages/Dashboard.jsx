import { useState, useEffect } from 'react';
import { useOutletContext } from 'react-router-dom';
import { maternaguardApi } from '@/api/maternaguard';
import { syncPendingAssessments } from '@/lib/offlineSync';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Link } from 'react-router-dom';
import { Activity, Heart, Thermometer, Droplets, AlertTriangle, Plus, TrendingUp, Bell } from 'lucide-react';
import { format } from 'date-fns';
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts';
import RiskBadge from '@/components/RiskBadge';
import { toast } from 'sonner';

function getTimeOfDay() {
  const h = new Date().getHours();
  if (h < 12) return 'morning';
  if (h < 17) return 'afternoon';
  return 'evening';
}

export default function Dashboard() {
  const { user } = useOutletContext();
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!user?.device_id) {
      setLoading(false);
      return;
    }

    if (navigator.onLine) {
      syncPendingAssessments()
        .then((status) => {
          if (status.synced > 0) {
            toast.success(`Synced ${status.synced} offline assessment(s)`);
          }
        })
        .catch(() => {
          // Ignore sync errors here; user can still view local backend data.
        });
    }

    let cancelled = false;
    maternaguardApi
      .getDeviceAssessments(user.device_id, 30)
      .then((logsData) => {
        if (!cancelled) {
          setLogs(logsData);
        }
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, [user]);

  const normalizedLogs = logs.map((entry) => ({
    ...entry,
    sbp: Number(entry?.sbp),
    dbp: Number(entry?.dbp),
    heart_rate: Number(entry?.heart_rate),
    body_temp: Number(entry?.body_temp),
    blood_sugar: Number(entry?.blood_sugar),
  }));

  const latest = normalizedLogs[0] || null;
  const hasValidBp = latest && Number.isFinite(latest.sbp) && Number.isFinite(latest.dbp);
  const latestBp = hasValidBp ? `${latest.sbp}/${latest.dbp}` : '—';
  const alerts = normalizedLogs.filter((entry) => entry.risk_level === 'high').slice(0, 5);

  const chartData = [...normalizedLogs]
    .reverse()
    .slice(-20)
    .filter((entry) => Number.isFinite(entry.sbp) && Number.isFinite(entry.dbp))
    .map((entry, index) => ({
      date: format(new Date(entry.original_timestamp), 'MMM d'),
      label: `${format(new Date(entry.original_timestamp), 'MMM d')} #${index + 1}`,
      systolic: entry.sbp,
      diastolic: entry.dbp,
    }));

  const riskLevel = latest?.risk_level || 'low';

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="w-8 h-8 border-4 border-primary/30 border-t-primary rounded-full animate-spin" />
      </div>
    );
  }

  return (
    <div className="flex flex-col">
      {/* Header */}
      <div className="bg-primary px-5 pt-12 pb-8">
        <div className="flex items-start justify-between">
          <div>
            <p className="text-primary-foreground/70 text-sm">Good {getTimeOfDay()},</p>
            <h1 className="font-playfair text-2xl font-bold text-primary-foreground mt-0.5">
              {user?.full_name?.split(' ')[0] || 'there'}
            </h1>
          </div>
          <Link to="/alerts">
            <div className="relative w-10 h-10 rounded-full bg-white/15 flex items-center justify-center">
              <Bell size={18} className="text-white" />
              {alerts.length > 0 && (
                <span className="absolute -top-0.5 -right-0.5 w-4 h-4 bg-red-400 rounded-full text-white text-[9px] flex items-center justify-center font-bold">
                  {alerts.length}
                </span>
              )}
            </div>
          </Link>
        </div>

        {/* Week + Risk pills */}
        <div className="flex gap-3 mt-5">
          <div className="flex items-center gap-2 bg-white/15 rounded-full px-4 py-2">
            <RiskBadge level={riskLevel} />
          </div>
        </div>
      </div>

      <div className="px-4 py-5 space-y-5">
        {/* Vitals grid */}
        <div>
          <div className="flex items-center justify-between mb-3">
            <h2 className="text-sm font-semibold text-foreground">Latest Vitals</h2>
            {latest && (
              <span className="text-xs text-muted-foreground">{format(new Date(latest.original_timestamp), 'MMM d, h:mm a')}</span>
            )}
          </div>
          <div className="grid grid-cols-2 gap-3">
            {[
              { label: 'Blood Pressure', value: latestBp, unit: 'mmHg', icon: Heart, color: 'text-primary', bg: 'bg-secondary' },
              { label: 'Heart Rate', value: Number.isFinite(latest?.heart_rate) ? latest.heart_rate : '—', unit: 'bpm', icon: Activity, color: 'text-accent', bg: 'bg-secondary' },
              { label: 'Temperature', value: Number.isFinite(latest?.body_temp) ? latest.body_temp : '—', unit: '°C', icon: Thermometer, color: 'text-primary', bg: 'bg-secondary' },
              { label: 'Blood Sugar', value: Number.isFinite(latest?.blood_sugar) ? latest.blood_sugar : '—', unit: 'mmol/L', icon: Droplets, color: 'text-accent', bg: 'bg-secondary' },
            ].map(({ label, value, unit, icon: Icon, color, bg }) => (
              <Card key={label} className="border-border shadow-sm">
                <CardContent className="p-4">
                  <div className={`w-8 h-8 rounded-xl ${bg} flex items-center justify-center mb-2`}>
                    <Icon className={`w-4 h-4 ${color}`} />
                  </div>
                  <p className="text-xs text-muted-foreground">{label}</p>
                  <p className="text-lg font-bold text-foreground mt-0.5">
                    {value} <span className="text-xs font-normal text-muted-foreground">{value !== '—' ? unit : ''}</span>
                  </p>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>

        {/* BP Chart */}
        {chartData.length > 1 && (
          <Card className="border-border shadow-sm">
            <CardHeader className="pb-2 pt-4 px-4">
              <CardTitle className="text-sm font-semibold flex items-center gap-2">
                <TrendingUp size={14} className="text-primary" /> BP Trend
              </CardTitle>
            </CardHeader>
            <CardContent className="px-2 pb-4">
              <ResponsiveContainer width="100%" height={160}>
                <LineChart data={chartData}>
                  <XAxis dataKey="label" tick={{ fontSize: 10 }} interval="preserveStartEnd" />
                  <YAxis tick={{ fontSize: 10 }} domain={['auto', 'auto']} width={28} />
                  <Tooltip />
                  <Line type="monotone" dataKey="systolic" stroke="hsl(var(--primary))" strokeWidth={2} dot={false} name="Systolic" />
                  <Line type="monotone" dataKey="diastolic" stroke="hsl(var(--chart-2))" strokeWidth={2} dot={false} name="Diastolic" />
                </LineChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        )}

        {chartData.length <= 1 && normalizedLogs.length > 0 && (
          <Card className="border-border shadow-sm">
            <CardContent className="p-4 text-xs text-muted-foreground">
              Need at least two valid BP readings to draw a trend graph.
            </CardContent>
          </Card>
        )}

        {/* Active alerts */}
        {alerts.length > 0 && (
          <div>
            <h2 className="text-sm font-semibold text-foreground mb-3">Active Alerts</h2>
            <div className="space-y-2">
              {alerts.map(alert => (
                <div
                  key={alert.id}
                  className="flex items-start gap-3 p-3 rounded-xl border bg-rose-50 border-rose-200"
                >
                  <AlertTriangle className="w-4 h-4 mt-0.5 flex-shrink-0 text-rose-700" />
                  <p className="text-sm text-foreground">
                    High risk detected at {format(new Date(alert.original_timestamp), 'MMM d, h:mm a')}. Top factor: {alert.top_feature || 'n/a'}.
                  </p>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Log CTA */}
        <Link to="/log">
          <Button className="w-full bg-primary hover:bg-primary/90 h-12 text-base gap-2 rounded-2xl">
            <Plus size={18} /> Log Health Entry
          </Button>
        </Link>

        {/* Empty state */}
        {logs.length === 0 && (
          <div className="text-center py-8">
            <Activity className="w-12 h-12 text-muted-foreground/30 mx-auto mb-3" />
            <p className="text-foreground font-medium">No health logs yet</p>
            <p className="text-sm text-muted-foreground mt-1">Start tracking your vitals above</p>
          </div>
        )}
      </div>
    </div>
  );
}
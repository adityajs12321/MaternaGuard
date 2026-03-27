import { useState, useEffect } from 'react';
import { useOutletContext } from 'react-router-dom';
import { maternaguardApi } from '@/api/maternaguard';
import { getDemoSmsLog } from '@/lib/smsSimulation';
import { Badge } from '@/components/ui/badge';
import { AlertTriangle, CheckCircle2, BellOff, Clock, MessageSquareWarning } from 'lucide-react';
import { format } from 'date-fns';

const severityConfig = {
  mid: { color: 'bg-secondary border-border', icon: 'text-primary', badge: 'bg-secondary text-primary' },
  high: { color: 'bg-primary/10 border-primary', icon: 'text-primary', badge: 'bg-primary text-primary-foreground' },
  low: { color: 'bg-secondary border-border', icon: 'text-muted-foreground', badge: 'bg-muted text-foreground' },
};

export default function Alerts() {
  const { user } = useOutletContext();
  const [alerts, setAlerts] = useState([]);
  const [demoSms, setDemoSms] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState('high');
  const isAdmin = user?.role === 'admin';

  useEffect(() => {
    if (!user?.device_id || isAdmin) return;
    setLoading(true);
    maternaguardApi
      .getDeviceAssessments(user.device_id, 100)
      .then((items) => {
        const filtered = items.filter((entry) => (filter === 'all' ? true : entry.risk_level === filter));
        setAlerts(filtered);
        setDemoSms(getDemoSmsLog());
      })
      .finally(() => setLoading(false));
  }, [user, filter, isAdmin]);

  return (
    <div className="flex flex-col">
      {/* Header */}
      <div className="bg-primary px-5 pt-12 pb-5">
        <h1 className="font-playfair text-2xl font-bold text-primary-foreground">Alerts</h1>
        <p className="text-primary-foreground/70 text-sm mt-0.5">Health alerts and notifications</p>

        {/* Filter pills */}
        <div className="flex gap-2 mt-4">
          {['high', 'mid', 'all'].map(f => (
            <button
              key={f}
              onClick={() => setFilter(f)}
              className={`px-4 py-1.5 rounded-full text-xs font-medium transition-colors capitalize ${
                filter === f ? 'bg-white text-primary' : 'bg-white/20 text-white'
              }`}
            >
              {f}
            </button>
          ))}
        </div>
      </div>

      <div className="px-4 py-4">
        {demoSms.length > 0 && (
          <div className="mb-4 space-y-3">
            <div className="flex items-center gap-2">
              <MessageSquareWarning className="w-4 h-4 text-blue-700" />
              <h2 className="text-sm font-semibold text-foreground">Demo Referral SMS Log</h2>
            </div>
            {demoSms.slice(0, 3).map((entry) => (
              <div key={entry.id} className="p-3 rounded-2xl border border-blue-200 bg-gradient-to-br from-blue-50 to-sky-50 shadow-sm">
                <div className="flex items-start justify-between gap-2 mb-2">
                  <div className="flex items-center gap-2">
                    <Badge className="text-[10px] px-2 bg-blue-100 text-blue-800">Demo SMS</Badge>
                    <p className="text-xs font-medium text-blue-900">{entry.target}</p>
                  </div>
                  <span className="text-[10px] text-blue-700 whitespace-nowrap">
                    {format(new Date(entry.createdAt), 'MMM d, h:mm a')}
                  </span>
                </div>

                <div className="grid grid-cols-2 gap-x-3 gap-y-1 text-xs mb-2">
                  <p className="text-blue-900"><span className="text-blue-700">Patient:</span> {entry.patientLabel}</p>
                  <p className="text-blue-900"><span className="text-blue-700">Risk:</span> {String(entry.riskLevel || 'high').toUpperCase()}</p>
                  <p className="text-blue-900 col-span-2"><span className="text-blue-700">Top factor:</span> {entry.topFeature || 'n/a'}</p>
                </div>

                <details className="text-xs">
                  <summary className="cursor-pointer text-blue-800 font-medium">View SMS text</summary>
                  <p className="mt-2 whitespace-pre-line text-foreground/90 bg-white/70 rounded-lg p-2 border border-blue-100">
                    {entry.body}
                  </p>
                </details>
              </div>
            ))}
          </div>
        )}

        {loading ? (
          <div className="flex items-center justify-center h-40">
            <div className="w-6 h-6 border-4 border-primary/30 border-t-primary rounded-full animate-spin" />
          </div>
        ) : alerts.length === 0 ? (
          <div className="text-center py-16">
            <BellOff className="w-14 h-14 text-muted-foreground/30 mx-auto mb-4" />
            <p className="font-medium text-foreground">No alerts</p>
            <p className="text-sm text-muted-foreground mt-1">
              {filter === 'high' ? "No high-risk entries found." : "No entries in this category."}
            </p>
          </div>
        ) : (
          <div className="space-y-3">
            {alerts.map(alert => {
              const cfg = severityConfig[alert.risk_level] || severityConfig.low;
              return (
                <div key={alert.id} className={`p-4 rounded-2xl border ${cfg.color}`}>
                  <div className="flex items-start gap-3">
                    <AlertTriangle className={`w-4 h-4 mt-0.5 flex-shrink-0 ${cfg.icon}`} />
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 flex-wrap">
                        <p className="text-sm font-medium text-foreground">
                          {alert.risk_level === 'high' ? 'Immediate referral recommended.' : 'Moderate risk. Monitor closely.'}
                        </p>
                        <Badge className={`text-[10px] capitalize px-2 ${cfg.badge}`}>{alert.risk_level}</Badge>
                      </div>
                      <p className="text-xs text-muted-foreground mt-0.5">Top feature: {alert.top_feature || 'n/a'}</p>
                      <div className="flex items-center gap-1 mt-1.5">
                        <Clock size={10} className="text-muted-foreground" />
                        <p className="text-xs text-muted-foreground">
                          {format(new Date(alert.original_timestamp), 'MMM d, yyyy h:mm a')}
                        </p>
                      </div>
                      {alert.sms_sent && (
                        <div className="flex items-center gap-1 mt-0.5">
                          <CheckCircle2 size={10} className="text-green-600" />
                          <p className="text-xs text-green-700">Referral SMS sent</p>
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}
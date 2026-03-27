import { useState, useEffect } from 'react';
import { useOutletContext } from 'react-router-dom';
import { useAuth } from '@/lib/AuthContext';
import { maternaguardApi } from '@/api/maternaguard';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Users, AlertTriangle, Activity, Search, ChevronRight, Heart } from 'lucide-react';
import RiskBadge from '@/components/RiskBadge';
import PatientDetail from '@/components/PatientDetail';

export default function ProviderDashboard() {
  const { user } = useOutletContext();
  const { doctorToken, loginDoctor } = useAuth();
  const [patients, setPatients] = useState([]);
  const [logsByKey, setLogsByKey] = useState({});
  const [search, setSearch] = useState('');
  const [selectedPatient, setSelectedPatient] = useState(null);
  const [loading, setLoading] = useState(true);
  const [loginLoading, setLoginLoading] = useState(false);
  const [loginForm, setLoginForm] = useState({ username: '', password: '' });

  useEffect(() => {
    if (!doctorToken || user?.role !== 'admin') {
      setLoading(false);
      return;
    }

    let cancelled = false;
    setLoading(true);
    maternaguardApi
      .getPatients(doctorToken, { limit: 200, offset: 0 })
      .then((list) => {
        if (!cancelled) {
          setPatients(list);
        }
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, [doctorToken, user]);

  const loadPatientLogs = async (patient) => {
    const key = patient.abha_id || patient.latest_device_id;
    if (logsByKey[key]) {
      setSelectedPatient(patient);
      return;
    }

    try {
      const logs = patient.abha_id
        ? await maternaguardApi.getPatientAssessmentsByAbha(doctorToken, patient.abha_id)
        : await maternaguardApi.getPatientAssessmentsByDevice(doctorToken, patient.latest_device_id, 50);
      setLogsByKey((prev) => ({ ...prev, [key]: logs }));
      setSelectedPatient(patient);
    } catch {
      setLogsByKey((prev) => ({ ...prev, [key]: [] }));
      setSelectedPatient(patient);
    }
  };

  const handleDoctorLogin = async (e) => {
    e.preventDefault();
    try {
      setLoginLoading(true);
      await loginDoctor(loginForm.username, loginForm.password);
    } finally {
      setLoginLoading(false);
    }
  };

  const filteredPatients = patients.filter(p =>
    !search ||
    (p.abha_id || '').toLowerCase().includes(search.toLowerCase()) ||
    (p.latest_device_id || '').toLowerCase().includes(search.toLowerCase())
  );

  const getPatientKey = (patient) => patient.abha_id || patient.latest_device_id;
  const getLogs = (patient) => logsByKey[getPatientKey(patient)] || [];
  const getLatestLog = (patient) => getLogs(patient)[0];

  if (user?.role !== 'admin' || !doctorToken) {
    return (
      <div className="px-4 py-16 max-w-md mx-auto">
        <Card className="border-border shadow-sm">
          <CardContent className="p-5 space-y-4">
            <h2 className="font-playfair text-xl">Doctor Login</h2>
            <p className="text-sm text-muted-foreground">Provider dashboard access requires backend JWT login.</p>
            <form onSubmit={handleDoctorLogin} className="space-y-3">
              <Input
                placeholder="Username"
                value={loginForm.username}
                onChange={(e) => setLoginForm((prev) => ({ ...prev, username: e.target.value }))}
              />
              <Input
                type="password"
                placeholder="Password"
                value={loginForm.password}
                onChange={(e) => setLoginForm((prev) => ({ ...prev, password: e.target.value }))}
              />
              <button
                type="submit"
                disabled={loginLoading}
                className="w-full h-10 rounded-xl bg-primary text-primary-foreground"
              >
                {loginLoading ? 'Signing in...' : 'Sign In'}
              </button>
            </form>
          </CardContent>
        </Card>
      </div>
    );
  }

  if (loading) return (
    <div className="flex items-center justify-center h-screen">
      <div className="w-8 h-8 border-4 border-primary/30 border-t-primary rounded-full animate-spin" />
    </div>
  );

  return (
    <div className="flex flex-col">
      {/* Header */}
      <div className="bg-primary px-5 pt-12 pb-5">
        <h1 className="font-playfair text-2xl font-bold text-primary-foreground">Patients</h1>
        <p className="text-primary-foreground/70 text-sm mt-0.5">Monitor your patients</p>

        {/* Stats row */}
        <div className="flex gap-3 mt-4">
          {[
            { label: 'Total', value: patients.length, icon: Users },
            { label: 'Alerts', value: patients.filter((p) => p.latest_risk === 'high').length, icon: AlertTriangle },
            { label: 'Today', value: patients.filter((p) => new Date(p.latest_date).toDateString() === new Date().toDateString()).length, icon: Activity },
            { label: 'High Risk', value: patients.filter(p => getLatestLog(p)?.risk_level === 'high' || p.latest_risk === 'high').length, icon: Heart },
          ].map(({ label, value, icon: Icon }) => (
            <div key={label} className="flex-1 bg-white/15 rounded-2xl px-3 py-2 text-center">
              <p className="text-white font-bold text-lg leading-none">{value}</p>
              <p className="text-white/70 text-[10px] mt-0.5">{label}</p>
            </div>
          ))}
        </div>
      </div>

      <div className="px-4 py-4 space-y-3">
        {/* Search */}
        <div className="relative">
          <Search size={15} className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground" />
          <Input
            placeholder="Search patients..."
            value={search}
            onChange={e => setSearch(e.target.value)}
            className="pl-9 h-10"
          />
        </div>

        {/* Patient list */}
        {filteredPatients.length === 0 ? (
          <div className="text-center py-16">
            <Users className="w-12 h-12 text-muted-foreground/30 mx-auto mb-3" />
            <p className="text-muted-foreground text-sm">No patients found</p>
          </div>
        ) : (
          filteredPatients.map(patient => {
            const latestLog = getLatestLog(patient.patient_email);
            const alertCount = getAlertCount(patient.patient_email);
            return (
              <Card
                key={getPatientKey(patient)}
                className="border-border shadow-sm active:scale-[0.98] transition-transform cursor-pointer"
                onClick={() => loadPatientLogs(patient)}
              >
                <CardContent className="p-4 flex items-center gap-3">
                  <div className="w-10 h-10 rounded-full bg-accent flex items-center justify-center text-primary font-semibold text-sm shrink-0">
                    {(patient.abha_id || patient.latest_device_id || 'P')[0].toUpperCase()}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <p className="font-medium text-sm text-foreground truncate">{patient.abha_id || `Device ${patient.latest_device_id.slice(0, 8)}`}</p>
                      {patient.high_risk_count > 0 && (
                        <Badge className="bg-red-100 text-red-700 text-[10px] px-1.5 h-4">{patient.high_risk_count}</Badge>
                      )}
                    </div>
                    <p className="text-xs text-muted-foreground truncate">
                      Latest: {new Date(patient.latest_date).toLocaleString()}
                    </p>
                  </div>
                  <div className="flex items-center gap-2 shrink-0">
                    <RiskBadge level={latestLog?.risk_level || patient.latest_risk} />
                    <ChevronRight size={14} className="text-muted-foreground" />
                  </div>
                </CardContent>
              </Card>
            );
          })
        )}
      </div>

      <Dialog open={!!selectedPatient} onOpenChange={() => setSelectedPatient(null)}>
        <DialogContent className="max-w-sm mx-4 max-h-[85vh] overflow-y-auto rounded-2xl">
          <DialogHeader>
            <DialogTitle className="font-playfair text-lg">
              {selectedPatient?.abha_id || `Device ${selectedPatient?.latest_device_id}`}
            </DialogTitle>
          </DialogHeader>
          {selectedPatient && (
            <PatientDetail
              patient={selectedPatient}
              logs={logsByKey[getPatientKey(selectedPatient)] || []}
            />
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}
import { useState, useEffect } from 'react';
import { useOutletContext } from 'react-router-dom';
import { useAuth } from '@/lib/AuthContext';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { toast } from 'sonner';
import { User, Phone, Calendar, Droplets, AlertCircle, LogOut } from 'lucide-react';

const CONDITIONS = ['Gestational Diabetes', 'Pre-eclampsia', 'Hypertension', 'Anemia', 'Thyroid Disorder', 'Other'];
const BLOOD_TYPES = ['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-'];

export default function Profile() {
  const { user } = useOutletContext();
  const { setUser, logout } = useAuth();
  const [form, setForm] = useState({});
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    if (!user) return;
    const stored = localStorage.getItem('mg_profile');
    const profile = stored ? JSON.parse(stored) : null;
    setForm(
      profile
        ? { ...profile }
        : {
            full_name: user.full_name || '',
            abha_id: user.abha_id || '',
            pre_existing_conditions: [],
          }
    );
    setLoading(false);
  }, [user]);

  const set = (k, v) => setForm(f => ({ ...f, [k]: v }));
  const toggleCondition = (c) => {
    const current = form.pre_existing_conditions || [];
    set('pre_existing_conditions', current.includes(c) ? current.filter(x => x !== c) : [...current, c]);
  };

  const handleSave = async () => {
    setSaving(true);
    localStorage.setItem('mg_profile', JSON.stringify(form));
    setUser({
      ...user,
      full_name: form.full_name || user.full_name,
      abha_id: form.abha_id || '',
    });
    toast.success('Profile saved!');
    setSaving(false);
  };

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
      <div className="bg-primary px-5 pt-12 pb-6">
        <div className="flex items-center justify-between">
          <div>
            <div className="w-14 h-14 rounded-full bg-white/20 flex items-center justify-center text-white text-xl font-bold mb-3">
              {user?.full_name?.[0] || user?.email?.[0]?.toUpperCase()}
            </div>
            <h1 className="font-playfair text-xl font-bold text-primary-foreground">{user?.full_name || 'Your Profile'}</h1>
            <p className="text-primary-foreground/70 text-xs mt-0.5">Device ID: {user?.device_id}</p>
          </div>
          <button onClick={logout} className="w-9 h-9 rounded-full bg-white/15 flex items-center justify-center">
            <LogOut size={16} className="text-white" />
          </button>
        </div>
      </div>

      <div className="px-4 py-5 space-y-4">
        {/* Personal Info */}
        <Card className="border-border shadow-sm">
          <CardHeader className="pb-3 pt-4">
            <CardTitle className="text-sm font-semibold flex items-center gap-2">
              <User size={14} className="text-primary" /> Personal Information
            </CardTitle>
          </CardHeader>
          <CardContent className="grid grid-cols-2 gap-3">
            <div className="space-y-1 col-span-2">
              <Label className="text-xs">Full Name</Label>
              <Input className="h-10 text-sm" value={form.full_name || ''} onChange={e => set('full_name', e.target.value)} placeholder="Your name" />
            </div>
            <div className="space-y-1 col-span-2">
              <Label className="text-xs">ABHA ID (optional)</Label>
              <Input className="h-10 text-sm" value={form.abha_id || ''} onChange={e => set('abha_id', e.target.value)} placeholder="14-digit ABHA ID" />
            </div>
            <div className="space-y-1">
              <Label className="text-xs">Phone</Label>
              <Input className="h-10 text-sm" value={form.phone || ''} onChange={e => set('phone', e.target.value)} placeholder="+1 555 0000" />
            </div>
            <div className="space-y-1">
              <Label className="text-xs flex items-center gap-1"><Droplets size={11} className="text-red-500" /> Blood Type</Label>
              <Select value={form.blood_type || ''} onValueChange={v => set('blood_type', v)}>
                <SelectTrigger className="h-10 text-sm"><SelectValue placeholder="Select" /></SelectTrigger>
                <SelectContent>
                  {BLOOD_TYPES.map(bt => <SelectItem key={bt} value={bt}>{bt}</SelectItem>)}
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-1 col-span-2">
              <Label className="text-xs flex items-center gap-1"><Calendar size={11} /> Date of Birth</Label>
              <Input type="date" className="h-10 text-sm" value={form.date_of_birth || ''} onChange={e => set('date_of_birth', e.target.value)} />
            </div>
          </CardContent>
        </Card>

        {/* Pregnancy Info */}
        <Card className="border-border shadow-sm">
          <CardHeader className="pb-3 pt-4">
            <CardTitle className="text-sm font-semibold">Pregnancy Information</CardTitle>
          </CardHeader>
          <CardContent className="grid grid-cols-2 gap-3">
            <div className="space-y-1">
              <Label className="text-xs">Due Date</Label>
              <Input type="date" className="h-10 text-sm" value={form.due_date || ''} onChange={e => set('due_date', e.target.value)} />
            </div>
            <div className="space-y-1">
              <Label className="text-xs">Gest. Week</Label>
              <Input type="number" className="h-10 text-sm" value={form.gestational_week || ''} onChange={e => set('gestational_week', Number(e.target.value))} placeholder="24" />
            </div>
            <div className="space-y-1 col-span-2">
              <Label className="text-xs">Provider Email</Label>
              <Input className="h-10 text-sm" value={form.provider_email || ''} onChange={e => set('provider_email', e.target.value)} placeholder="doctor@clinic.com" />
            </div>
          </CardContent>
        </Card>

        {/* Conditions */}
        <Card className="border-border shadow-sm">
          <CardHeader className="pb-3 pt-4">
            <CardTitle className="text-sm font-semibold flex items-center gap-2">
              <AlertCircle size={14} className="text-primary" /> Pre-existing Conditions
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 gap-2">
              {CONDITIONS.map(c => {
                const selected = (form.pre_existing_conditions || []).includes(c);
                return (
                  <button
                    key={c} type="button" onClick={() => toggleCondition(c)}
                    className={`text-left px-3 py-2 rounded-xl border text-xs transition-all ${
                      selected ? 'border-primary bg-accent text-primary font-medium' : 'border-border hover:border-primary/40'
                    }`}
                  >
                    {c}
                  </button>
                );
              })}
            </div>
          </CardContent>
        </Card>

        {/* Emergency Contact */}
        <Card className="border-border shadow-sm">
          <CardHeader className="pb-3 pt-4">
            <CardTitle className="text-sm font-semibold flex items-center gap-2">
              <Phone size={14} className="text-accent" /> Emergency Contact
            </CardTitle>
          </CardHeader>
          <CardContent className="grid grid-cols-2 gap-3">
            <div className="space-y-1">
              <Label className="text-xs">Name</Label>
              <Input className="h-10 text-sm" value={form.emergency_contact_name || ''} onChange={e => set('emergency_contact_name', e.target.value)} placeholder="Full name" />
            </div>
            <div className="space-y-1">
              <Label className="text-xs">Phone</Label>
              <Input className="h-10 text-sm" value={form.emergency_contact_phone || ''} onChange={e => set('emergency_contact_phone', e.target.value)} placeholder="+1 555 0000" />
            </div>
          </CardContent>
        </Card>

        <Button onClick={handleSave} disabled={saving} className="w-full bg-primary hover:bg-primary/90 h-12 text-base rounded-2xl">
          {saving ? 'Saving...' : 'Save Profile'}
        </Button>
      </div>
    </div>
  );
}
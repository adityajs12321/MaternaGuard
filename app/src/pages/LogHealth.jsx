import { useState } from 'react';
import { useOutletContext, useNavigate } from 'react-router-dom';
import { maternaguardApi } from '@/api/maternaguard';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { enqueueAssessment } from '@/lib/offlineSync';
import { addDemoReferralSms } from '@/lib/smsSimulation';
import { toast } from 'sonner';
import { Activity, Heart, Thermometer, Syringe, ChevronLeft } from 'lucide-react';
import { Link } from 'react-router-dom';

export default function LogHealth() {
  const { user } = useOutletContext();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [form, setForm] = useState({
    age: '',
    sbp: '',
    dbp: '',
    blood_sugar: '',
    body_temp: '',
    heart_rate: '',
    abha_id: user?.abha_id || '',
  });

  const setField = (k, v) => setForm(f => ({ ...f, [k]: v }));

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      setLoading(true);
      const payload = {
        device_id: user.device_id,
        abha_id: form.abha_id || null,
        age: Number(form.age),
        sbp: Number(form.sbp),
        dbp: Number(form.dbp),
        blood_sugar: Number(form.blood_sugar),
        body_temp: Number(form.body_temp),
        heart_rate: Number(form.heart_rate),
        original_timestamp: new Date().toISOString(),
      };
      const result = await maternaguardApi.predict(payload);
      const riskLabel = result.risk_level?.toUpperCase() || 'UNKNOWN';
      toast.success(`Prediction complete: ${riskLabel} risk`);
      if (result.risk_level === 'high') {
        addDemoReferralSms({
          abhaId: payload.abha_id,
          deviceId: payload.device_id,
          timestamp: payload.original_timestamp,
          riskLevel: result.risk_level,
          topFeature: result.top_feature,
        });
        toast.warning('High-risk assessment detected. Referral flow should be initiated.');
        toast.info('Demo referral SMS generated for district hospital workflow.');
      }
      navigate('/');
    } catch (err) {
      const shouldQueueOffline = Boolean(err?.network) || Number(err?.status) >= 500;

      if (shouldQueueOffline) {
        const queuedPayload = {
          device_id: user.device_id,
          abha_id: form.abha_id || null,
          age: Number(form.age),
          sbp: Number(form.sbp),
          dbp: Number(form.dbp),
          blood_sugar: Number(form.blood_sugar),
          body_temp: Number(form.body_temp),
          heart_rate: Number(form.heart_rate),
          original_timestamp: new Date().toISOString(),
        };
        enqueueAssessment(queuedPayload);
        toast.error(err.message || 'Prediction failed');
        toast.info('Assessment saved offline. It will sync when connectivity is available.');
      } else {
        toast.error(err.message || 'Please check your input values and try again.');
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex flex-col">
      {/* Mobile header */}
      <div className="bg-primary px-4 pt-12 pb-5 flex items-center gap-3">
        <Link to="/">
          <div className="w-9 h-9 rounded-full bg-white/15 flex items-center justify-center">
            <ChevronLeft size={20} className="text-white" />
          </div>
        </Link>
        <div>
          <h1 className="font-playfair text-xl font-bold text-primary-foreground">Log Health Entry</h1>
          <p className="text-primary-foreground/70 text-xs mt-0.5">Record your vitals and symptoms</p>
        </div>
      </div>

      <form onSubmit={handleSubmit} className="px-4 py-5 space-y-4">
        {/* Vitals */}
        <Card className="border-border shadow-sm">
          <CardHeader className="pb-3 pt-4">
            <CardTitle className="text-sm font-semibold flex items-center gap-2">
              <Heart size={14} className="text-red-500" /> ML Input Vitals
            </CardTitle>
          </CardHeader>
          <CardContent className="grid grid-cols-2 gap-3">
            {[
              { key: 'age', label: 'Age (years)', placeholder: '28', icon: null },
              { key: 'sbp', label: 'Systolic BP', placeholder: '120', icon: null },
              { key: 'dbp', label: 'Diastolic BP', placeholder: '80', icon: null },
              { key: 'heart_rate', label: 'Heart Rate (bpm)', placeholder: '75', icon: Activity },
              { key: 'body_temp', label: 'Temp (°C)', placeholder: '36.6', icon: Thermometer, step: '0.1' },
              { key: 'blood_sugar', label: 'Blood Sugar (mmol/L)', placeholder: '5.6', icon: Syringe, step: '0.1' },
              { key: 'abha_id', label: 'ABHA ID (optional)', placeholder: '14-digit ABHA', icon: null, type: 'text' },
            ].map(({ key, label, placeholder, icon: Icon, step }) => (
              <div key={key} className="space-y-1">
                <Label className="text-xs">{label}</Label>
                <Input
                  type={key === 'abha_id' ? 'text' : 'number'}
                  step={step}
                  placeholder={placeholder}
                  value={form[key]}
                  onChange={e => setField(key, e.target.value)}
                  className="h-10 text-sm"
                />
              </div>
            ))}
          </CardContent>
        </Card>

        <Button type="submit" disabled={loading} className="w-full bg-primary hover:bg-primary/90 h-12 text-base rounded-2xl">
          {loading ? 'Predicting...' : 'Run Risk Prediction'}
        </Button>
      </form>
    </div>
  );
}
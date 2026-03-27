const SMS_LOG_KEY = 'mg_demo_sms_log';

export function getDemoSmsLog() {
  const raw = localStorage.getItem(SMS_LOG_KEY);
  if (!raw) return [];
  try {
    const parsed = JSON.parse(raw);
    return Array.isArray(parsed) ? parsed : [];
  } catch {
    return [];
  }
}

export function addDemoReferralSms({ abhaId, deviceId, timestamp, riskLevel, topFeature }) {
  const current = getDemoSmsLog();
  const id = `${deviceId}-${Date.now()}`;
  const patientLabel = abhaId || `Device-${String(deviceId || 'unknown').slice(0, 8)}`;

  const body = [
    'MATERNAGUARD ALERT',
    'HIGH RISK PREGNANCY DETECTED',
    `Patient: ${patientLabel}`,
    `Risk level: ${String(riskLevel || 'high').toUpperCase()}`,
    `Assessment time: ${timestamp}`,
    topFeature ? `Top factor: ${topFeature}` : null,
    'Action required: Prepare for referral from local PHC.',
    '(Demo mode: SMS not sent to real hospital)',
  ]
    .filter(Boolean)
    .join('\n');

  const entry = {
    id,
    createdAt: new Date().toISOString(),
    timestamp,
    patientLabel,
    riskLevel: riskLevel || 'high',
    topFeature: topFeature || null,
    target: 'District Hospital (demo)',
    status: 'simulated',
    body,
  };

  const next = [entry, ...current].slice(0, 50);
  localStorage.setItem(SMS_LOG_KEY, JSON.stringify(next));
  return entry;
}

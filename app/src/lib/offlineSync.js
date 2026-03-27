import { maternaguardApi } from '@/api/maternaguard';

const STORAGE_KEY = 'mg_pending_assessments';

export function getPendingAssessments() {
  const raw = localStorage.getItem(STORAGE_KEY);
  if (!raw) return [];
  try {
    return JSON.parse(raw);
  } catch {
    return [];
  }
}

export function enqueueAssessment(assessment) {
  const current = getPendingAssessments();
  const next = [...current, assessment];
  localStorage.setItem(STORAGE_KEY, JSON.stringify(next));
}

export function clearPendingAssessments() {
  localStorage.removeItem(STORAGE_KEY);
}

function isFiniteNumber(value) {
  return typeof value === 'number' && Number.isFinite(value);
}

function inRange(value, min, max) {
  return isFiniteNumber(value) && value >= min && value <= max;
}

function normalizeQueuedAssessment(item) {
  if (!item || typeof item !== 'object') return null;

  const normalized = {
    device_id: typeof item.device_id === 'string' ? item.device_id : '',
    abha_id: item.abha_id ?? null,
    age: Number(item.age),
    sbp: Number(item.sbp),
    dbp: Number(item.dbp),
    blood_sugar: Number(item.blood_sugar),
    body_temp: Number(item.body_temp),
    heart_rate: Number(item.heart_rate),
    original_timestamp: item.original_timestamp,
  };

  const hasRequiredShape =
    normalized.device_id.length > 0 &&
    typeof normalized.original_timestamp === 'string' &&
    inRange(normalized.age, 10, 60) &&
    inRange(normalized.sbp, 70, 220) &&
    inRange(normalized.dbp, 40, 140) &&
    inRange(normalized.blood_sugar, 2, 30) &&
    inRange(normalized.body_temp, 34, 43) &&
    inRange(normalized.heart_rate, 30, 200);

  return hasRequiredShape ? normalized : null;
}

export async function syncPendingAssessments() {
  const pending = getPendingAssessments();
  if (!pending.length) {
    return { synced: 0, pending: 0 };
  }

  const validPending = pending
    .map(normalizeQueuedAssessment)
    .filter(Boolean);

  if (!validPending.length) {
    clearPendingAssessments();
    return { synced: 0, pending: 0, droppedInvalid: pending.length };
  }

  if (validPending.length !== pending.length) {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(validPending));
  }

  let response;
  try {
    response = await maternaguardApi.sync(validPending);
  } catch (err) {
    // If queued payload fails backend validation, drop queue to prevent repeat 422 spam.
    if (Number(err?.status) === 422) {
      clearPendingAssessments();
      return { synced: 0, pending: 0, droppedInvalid: validPending.length, validationError: true };
    }
    throw err;
  }
  if (!response.errors?.length) {
    clearPendingAssessments();
  }

  return {
    synced: response.synced_count,
    pending: getPendingAssessments().length,
    highRisk: response.high_risk_count,
    smsSent: response.sms_sent,
  };
}

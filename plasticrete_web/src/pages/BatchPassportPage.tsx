import React, { useEffect, useState } from 'react';
import {
  batchPhotoUrl,
  fetchBatch,
  updateBatch,
  uploadBatchPhoto,
  type SavedBatch,
} from '../api/client';

export const BatchPassportPage: React.FC<{ batchId: string | null }> = ({ batchId }) => {
  const [batch, setBatch] = useState<SavedBatch | null>(null);
  const [error, setError] = useState('');
  const [castDate, setCastDate] = useState('');
  const [cs7, setCs7] = useState('');
  const [cs28, setCs28] = useState('');
  const [absorption, setAbsorption] = useState('');
  const [notes, setNotes] = useState('');
  const [photoStamp, setPhotoStamp] = useState(0);

  useEffect(() => {
    if (!batchId) return;
    let cancelled = false;
    fetchBatch(batchId)
      .then((loaded) => {
        if (cancelled) return;
        setBatch(loaded);
        setCastDate(loaded.cast_date || '');
        setCs7(loaded.measured_cs_7d == null ? '' : String(loaded.measured_cs_7d));
        setCs28(loaded.measured_cs_28d == null ? '' : String(loaded.measured_cs_28d));
        setAbsorption(loaded.measured_absorption_pct == null ? '' : String(loaded.measured_absorption_pct));
        setNotes(loaded.notes || '');
        setError('');
      })
      .catch((err: unknown) => {
        if (!cancelled) setError(err instanceof Error ? err.message : 'Could not load the batch.');
      });
    return () => {
      cancelled = true;
    };
  }, [batchId]);

  if (!batchId) {
    return <p className="text-sm font-semibold text-slate-800">Save a batch from the studio to open its passport.</p>;
  }
  if (error) {
    return <p className="text-sm font-semibold text-red-800">{error}</p>;
  }
  if (!batch) {
    return <p className="text-sm font-semibold text-slate-700">Loading batch {batchId}…</p>;
  }

  const numberOrUndefined = (value: string) => (value.trim() === '' ? undefined : Number(value));

  return (
    <div className="max-w-4xl mx-auto space-y-6 py-4">
      <div>
        <p className="text-xs font-mono font-bold text-slate-600">{batch.id}</p>
        <h1 className="text-2xl font-extrabold text-slate-950">Batch passport</h1>
        <p className="text-xs font-semibold text-slate-700 mt-1">{batch.model_version}</p>
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <div className="p-3 rounded-xl bg-white border border-slate-300">
          <span className="text-[11px] font-bold text-slate-700 block">Predicted mean</span>
          <span className="font-mono font-extrabold text-slate-950">{batch.predicted_cs_mean} MPa</span>
        </div>
        <div className="p-3 rounded-xl bg-white border border-slate-300">
          <span className="text-[11px] font-bold text-slate-700 block">90% interval</span>
          <span className="font-mono font-extrabold text-slate-950">{batch.predicted_cs_low} – {batch.predicted_cs_high}</span>
        </div>
        <div className="p-3 rounded-xl bg-white border border-slate-300">
          <span className="text-[11px] font-bold text-slate-700 block">Measured 28-day</span>
          <span className="font-mono font-extrabold text-slate-950">{batch.measured_cs_28d ?? '—'}</span>
        </div>
        <div className="p-3 rounded-xl bg-white border border-slate-300">
          <span className="text-[11px] font-bold text-slate-700 block">Error (measured − mean)</span>
          <span className="font-mono font-extrabold text-slate-950">{batch.error_mpa ?? '—'}</span>
        </div>
      </div>

      <p className="text-sm font-semibold text-slate-800">{batch.calibration.message}</p>

      <form
        className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs font-semibold text-slate-900"
        onSubmit={async (event) => {
          event.preventDefault();
          try {
            const saved = await updateBatch(batch.id, {
              cast_date: castDate || undefined,
              measured_cs_7d: numberOrUndefined(cs7),
              measured_cs_28d: numberOrUndefined(cs28),
              measured_absorption_pct: numberOrUndefined(absorption),
              notes,
            });
            setBatch(saved);
            setError('');
          } catch (err) {
            setError(err instanceof Error ? err.message : 'Could not save the lab result.');
          }
        }}
      >
        <label>Cast date
          <input type="date" value={castDate} onChange={(e) => setCastDate(e.target.value)} className="mt-1 w-full rounded-lg border border-slate-300 px-2 py-1.5" />
        </label>
        <label>7-day strength (MPa)
          <input type="number" step="0.1" value={cs7} onChange={(e) => setCs7(e.target.value)} className="mt-1 w-full rounded-lg border border-slate-300 px-2 py-1.5 font-mono" />
        </label>
        <label>28-day strength (MPa)
          <input type="number" step="0.1" value={cs28} onChange={(e) => setCs28(e.target.value)} className="mt-1 w-full rounded-lg border border-slate-300 px-2 py-1.5 font-mono" />
        </label>
        <label>Absorption (%)
          <input type="number" step="0.1" value={absorption} onChange={(e) => setAbsorption(e.target.value)} className="mt-1 w-full rounded-lg border border-slate-300 px-2 py-1.5 font-mono" />
        </label>
        <label className="sm:col-span-2">Notes
          <textarea value={notes} onChange={(e) => setNotes(e.target.value)} className="mt-1 w-full rounded-lg border border-slate-300 px-2 py-1.5" rows={3} />
        </label>
        <button type="submit" className="sm:col-span-2 rounded-xl bg-slate-900 text-white font-bold py-2.5 cursor-pointer">
          Save lab result
        </button>
      </form>

      <div className="flex flex-wrap items-center gap-4">
        <label className="text-xs font-bold text-slate-900">
          Cube photo
          <input
            type="file"
            accept="image/jpeg,image/png,image/webp"
            className="mt-1 block text-xs"
            onChange={async (event) => {
              const file = event.target.files?.[0];
              if (!file) return;
              try {
                await uploadBatchPhoto(batch.id, file);
                setPhotoStamp(Date.now());
              } catch (err) {
                setError(err instanceof Error ? err.message : 'Photo upload failed.');
              }
            }}
          />
        </label>
        <img
          src={`${batchPhotoUrl(batch.id)}?t=${photoStamp}`}
          alt="Cube"
          className="h-28 w-28 object-cover rounded-xl border border-slate-300 bg-slate-100"
          onError={(event) => { (event.target as HTMLImageElement).style.display = 'none'; }}
        />
        <a
          href={`/api/batches/${encodeURIComponent(batch.id)}/passport.pdf`}
          className="text-xs font-bold text-emerald-800 underline"
        >
          Download passport PDF
        </a>
      </div>
      <p className="text-[11px] font-mono text-slate-600">QR target: {batch.qr_url}</p>
    </div>
  );
};

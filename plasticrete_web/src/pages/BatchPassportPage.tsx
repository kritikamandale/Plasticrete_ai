import React, { useEffect, useRef, useState } from 'react';
import {
  batchPhotoUrl,
  deleteBatchPhoto,
  fetchBatch,
  listBatches,
  updateBatch,
  uploadBatchPhoto,
  type BatchSummary,
  type SavedBatch,
} from '../api/client';
import { useMix } from '../context/MixContext';
import {
  AlertTriangle,
  FlaskConical,
  Camera,
  Trash2,
  ArrowLeft,
  Scale,
} from 'lucide-react';

function formatMpa(value: number | null | undefined): string {
  if (value == null || !Number.isFinite(Number(value))) return '—';
  return Number(value).toFixed(1);
}

function formatMixLine(batch: SavedBatch): string {
  const mix = batch.mix_params;
  const parts = [
    mix.plastic_type,
    mix.replacement_pct != null ? `${mix.replacement_pct}% plastic` : null,
    mix.particle_size_mm != null ? `${mix.particle_size_mm} mm` : null,
    mix.wc_ratio != null ? `w/c ${mix.wc_ratio}` : null,
    mix.additive_type ? String(mix.additive_type).replaceAll('_', ' ') : null,
    mix.additive_pct != null ? `${mix.additive_pct}% additive` : null,
  ];
  return parts.filter(Boolean).join(' · ');
}

function intervalStatus(batch: SavedBatch): string | null {
  if (batch.measured_cs_28d == null || batch.predicted_cs_low == null || batch.predicted_cs_high == null) {
    return null;
  }
  const measured = Number(batch.measured_cs_28d);
  if (measured >= Number(batch.predicted_cs_low) && measured <= Number(batch.predicted_cs_high)) {
    return 'The laboratory result sits inside the model’s 90% range.';
  }
  return 'The laboratory result is outside the model’s 90% range.';
}

const BatchPhotoThumb: React.FC<{ id: string; hasPhoto?: boolean }> = ({ id, hasPhoto }) => {
  const [show, setShow] = useState(hasPhoto !== false);
  if (!show) {
    return (
      <div className="w-20 h-20 shrink-0 rounded-lg bg-[#F5F5F3] border border-dashed border-[#E5E5E0] flex items-center justify-center">
        <Camera className="w-5 h-5 text-[#525866]" />
      </div>
    );
  }
  return (
    <img
      src={batchPhotoUrl(id)}
      alt=""
      onError={() => setShow(false)}
      className="w-20 h-20 shrink-0 rounded-lg object-cover border border-[#E5E5E0] bg-[#F5F5F3]"
    />
  );
};

export const BatchPassportPage: React.FC<{ batchId: string | null }> = ({ batchId }) => {
  const [batch, setBatch] = useState<SavedBatch | null>(null);
  const [loadError, setLoadError] = useState('');
  const [saveError, setSaveError] = useState('');
  const [castDate, setCastDate] = useState('');
  const [cs7, setCs7] = useState('');
  const [cs28, setCs28] = useState('');
  const [absorption, setAbsorption] = useState('');
  const [notes, setNotes] = useState('');
  const [cubeSize, setCubeSize] = useState('150');
  const [photoStamp, setPhotoStamp] = useState(0);
  const [hasPhoto, setHasPhoto] = useState(false);
  const [photoBusy, setPhotoBusy] = useState(false);
  const [savedSuccess, setSavedSuccess] = useState(false);
  const [records, setRecords] = useState<BatchSummary[]>([]);
  const [listError, setListError] = useState('');
  const [listLoading, setListLoading] = useState(false);
  const photoInputRef = useRef<HTMLInputElement>(null);
  const { openBatch, openBatchList, setMainRoute, startNewMix } = useMix();

  useEffect(() => {
    if (batchId) return;
    let cancelled = false;
    setListLoading(true);
    listBatches()
      .then((rows) => {
        if (cancelled) return;
        setRecords(Array.isArray(rows) ? rows : []);
        setListError('');
      })
      .catch((err: unknown) => {
        if (!cancelled) setListError(err instanceof Error ? err.message : 'Could not load batch records.');
      })
      .finally(() => {
        if (!cancelled) setListLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [batchId]);

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
        setCubeSize(loaded.cube_size_mm != null ? String(Math.round(Number(loaded.cube_size_mm))) : '150');
        setHasPhoto(Boolean(loaded.cube_photo_path));
        setLoadError('');
      })
      .catch((err: unknown) => {
        if (!cancelled) setLoadError(err instanceof Error ? err.message : 'Could not load the batch.');
      });
    return () => {
      cancelled = true;
    };
  }, [batchId]);

  if (!batchId) {
    return (
      <div className="space-y-6 py-4">
        <div className="flex flex-col sm:flex-row sm:items-end justify-between gap-4 pb-4 border-b border-[#E5E5E0]">
          <div>
            <h1 className="text-2xl font-heading font-bold text-[#1E2022] tracking-tight">
              Cast & Record
            </h1>
            <p className="text-sm text-[#525866] mt-1 max-w-2xl">
              Saved mix passports stay here. Open one later to add the cube photo and 7-day or 28-day lab numbers, then compare them with the original prediction.
            </p>
          </div>
          <button
            type="button"
            onClick={startNewMix}
            className="inline-flex px-4 py-2.5 bg-[#2563EB] hover:bg-[#1D4ED8] text-white text-xs font-heading font-bold uppercase tracking-wider rounded-[4px]"
          >
            Start a new mix
          </button>
        </div>
        {listError && (
          <div className="p-4 rounded-lg bg-[#FFF7ED] border border-[#F97316]/40 text-sm text-[#1E2022]">
            {listError}
          </div>
        )}
        {listLoading ? (
          <div className="p-10 text-center bg-[#FFFFFF] border border-[#E5E5E0] rounded-xl text-sm text-[#525866]">
            Loading saved batch passports…
          </div>
        ) : records.length === 0 ? (
          <div className="p-10 text-center bg-[#FFFFFF] border border-[#E5E5E0] rounded-xl">
            <FlaskConical className="w-8 h-8 text-[#525866] mx-auto mb-3" />
            <h2 className="font-heading font-bold text-[#1E2022]">No batch has been saved yet</h2>
            <p className="text-sm text-[#525866] mt-2 max-w-md mx-auto">
              Generate a prediction in the mix workspace, then use Cast & Record. The new passport opens here and remains after you close the site.
            </p>
            <button
              type="button"
              onClick={() => setMainRoute('studio')}
              className="mt-5 inline-flex px-4 py-2.5 bg-[#2563EB] hover:bg-[#1D4ED8] text-white text-xs font-medium rounded-[4px]"
            >
              Open mix workspace
            </button>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {records.map((record) => {
              const compared = record.measured_cs_28d != null;
              return (
                <button
                  key={record.id}
                  type="button"
                  onClick={() => openBatch(record.id)}
                  className="text-left p-4 rounded-xl bg-[#FFFFFF] border border-[#E5E5E0] hover:border-[#2563EB] focus:outline-none focus-visible:ring-2 focus-visible:ring-[#2563EB] flex gap-4"
                >
                  <BatchPhotoThumb id={record.id} hasPhoto={record.has_photo} />
                  <div className="min-w-0 flex-1">
                    <span className="font-mono text-xs font-bold text-[#2563EB]">{record.id}</span>
                    <div className="mt-2 grid grid-cols-2 gap-2">
                      <div>
                        <span className="block text-[10px] font-semibold uppercase tracking-wide text-[#525866]">Predicted</span>
                        <span className="font-mono text-xl font-bold tabular-nums text-[#1E2022]">
                          {formatMpa(record.predicted_cs_mean)}
                          <span className="ml-1 text-xs font-semibold text-[#525866]">MPa</span>
                        </span>
                      </div>
                      <div>
                        <span className="block text-[10px] font-semibold uppercase tracking-wide text-[#525866]">Lab 28-day</span>
                        <span className="font-mono text-xl font-bold tabular-nums text-[#1E2022]">
                          {compared ? formatMpa(record.measured_cs_28d) : '—'}
                          <span className="ml-1 text-xs font-semibold text-[#525866]">MPa</span>
                        </span>
                      </div>
                    </div>
                    <span className="mt-2 block text-sm text-[#525866]">
                      {record.plastic_type || 'Mix'}
                      {record.replacement_pct != null ? ` · ${record.replacement_pct}% replacement` : ''}
                      {record.cast_date ? ` · cast ${record.cast_date}` : ''}
                    </span>
                    <span className="mt-1 block text-xs font-semibold text-[#2563EB]">
                      {compared
                        ? `Compared · difference ${formatMpa(record.error_mpa)} MPa`
                        : '28-day test pending · open to add results or a cube photo'}
                    </span>
                  </div>
                </button>
              );
            })}
          </div>
        )}
      </div>
    );
  }

  if (loadError) {
    return (
      <div className="p-4 rounded-lg bg-[#FFF7ED] border border-[#F97316]/40 text-xs text-[#1E2022] max-w-xl mx-auto my-12 flex items-center gap-2">
        <AlertTriangle className="w-4 h-4 text-[#F97316] shrink-0" />
        <span>{loadError}</span>
      </div>
    );
  }

  if (!batch) {
    return (
      <div className="p-8 text-center text-xs font-mono text-[#525866]">
        Loading traceable batch passport {batchId}…
      </div>
    );
  }

  const numberOrUndefined = (value: string) => (value.trim() === '' ? undefined : Number(value));

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaveError('');
    setSavedSuccess(false);
    try {
      const updated = await updateBatch(batchId, {
        cast_date: castDate || undefined,
        measured_cs_7d: numberOrUndefined(cs7),
        measured_cs_28d: numberOrUndefined(cs28),
        measured_absorption_pct: numberOrUndefined(absorption),
        notes: notes || undefined,
        cube_size_mm: Number(cubeSize),
      });
      setBatch(updated);
      setSavedSuccess(true);
      setTimeout(() => setSavedSuccess(false), 3000);
    } catch (err) {
      setSaveError(err instanceof Error ? err.message : 'Failed to save batch data.');
    }
  };

  const handlePhotoUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file || !batchId) return;
    setSaveError('');
    setPhotoBusy(true);
    try {
      await uploadBatchPhoto(batchId, file);
      setHasPhoto(true);
      setPhotoStamp(Date.now());
    } catch (err) {
      setSaveError(err instanceof Error ? err.message : 'Photo upload failed.');
    } finally {
      setPhotoBusy(false);
    }
  };

  const handlePhotoDelete = async () => {
    if (!batchId || !hasPhoto) return;
    setSaveError('');
    setPhotoBusy(true);
    try {
      await deleteBatchPhoto(batchId);
      setHasPhoto(false);
      setPhotoStamp(Date.now());
      if (photoInputRef.current) photoInputRef.current.value = '';
    } catch (err) {
      setSaveError(err instanceof Error ? err.message : 'Could not remove the photo.');
    } finally {
      setPhotoBusy(false);
    }
  };

  const compared = batch.measured_cs_28d != null && batch.predicted_cs_mean != null;
  const rangeNote = intervalStatus(batch);
  const errorMpa = batch.error_mpa != null
    ? batch.error_mpa
    : compared
      ? Number(batch.measured_cs_28d) - Number(batch.predicted_cs_mean)
      : null;

  return (
    <div className="space-y-6 py-4">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-[#E5E5E0]">
        <div>
          <button
            type="button"
            onClick={openBatchList}
            className="inline-flex items-center gap-1 text-xs font-semibold text-[#2563EB] mb-2"
          >
            <ArrowLeft className="w-3.5 h-3.5" />
            All saved batches
          </button>
          <div className="flex items-center gap-2">
            <span className="font-mono text-xs font-bold text-[#2563EB] bg-[#2563EB]/10 px-2 py-0.5 rounded border border-[#2563EB]/20">
              {batch.id}
            </span>
            <span className="eyebrow-tag text-[9px] text-[#525866]">SAVED PASSPORT</span>
          </div>
          <h1 className="text-2xl font-heading font-bold text-[#1E2022] tracking-tight mt-1">
            Physical Cube Verification Passport
          </h1>
          <p className="text-sm text-[#525866] mt-1 max-w-2xl">
            {formatMixLine(batch)}
            {batch.cast_date ? ` · cast ${batch.cast_date}` : ''}
          </p>
        </div>
        <button
          type="button"
          onClick={startNewMix}
          className="inline-flex px-4 py-2.5 border border-[#E5E5E0] bg-[#FFFFFF] hover:bg-[#F5F5F3] text-[#1E2022] text-xs font-heading font-bold uppercase tracking-wider rounded-[4px]"
        >
          Start a new mix
        </button>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-4">
        <div className="min-h-36 p-5 rounded-xl bg-[#FFFFFF] border border-[#E5E5E0] flex flex-col justify-between">
          <span className="text-[11px] font-semibold uppercase tracking-wide text-[#525866]">Predicted compressive strength</span>
          <span className="mt-4 font-mono text-4xl font-bold tabular-nums text-[#1E2022] leading-none">
            {formatMpa(batch.predicted_cs_mean)}
          </span>
          <span className="mt-2 text-sm font-semibold text-[#525866]">MPa · model prediction</span>
        </div>
        <div className="min-h-36 p-5 rounded-xl bg-[#FFFFFF] border border-[#E5E5E0] flex flex-col justify-between">
          <span className="text-[11px] font-semibold uppercase tracking-wide text-[#525866]">90% prediction interval</span>
          <div className="mt-4 space-y-2">
            <div className="flex items-baseline justify-between gap-3">
              <span className="text-sm text-[#525866]">Low</span>
              <span className="font-mono text-2xl font-bold tabular-nums text-[#2563EB] whitespace-nowrap">
                {formatMpa(batch.predicted_cs_low)} <span className="text-sm font-semibold">MPa</span>
              </span>
            </div>
            <div className="flex items-baseline justify-between gap-3">
              <span className="text-sm text-[#525866]">High</span>
              <span className="font-mono text-2xl font-bold tabular-nums text-[#2563EB] whitespace-nowrap">
                {formatMpa(batch.predicted_cs_high)} <span className="text-sm font-semibold">MPa</span>
              </span>
            </div>
          </div>
        </div>
        <div className="min-h-36 p-5 rounded-xl bg-[#FFFFFF] border border-[#E5E5E0] flex flex-col justify-between">
          <span className="text-[11px] font-semibold uppercase tracking-wide text-[#525866]">Measured 28-day strength</span>
          <span className="mt-4 font-mono text-4xl font-bold tabular-nums text-[#1E2022] leading-none">
            {batch.measured_cs_28d != null ? formatMpa(batch.measured_cs_28d) : '—'}
          </span>
          <span className="mt-2 text-sm font-semibold text-[#525866]">
            {batch.measured_cs_28d != null ? 'MPa · laboratory result' : 'MPa · test pending'}
          </span>
        </div>
        <div className="min-h-36 p-5 rounded-xl bg-[#FFFFFF] border border-[#E5E5E0] flex flex-col justify-between">
          <span className="text-[11px] font-semibold uppercase tracking-wide text-[#525866]">IS 516 cube status</span>
          <span className="mt-4 text-2xl font-heading font-bold text-[#1E2022]">
            {batch.measured_cs_28d != null ? 'Result recorded' : 'Awaiting test'}
          </span>
          <span className="mt-2 text-sm text-[#525866]">A recorded result is not a certificate.</span>
        </div>
      </div>

      {compared ? (
        <div className="p-5 rounded-xl bg-[#FFFFFF] border border-[#2563EB]/30">
          <div className="flex items-center gap-2 mb-3">
            <Scale className="w-4 h-4 text-[#2563EB]" />
            <h2 className="font-heading font-bold text-sm text-[#1E2022]">Forecast versus laboratory</h2>
          </div>
          <p className="text-sm text-[#1E2022] max-w-3xl">
            The model guessed <strong className="font-mono">{formatMpa(batch.predicted_cs_mean)} MPa</strong>.
            The cube test at 28 days measured <strong className="font-mono">{formatMpa(batch.measured_cs_28d)} MPa</strong>
            {errorMpa != null ? (
              <>
                {' '}
                ({errorMpa >= 0 ? 'the lab cube was stronger by' : 'the lab cube was weaker by'}{' '}
                <strong className="font-mono">{formatMpa(Math.abs(errorMpa))} MPa</strong>).
              </>
            ) : (
              '.'
            )}
          </p>
          {batch.measured_cs_7d != null && (
            <p className="text-sm text-[#525866] mt-2">
              7-day laboratory strength: <span className="font-mono font-semibold text-[#1E2022]">{formatMpa(batch.measured_cs_7d)} MPa</span>
              {batch.measured_absorption_pct != null ? ` · absorption ${formatMpa(batch.measured_absorption_pct)}%` : ''}
            </p>
          )}
          {rangeNote && (
            <p className="text-sm font-semibold text-[#2563EB] mt-2">{rangeNote}</p>
          )}
          {batch.notes ? (
            <p className="text-sm text-[#525866] mt-3 border-t border-[#E5E5E0] pt-3">
              <span className="font-semibold text-[#1E2022]">Saved notes. </span>
              {batch.notes}
            </p>
          ) : null}
        </div>
      ) : (
        <div className="p-4 rounded-xl bg-[#F5F5F3] border border-[#E5E5E0] text-sm text-[#525866]">
          This passport is stored. After the cube is crushed, type the 7-day and 28-day readings below. This page will then show the model guess next to the laboratory number.
        </div>
      )}

      {saveError && (
        <div className="p-3 rounded-lg bg-[#FFF7ED] border border-[#F97316]/40 text-xs text-[#1E2022]">
          {saveError}
        </div>
      )}

      {savedSuccess && (
        <div className="p-3 rounded-lg bg-[#F5F5F3] border border-[#2563EB]/40 text-xs font-mono text-[#2563EB]">
          Saved. Open this passport later from Cast & Record — the numbers and photo stay on this page.
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-12 gap-6">
        <form onSubmit={handleSave} className="md:col-span-7 engineering-card rounded-xl p-5 border border-[#E5E5E0] bg-[#FFFFFF] shadow-xs space-y-4">
          <div className="pb-3 border-b border-[#E5E5E0]">
            <h3 className="font-heading font-bold text-sm text-[#1E2022]">
              Laboratory Test Measurements (IS 516)
            </h3>
            <p className="text-xs text-[#525866]">Enter compression machine readings. Saving writes them onto this passport for later comparison.</p>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div className="space-y-1">
              <label className="text-xs font-semibold text-[#525866]">Casting Date</label>
              <input
                type="date"
                value={castDate}
                onChange={(e) => setCastDate(e.target.value)}
                className="w-full text-sm font-mono rounded-lg border border-[#E5E5E0] bg-[#F5F5F3] px-3 py-2.5 focus:outline-none focus:ring-2 focus:ring-[#2563EB]"
              />
            </div>

            <div className="space-y-1">
              <label className="text-xs font-semibold text-[#525866]">Cube dimension</label>
              <select
                value={cubeSize}
                onChange={(e) => setCubeSize(e.target.value)}
                className="w-full text-sm font-semibold rounded-lg border border-[#E5E5E0] bg-[#F5F5F3] px-3 py-2.5 focus:outline-none focus:ring-2 focus:ring-[#2563EB]"
              >
                <option value="150">150 mm cube</option>
                <option value="100">100 mm cube</option>
              </select>
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 pt-2">
            <div className="space-y-1">
              <label className="text-xs font-semibold text-[#525866]">7-Day CS (MPa)</label>
              <input
                type="number"
                step="0.1"
                placeholder="e.g. 18.5"
                value={cs7}
                onChange={(e) => setCs7(e.target.value)}
                className="w-full text-sm font-mono font-bold rounded-lg border border-[#E5E5E0] bg-[#FFFFFF] px-3 py-2.5 focus:outline-none focus:ring-2 focus:ring-[#2563EB]"
              />
            </div>

            <div className="space-y-1">
              <label className="text-xs font-semibold text-[#525866]">28-Day CS (MPa)</label>
              <input
                type="number"
                step="0.1"
                placeholder="e.g. 26.2"
                value={cs28}
                onChange={(e) => setCs28(e.target.value)}
                className="w-full text-sm font-mono font-bold rounded-lg border border-[#E5E5E0] bg-[#FFFFFF] px-3 py-2.5 focus:outline-none focus:ring-2 focus:ring-[#2563EB]"
              />
            </div>

            <div className="space-y-1">
              <label className="text-xs font-semibold text-[#525866]">Absorption (%)</label>
              <input
                type="number"
                step="0.1"
                placeholder="e.g. 4.2"
                value={absorption}
                onChange={(e) => setAbsorption(e.target.value)}
                className="w-full text-sm font-mono font-bold rounded-lg border border-[#E5E5E0] bg-[#FFFFFF] px-3 py-2.5 focus:outline-none focus:ring-2 focus:ring-[#2563EB]"
              />
            </div>
          </div>

          <div className="space-y-1 pt-2">
            <label className="text-xs font-semibold text-[#525866]">Technician Notes & Observations</label>
            <textarea
              rows={3}
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              placeholder="Record slump behaviour, compaction method, surface voids, or failure mode..."
              className="w-full text-xs font-mono rounded-lg border border-[#E5E5E0] bg-[#F5F5F3] p-2.5 focus:ring-2 focus:ring-[#2563EB]"
            />
          </div>

          <button
            type="submit"
            className="w-full py-2.5 px-4 rounded-lg bg-[#2563EB] hover:bg-[#1D4ED8] text-white text-xs font-heading font-bold uppercase tracking-wider transition-all shadow-xs cursor-pointer"
          >
            Save numbers for later comparison
          </button>
        </form>

        <div className="md:col-span-5 space-y-4">
          <div className="engineering-card rounded-xl p-5 border border-[#E5E5E0] bg-[#FFFFFF] shadow-xs space-y-4">
            <div className="flex items-center justify-between pb-3 border-b border-[#E5E5E0]">
              <span className="eyebrow-tag text-[10px] text-[#525866]">SAVED CUBE PHOTO</span>
              <Camera className="w-4 h-4 text-[#525866]" />
            </div>

            <div className="aspect-video w-full rounded-lg bg-[#F5F5F3] border border-dashed border-[#E5E5E0] flex flex-col items-center justify-center p-4 text-center overflow-hidden relative">
              {hasPhoto && batchId ? (
                <img
                  src={`${batchPhotoUrl(batchId)}?t=${photoStamp}`}
                  alt="Saved cube specimen"
                  onError={() => setHasPhoto(false)}
                  className="absolute inset-0 w-full h-full object-cover rounded"
                />
              ) : (
                <div className="text-xs text-[#525866]">
                  <Camera className="w-6 h-6 mx-auto mb-1 text-[#525866]" />
                  <span className="font-semibold block">Attach a photo of the cube</span>
                  <span className="text-[10px]">Grey concrete cube or cube in the testing machine. JPEG or PNG, under 5 MB. It stays on this passport.</span>
                </div>
              )}
            </div>

            <input
              ref={photoInputRef}
              type="file"
              accept="image/jpeg,image/png,image/webp"
              onChange={handlePhotoUpload}
              disabled={photoBusy}
              className="w-full text-xs text-[#525866] file:mr-3 file:py-1.5 file:px-3 file:rounded-md file:border file:border-[#E5E5E0] file:bg-[#F5F5F3] file:text-xs file:font-semibold file:text-[#1E2022] hover:file:bg-[#FFFFFF] cursor-pointer disabled:opacity-60"
            />
            {hasPhoto ? (
              <button
                type="button"
                onClick={handlePhotoDelete}
                disabled={photoBusy}
                className="w-full inline-flex items-center justify-center gap-2 py-2 px-4 rounded-lg border border-[#E5E5E0] bg-[#FFFFFF] hover:bg-[#FFF7ED] text-[#1E2022] text-xs font-heading font-bold uppercase tracking-wider disabled:opacity-60"
              >
                <Trash2 className="w-3.5 h-3.5" />
                {photoBusy ? 'Removing…' : 'Remove photo'}
              </button>
            ) : null}
          </div>
        </div>
      </div>
    </div>
  );
};

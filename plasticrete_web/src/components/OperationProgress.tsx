import React, { useState, useEffect } from 'react';
import {
  Loader2,
  Clock,
  AlertTriangle,
  XCircle,
  CheckCircle2,
  RefreshCw,
  X,
  ChevronDown,
  ChevronUp,
} from 'lucide-react';

export type OperationStatus =
  | 'idle'
  | 'submitting'
  | 'queued'
  | 'running'
  | 'progress'
  | 'delayed'
  | 'success'
  | 'error'
  | 'timeout'
  | 'cancelled';

export interface OperationProgressProps {
  title: string;
  description?: string;
  status: OperationStatus;
  startTime?: number | null; // Date.now() timestamp when started
  expectedDurationMs?: number; // Approximate historical execution range (e.g., 2000ms for M1, 8000ms for M2)
  actualProgressPct?: number | null; // Real percentage if provided by backend (0-100)
  errorMessage?: string | null;
  technicalDetails?: string | null;
  onRetry?: () => void;
  onCancel?: () => void;
  cancelLabel?: string;
  variant?: 'panel' | 'card' | 'inline';
  className?: string;
}

export const OperationProgress: React.FC<OperationProgressProps> = ({
  title,
  description,
  status,
  startTime,
  expectedDurationMs,
  actualProgressPct,
  errorMessage,
  technicalDetails,
  onRetry,
  onCancel,
  cancelLabel = 'Cancel',
  variant = 'panel',
  className = '',
}) => {
  const [elapsedMs, setElapsedMs] = useState<number>(0);
  const [showTechDetails, setShowTechDetails] = useState(false);

  useEffect(() => {
    if (!startTime || (status !== 'submitting' && status !== 'running' && status !== 'delayed' && status !== 'progress' && status !== 'queued')) {
      if (status === 'idle') setElapsedMs(0);
      return;
    }

    const interval = setInterval(() => {
      setElapsedMs(Math.max(0, Date.now() - startTime));
    }, 100);

    return () => clearInterval(interval);
  }, [startTime, status]);

  // Format elapsed time as mm:ss.s
  const formatTime = (ms: number): string => {
    const totalSec = Math.floor(ms / 1000);
    const mins = Math.floor(totalSec / 60);
    const secs = totalSec % 60;
    return `${String(mins).padStart(2, '0')}:${String(secs).padStart(2, '0')}`;
  };

  const isIndeterminate = actualProgressPct == null || actualProgressPct === undefined;
  const isDelayed = status === 'delayed' || (expectedDurationMs && elapsedMs > expectedDurationMs && (status === 'running' || status === 'submitting'));

  if (status === 'idle') {
    return null;
  }

  // Inline Variant
  if (variant === 'inline') {
    return (
      <div className={`inline-flex items-center gap-2 text-xs font-mono px-2.5 py-1 rounded bg-[#F5F5F3] border border-[#E5E5E0] ${className}`}>
        {status === 'running' || status === 'submitting' ? (
          <Loader2 className="w-3.5 h-3.5 text-[#2563EB] animate-spin shrink-0" />
        ) : status === 'delayed' ? (
          <AlertTriangle className="w-3.5 h-3.5 text-[#F97316] shrink-0" />
        ) : status === 'error' || status === 'timeout' ? (
          <XCircle className="w-3.5 h-3.5 text-[#F97316] shrink-0" />
        ) : (
          <CheckCircle2 className="w-3.5 h-3.5 text-[#2563EB] shrink-0" />
        )}
        <span className="font-semibold text-[#1E2022] truncate">{title}</span>
        {startTime && (
          <span className="text-[#525866]">[{formatTime(elapsedMs)}]</span>
        )}
        {onRetry && (status === 'error' || status === 'timeout' || status === 'delayed') && (
          <button onClick={onRetry} className="ml-1 text-[#2563EB] hover:underline flex items-center gap-1 font-sans font-bold">
            <RefreshCw className="w-3 h-3" /> Retry
          </button>
        )}
      </div>
    );
  }

  // Card & Panel Variants
  return (
    <div
      role="status"
      aria-live="polite"
      className={`engineering-card rounded-xl p-5 border border-[#E5E5E0] bg-[#FFFFFF] shadow-xs space-y-4 ${className}`}
    >
      {/* Header with Title and Elapsed / Status Timer */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-3 border-b border-[#E5E5E0]">
        <div className="flex items-center gap-2.5">
          <div
            className={`p-1.5 rounded-md shrink-0 border ${
              status === 'error' || status === 'timeout'
                ? 'bg-[#FFF7ED] text-[#F97316] border-[#F97316]/30'
                : isDelayed
                ? 'bg-[#FFF7ED] text-[#F97316] border-[#F97316]/30'
                : status === 'success'
                ? 'bg-[#F5F5F3] text-[#2563EB] border-[#2563EB]/20'
                : 'bg-[#F5F5F3] text-[#2563EB] border-[#E5E5E0]'
            }`}
          >
            {status === 'running' || status === 'submitting' || status === 'progress' ? (
              <Loader2 className="w-4 h-4 animate-spin text-[#2563EB]" />
            ) : status === 'delayed' || isDelayed ? (
              <AlertTriangle className="w-4 h-4 text-[#F97316]" />
            ) : status === 'error' || status === 'timeout' ? (
              <XCircle className="w-4 h-4 text-[#F97316]" />
            ) : status === 'cancelled' ? (
              <X className="w-4 h-4 text-[#525866]" />
            ) : (
              <CheckCircle2 className="w-4 h-4 text-[#2563EB]" />
            )}
          </div>

          <div>
            <div className="flex items-center gap-2">
              <h4 className="font-heading font-bold text-sm text-[#1E2022] tracking-tight">
                {title}
              </h4>
              <span
                className={`eyebrow-tag text-[9px] px-2 py-0.5 rounded border uppercase ${
                  status === 'error' || status === 'timeout'
                    ? 'bg-[#FFF7ED] text-[#F97316] border-[#F97316]/30'
                    : isDelayed
                    ? 'bg-[#FFF7ED] text-[#F97316] border-[#F97316]/30'
                    : status === 'success'
                    ? 'bg-[#2563EB]/10 text-[#2563EB] border-[#2563EB]/20'
                    : 'bg-[#F5F5F3] text-[#333A42] border-[#E5E5E0]'
                }`}
              >
                {status === 'running' || status === 'submitting'
                  ? isDelayed
                    ? 'Taking longer than usual'
                    : 'Preparing'
                  : status === 'success'
                  ? 'Ready'
                  : status === 'error'
                  ? 'Could not complete'
                  : status === 'timeout'
                  ? 'Timed out'
                  : status === 'cancelled'
                  ? 'Stopped'
                  : status === 'delayed'
                  ? 'Taking longer than usual'
                  : status === 'queued'
                  ? 'Waiting'
                  : status}
              </span>
            </div>
            {description && (
              <p className="text-xs text-[#525866] mt-0.5 leading-relaxed">{description}</p>
            )}
          </div>
        </div>

        {/* Elapsed Timer Counter */}
        <div className="flex items-center gap-3 shrink-0 text-xs font-mono">
          <div className="flex items-center gap-1.5 px-2.5 py-1 rounded bg-[#F5F5F3] border border-[#E5E5E0] text-[#333A42]">
            <Clock className="w-3.5 h-3.5 text-[#525866]" />
            <span className="font-semibold">Elapsed: {formatTime(elapsedMs)}</span>
          </div>
        </div>
      </div>

      {/* Real Progress or Honest Indeterminate Activity Bar */}
      {(status === 'running' || status === 'submitting' || status === 'progress' || isDelayed) && (
        <div className="space-y-1.5">
          <div className="flex justify-between items-center text-[11px] font-mono text-[#525866]">
            <span>
              {isIndeterminate
                ? expectedDurationMs
                  ? `Est. typical window: ~${(expectedDurationMs / 1000).toFixed(0)}s`
                  : 'Estimated completion time is not available for this operation.'
                : `Progress: ${Math.round(actualProgressPct || 0)}%`}
            </span>
            <span className="font-semibold text-[#1E2022]">
              {isIndeterminate ? (isDelayed ? 'Delayed' : 'Active') : `${Math.round(actualProgressPct || 0)}%`}
            </span>
          </div>

          {/* Bar */}
          <div className="w-full h-2 bg-[#E5E5E0] rounded-full overflow-hidden relative">
            {isIndeterminate ? (
              <div
                className={`indeterminate-bar h-full rounded-full ${
                  isDelayed ? 'bg-[#F97316]' : 'bg-[#2563EB]'
                }`}
              />
            ) : (
              <div
                className="h-full bg-[#2563EB] rounded-full transition-all duration-300"
                style={{ width: `${Math.min(100, Math.max(0, actualProgressPct || 0))}%` }}
              />
            )}
          </div>
        </div>
      )}

      {/* Delayed State Explanatory Callout */}
      {isDelayed && (status === 'running' || status === 'submitting' || status === 'delayed') && (
        <div className="p-3 rounded-lg bg-[#FFF7ED] border border-[#F97316]/40 text-xs text-[#1E2022] flex items-start gap-2.5">
          <AlertTriangle className="w-4 h-4 text-[#F97316] shrink-0 mt-0.5" />
          <div className="space-y-1">
            <span className="font-bold block">This operation is taking longer than usual.</span>
            <p className="text-[#525866] leading-relaxed">
              The calculation is still running. Elapsed time is shown above. You can keep waiting, or stop waiting if this panel offers that action.
            </p>
          </div>
        </div>
      )}

      {/* Error or Timeout Callout */}
      {(status === 'error' || status === 'timeout') && (
        <div className="p-3.5 rounded-lg bg-[#FFF7ED] border border-[#F97316]/40 text-xs text-[#1E2022] space-y-2">
          <div className="flex items-start gap-2">
            <XCircle className="w-4 h-4 text-[#F97316] shrink-0 mt-0.5" />
            <div className="space-y-1">
              <span className="font-bold text-[#1E2022] font-heading block">
                {status === 'timeout'
                  ? 'The calculation timed out'
                  : 'Unable to complete operation'}
              </span>
              <p className="text-[#525866] leading-relaxed">
                {errorMessage ||
                  (status === 'timeout'
                    ? "We haven't received a response within the configured waiting period. Your current formulation is preserved."
                    : 'The prediction service is temporarily unavailable. Your saved mix is unchanged. Try again or review the inputs.')}
              </p>
            </div>
          </div>

          {technicalDetails && (
            <div className="pt-2">
              <button
                type="button"
                onClick={() => setShowTechDetails(!showTechDetails)}
                className="inline-flex items-center gap-1 text-[11px] font-mono text-[#525866] hover:text-[#1E2022]"
              >
                <span>{showTechDetails ? 'Hide' : 'Show'} Technical Diagnostic</span>
                {showTechDetails ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
              </button>
              {showTechDetails && (
                <pre className="mt-1.5 p-2 rounded bg-[#FFFFFF] border border-[#E5E5E0] text-[10px] font-mono text-[#525866] overflow-x-auto whitespace-pre-wrap">
                  {technicalDetails}
                </pre>
              )}
            </div>
          )}
        </div>
      )}

      {/* Action Recovery Buttons */}
      {(onRetry || onCancel) && (
        <div className="flex items-center gap-2.5 pt-1">
          {onRetry && (
            <button
              onClick={onRetry}
              disabled={status === 'running' || status === 'submitting'}
              className="inline-flex items-center gap-1.5 px-3.5 py-1.5 rounded-md bg-[#2563EB] hover:bg-[#1D4ED8] text-white text-xs font-heading font-bold uppercase tracking-wider transition-all disabled:opacity-50 cursor-pointer shadow-xs"
            >
              <RefreshCw className="w-3.5 h-3.5" />
              <span>Try again</span>
            </button>
          )}

          {onCancel && (status === 'running' || status === 'submitting' || isDelayed) && (
            <button
              onClick={onCancel}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-md bg-[#FFFFFF] hover:bg-[#F5F5F3] text-[#525866] text-xs font-semibold border border-[#E5E5E0] transition-colors cursor-pointer"
            >
              <span>{cancelLabel}</span>
            </button>
          )}
        </div>
      )}
    </div>
  );
};


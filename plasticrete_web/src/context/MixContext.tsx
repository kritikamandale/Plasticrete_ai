import React, { createContext, useContext, useState, useEffect, useCallback, useRef } from 'react';
import type {
  MixInput,
  PredictionResponse,
  ScoreResponse,
  RecommendationResponse,
  FormulationRecord,
  PipelineStepStatus,
  TradeoffPoint,
  OptimizeResponse,
} from '../types';
import {
  DEFAULT_MIX,
  predictProperties,
  scoreSustainability,
  recommendApplications,
  listSavedFormulations,
  saveFormulation,
  duplicateSavedFormulation,
  deleteSavedFormulation,
} from '../api/client';
import { mixFromQuery, mixToQuery, pathFor, readLocation, type MainNavRoute, type StudioSubTab } from '../routing';
import type { OperationStatus } from '../components/OperationProgress';

export type { MainNavRoute, StudioSubTab };

interface PipelineState {
  m1: PipelineStepStatus;
  m2: PipelineStepStatus;
  m3: PipelineStepStatus;
  m4: PipelineStepStatus;
}

interface MixContextType {
  // Formulation state
  formulationId: string;
  formulationName: string;
  formulationVersion: number;
  isBaseline: boolean;
  mix: MixInput;
  setMix: (mix: MixInput | ((prev: MixInput) => MixInput)) => void;
  activeMix: MixInput; // Returns selected candidate mix or base mix

  // Candidate selection from M2
  selectedCandidate: TradeoffPoint | null;
  selectCandidate: (candidate: TradeoffPoint | null) => void;
  optimizationResult: OptimizeResponse | null;
  setOptimizationResult: (opt: OptimizeResponse | null) => void;

  // Pipeline execution state
  pipelineState: PipelineState;
  prediction: PredictionResponse | null;
  score: ScoreResponse | null;
  recommendation: RecommendationResponse | null;
  loading: boolean;
  refreshAll: (overrideMix?: MixInput) => Promise<void>;

  // Routing and Navigation
  mainRoute: MainNavRoute;
  setMainRoute: (route: MainNavRoute) => void;
  studioTab: StudioSubTab;
  setStudioTab: (tab: StudioSubTab) => void;
  applyPreset: (presetName: string) => void;
  inferenceSource: 'live' | 'unavailable';
  serviceError: string | null;
  batchId: string | null;
  openBatch: (id: string) => void;
  openBatchList: () => void;
  startNewMix: () => void;

  // Global Asynchronous Operation Status
  operationStatus: OperationStatus;
  operationTitle: string;
  operationDescription: string;
  operationStartTime: number | null;
  cancelOperation: () => void;

  // UI Drawers & Persistence
  isDrawerOpen: boolean;
  setIsDrawerOpen: (open: boolean) => void;
  isHistoryOpen: boolean;
  setIsHistoryOpen: (open: boolean) => void;
  savedFormulations: FormulationRecord[];
  fetchHistory: () => Promise<void>;
  saveCurrentFormulation: (customName?: string) => Promise<FormulationRecord | null>;
  restoreSavedFormulation: (record: FormulationRecord) => void;
  duplicateCurrentFormulation: (customName?: string) => Promise<FormulationRecord | null>;
  removeSavedFormulation: (id: string) => Promise<void>;
}

export const PRESETS: Record<string, MixInput> = {
  'M20 Eco-Standard (PET 15%)': {
    plastic_type: 'PET',
    replacement_pct: 15.0,
    particle_size_mm: 4.0,
    wc_ratio: 0.45,
    additive_type: 'fly_ash',
    additive_pct: 10.0,
    curing_temp_c: 27.0,
    curing_days: 28,
  },
  'High-Duty Paving (HDPE 20%)': {
    plastic_type: 'HDPE',
    replacement_pct: 20.0,
    particle_size_mm: 3.0,
    wc_ratio: 0.40,
    additive_type: 'silica_fume',
    additive_pct: 8.0,
    curing_temp_c: 35.0,
    curing_days: 28,
  },
  'Ultra-Green Diversion (Mixed 25%)': {
    plastic_type: 'Mixed',
    replacement_pct: 25.0,
    particle_size_mm: 5.0,
    wc_ratio: 0.42,
    additive_type: 'fly_ash',
    additive_pct: 15.0,
    curing_temp_c: 30.0,
    curing_days: 56,
  },
  'Lightweight Partition (LDPE 30%)': {
    plastic_type: 'LDPE',
    replacement_pct: 30.0,
    particle_size_mm: 2.0,
    wc_ratio: 0.50,
    additive_type: 'fibres',
    additive_pct: 2.0,
    curing_temp_c: 25.0,
    curing_days: 28,
  },
};

const STORAGE_KEY = 'plasticrete_active_formulation_v2';

const MixContext = createContext<MixContextType | undefined>(undefined);

export const MixProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const initialLocation = readLocation();

  // Load cached active formulation if available
  const cachedData = (() => {
    try {
      const item = localStorage.getItem(STORAGE_KEY);
      return item ? JSON.parse(item) : null;
    } catch {
      return null;
    }
  })();

  const [formulationId, setFormulationId] = useState<string>(
    cachedData?.id || `FORM-${Math.random().toString(16).slice(2, 8).toUpperCase()}`
  );
  const [formulationName, setFormulationName] = useState<string>(
    cachedData?.name || 'M20 Eco-Standard Formulation'
  );
  const [formulationVersion, setFormulationVersion] = useState<number>(cachedData?.version || 1);
  const [isBaseline, setIsBaseline] = useState<boolean>(cachedData?.isBaseline ?? true);

  const [mix, setMixState] = useState<MixInput>(() => {
    const urlMix = mixFromQuery(window.location.search);
    if (urlMix) return urlMix;
    if (cachedData?.mix) return cachedData.mix;
    return DEFAULT_MIX;
  });

  // M2 optimization candidates
  const [selectedCandidate, setSelectedCandidate] = useState<TradeoffPoint | null>(null);
  const [optimizationResult, setOptimizationResult] = useState<OptimizeResponse | null>(null);

  // Active mix is the selected candidate recipe if chosen, otherwise the baseline mix
  const activeMix: MixInput = selectedCandidate ? {
    plastic_type: selectedCandidate.recipe.plastic_type || mix.plastic_type,
    replacement_pct: selectedCandidate.recipe.replacement_pct,
    particle_size_mm: selectedCandidate.recipe.particle_size_mm,
    wc_ratio: selectedCandidate.recipe.wc_ratio,
    additive_type: selectedCandidate.recipe.additive_type || mix.additive_type,
    additive_pct: selectedCandidate.recipe.additive_pct,
    curing_temp_c: mix.curing_temp_c,
    curing_days: mix.curing_days,
  } : mix;

  const [prediction, setPrediction] = useState<PredictionResponse | null>(null);
  const [score, setScore] = useState<ScoreResponse | null>(null);
  const [recommendation, setRecommendation] = useState<RecommendationResponse | null>(null);

  const [pipelineState, setPipelineState] = useState<PipelineState>({
    m1: 'not_started',
    m2: 'not_started',
    m3: 'not_started',
    m4: 'not_started',
  });

  const [loading, setLoading] = useState<boolean>(false);
  const [inferenceSource, setInferenceSource] = useState<'live' | 'unavailable'>('unavailable');
  const [serviceError, setServiceError] = useState<string | null>(null);
  const [mainRoute, setMainRouteState] = useState<MainNavRoute>(initialLocation.route);
  const [studioTab, setStudioTabState] = useState<StudioSubTab>(initialLocation.tab);
  const [batchId, setBatchId] = useState<string | null>(initialLocation.batchId);

  // Operation progress states
  const [operationStatus, setOperationStatus] = useState<OperationStatus>('idle');
  const [operationTitle, setOperationTitle] = useState<string>('Preparing your prediction');
  const [operationDescription, setOperationDescription] = useState<string>('Ready');
  const [operationStartTime, setOperationStartTime] = useState<number | null>(null);

  // Drawers and DB history
  const [isDrawerOpen, setIsDrawerOpen] = useState(false);
  const [isHistoryOpen, setIsHistoryOpen] = useState(false);
  const [savedFormulations, setSavedFormulations] = useState<FormulationRecord[]>([]);

  const abortControllerRef = useRef<AbortController | null>(null);
  const activeRequestIdRef = useRef<number>(0);
  const skipUrlWrite = useRef(false);

  // Persist active formulation locally
  useEffect(() => {
    try {
      localStorage.setItem(
        STORAGE_KEY,
        JSON.stringify({
          id: formulationId,
          name: formulationName,
          version: formulationVersion,
          isBaseline,
          mix,
        })
      );
    } catch {
      // storage unavailable
    }
  }, [formulationId, formulationName, formulationVersion, isBaseline, mix]);

  const fetchHistory = useCallback(async () => {
    try {
      const records = await listSavedFormulations();
      setSavedFormulations(records);
    } catch {
      // ignore history fetch error on startup
    }
  }, []);

  useEffect(() => {
    fetchHistory();
  }, [fetchHistory]);

  const cancelOperation = useCallback(() => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      abortControllerRef.current = null;
    }
    setLoading(false);
    setOperationStatus('cancelled');
    setOperationDescription('Operation cancelled by user.');
  }, []);

  const setMix = (next: MixInput | ((prev: MixInput) => MixInput)) => {
    setMixState((prev) => {
      const resolved = typeof next === 'function' ? next(prev) : next;
      if (JSON.stringify(resolved) !== JSON.stringify(prev)) {
        setBatchId(null);
        setSelectedCandidate(null); // Return to base mix if modified
        setPipelineState({
          m1: 'stale',
          m2: 'stale',
          m3: 'stale',
          m4: 'stale',
        });
      }
      return resolved;
    });
  };

  const selectCandidate = (candidate: TradeoffPoint | null) => {
    setSelectedCandidate(candidate);
    // Mark downstream steps stale as new recipe is selected
    setPipelineState((prev) => ({
      ...prev,
      m3: 'ready',
      m4: 'ready',
    }));
  };

  const writeUrl = useCallback((route: MainNavRoute, tab: StudioSubTab, nextBatch: string | null, nextMix: MixInput, replace: boolean) => {
    const url = `${pathFor(route, tab, nextBatch)}?${mixToQuery(nextMix)}`;
    const current = `${window.location.pathname}${window.location.search}`;
    if (url === current) return;
    if (replace) window.history.replaceState({}, '', url);
    else window.history.pushState({}, '', url);
  }, []);

  const setMainRoute = (route: MainNavRoute) => {
    setMainRouteState(route);
    writeUrl(route, studioTab, route === 'batch' ? batchId : null, mix, false);
  };

  const setStudioTab = (tab: StudioSubTab) => {
    setStudioTabState(tab);
    setMainRouteState('studio');
    writeUrl('studio', tab, null, mix, false);
  };

  const openBatch = (id: string) => {
    setBatchId(id);
    setMainRouteState('batch');
    writeUrl('batch', studioTab, id, mix, false);
  };

  const openBatchList = () => {
    setBatchId(null);
    setMainRouteState('batch');
    writeUrl('batch', studioTab, null, mix, false);
  };

  const startNewMix = () => {
    setFormulationId(`FORM-${Math.random().toString(16).slice(2, 8).toUpperCase()}`);
    setFormulationName('New mix');
    setFormulationVersion(1);
    setIsBaseline(true);
    setOptimizationResult(null);
    setSelectedCandidate(null);
    setBatchId(null);
    setMixState(DEFAULT_MIX);
    setPipelineState({
      m1: 'stale',
      m2: 'stale',
      m3: 'stale',
      m4: 'stale',
    });
    setStudioTabState('overview');
    setMainRouteState('studio');
    setIsDrawerOpen(true);
    writeUrl('studio', 'overview', null, DEFAULT_MIX, false);
  };

  const refreshAll = useCallback(async (overrideMix?: MixInput) => {
    const targetMix = overrideMix || activeMix;

    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }
    const controller = new AbortController();
    abortControllerRef.current = controller;

    const requestId = ++activeRequestIdRef.current;
    const now = Date.now();

    setLoading(true);
    setOperationStatus('running');
    setOperationTitle('Preparing your prediction');
    setOperationDescription('Estimating seven concrete properties, environmental indicators, and application screening for this mix.');
    setOperationStartTime(now);
    setServiceError(null);

    setPipelineState({
      m1: 'running',
      m2: 'ready',
      m3: 'running',
      m4: 'running',
    });

    try {
      const pred = await predictProperties(targetMix, controller.signal);
      if (activeRequestIdRef.current !== requestId) return;
      setPrediction(pred);
      setPipelineState((prev) => ({ ...prev, m1: 'completed' }));

      const [sc, rec] = await Promise.all([
        scoreSustainability(targetMix, pred, controller.signal),
        recommendApplications(targetMix, pred, controller.signal),
      ]);

      if (activeRequestIdRef.current !== requestId) return;
      setScore(sc);
      setRecommendation(rec);
      setInferenceSource('live');
      setServiceError(null);
      setOperationStatus('success');
      setOperationDescription('Your prediction is ready.');

      setPipelineState((prev) => ({
        ...prev,
        m3: 'completed',
        m4: 'completed',
      }));
    } catch (e: unknown) {
      if (activeRequestIdRef.current !== requestId) return;
      if (e instanceof DOMException && e.name === 'AbortError') {
        return;
      }

      const errMsg = e instanceof Error ? e.message : 'The model service did not return a result.';
      const isTimeout = errMsg.toLowerCase().includes('time') && errMsg.toLowerCase().includes('out');

      setInferenceSource('unavailable');
      setServiceError(errMsg);
      setOperationStatus(isTimeout ? 'timeout' : 'error');
      setOperationDescription(errMsg);

      setPipelineState((prev) => ({
        ...prev,
        m1: prev.m1 === 'running' ? 'failed' : prev.m1,
        m3: prev.m3 === 'running' ? 'failed' : prev.m3,
        m4: prev.m4 === 'running' ? 'failed' : prev.m4,
      }));
    } finally {
      if (activeRequestIdRef.current === requestId) {
        setLoading(false);
      }
    }
  }, [activeMix]);

  useEffect(() => {
    // The mix search is CPU-heavy on the same API. Do not start another
    // prediction while the optimizer tab is idle on the entered mix.
    if (mainRoute === 'studio' && studioTab === 'optimizer' && !selectedCandidate) {
      return;
    }
    const timer = setTimeout(() => {
      refreshAll();
    }, 250);
    return () => clearTimeout(timer);
  }, [mix, selectedCandidate, mainRoute, studioTab]);

  useEffect(() => {
    const onPop = () => {
      skipUrlWrite.current = true;
      const location = readLocation();
      setMainRouteState(location.route);
      setStudioTabState(location.tab);
      setBatchId(location.batchId);
      const parsed = mixFromQuery(window.location.search);
      if (parsed) setMixState(parsed);
      skipUrlWrite.current = false;
    };
    window.addEventListener('popstate', onPop);
    return () => window.removeEventListener('popstate', onPop);
  }, []);

  useEffect(() => {
    if (skipUrlWrite.current) return;
    writeUrl(mainRoute, studioTab, batchId, mix, true);
  }, [mix, mainRoute, studioTab, batchId, writeUrl]);

  const applyPreset = (presetName: string) => {
    const found = PRESETS[presetName];
    if (found) {
      setFormulationName(presetName);
      setSelectedCandidate(null);
      setMix(found);
    }
  };

  const saveCurrentFormulation = async (customName?: string): Promise<FormulationRecord | null> => {
    const title = customName || formulationName || `Formulation ${formulationId}`;
    try {
      const saved = await saveFormulation({
        id: formulationId,
        name: title,
        version: formulationVersion,
        is_baseline: isBaseline,
        mix_params: mix,
        prediction: prediction || undefined,
        optimization: optimizationResult || undefined,
        score: score || undefined,
        recommendation: recommendation || undefined,
        status: 'active',
      });
      setFormulationName(saved.name);
      fetchHistory();
      return saved;
    } catch (err) {
      console.error('Failed to save formulation', err);
      return null;
    }
  };

  const restoreSavedFormulation = (record: FormulationRecord) => {
    setFormulationId(record.id);
    setFormulationName(record.name);
    setFormulationVersion(record.version);
    setIsBaseline(record.is_baseline);
    setMixState(record.mix_params);
    setSelectedCandidate(null);
    if (record.prediction) setPrediction(record.prediction);
    if (record.optimization) setOptimizationResult(record.optimization);
    if (record.score) setScore(record.score);
    if (record.recommendation) setRecommendation(record.recommendation);
    setPipelineState({
      m1: record.prediction ? 'completed' : 'ready',
      m2: record.optimization ? 'completed' : 'ready',
      m3: record.score ? 'completed' : 'ready',
      m4: record.recommendation ? 'completed' : 'ready',
    });
    setIsHistoryOpen(false);
  };

  const duplicateCurrentFormulation = async (customName?: string): Promise<FormulationRecord | null> => {
    try {
      const cloned = await duplicateSavedFormulation(formulationId, customName);
      restoreSavedFormulation(cloned);
      fetchHistory();
      return cloned;
    } catch {
      // If not yet saved in backend, clone locally
      const newId = `FORM-${Math.random().toString(16).slice(2, 8).toUpperCase()}`;
      const newVersion = formulationVersion + 1;
      const newName = customName || `${formulationName} (v${newVersion})`;
      setFormulationId(newId);
      setFormulationName(newName);
      setFormulationVersion(newVersion);
      setIsBaseline(false);
      return null;
    }
  };

  const removeSavedFormulation = async (id: string) => {
    try {
      await deleteSavedFormulation(id);
      fetchHistory();
    } catch (err) {
      console.error('Failed to delete formulation', err);
    }
  };

  return (
    <MixContext.Provider
      value={{
        formulationId,
        formulationName,
        formulationVersion,
        isBaseline,
        mix,
        setMix,
        activeMix,
        selectedCandidate,
        selectCandidate,
        optimizationResult,
        setOptimizationResult,
        pipelineState,
        prediction,
        score,
        recommendation,
        loading,
        refreshAll,
        mainRoute,
        setMainRoute,
        studioTab,
        setStudioTab,
        applyPreset,
        inferenceSource,
        serviceError,
        batchId,
        openBatch,
        openBatchList,
        startNewMix,
        operationStatus,
        operationTitle,
        operationDescription,
        operationStartTime,
        cancelOperation,
        isDrawerOpen,
        setIsDrawerOpen,
        isHistoryOpen,
        setIsHistoryOpen,
        savedFormulations,
        fetchHistory,
        saveCurrentFormulation,
        restoreSavedFormulation,
        duplicateCurrentFormulation,
        removeSavedFormulation,
      }}
    >
      {children}
    </MixContext.Provider>
  );
};

export const useMix = () => {
  const context = useContext(MixContext);
  if (!context) throw new Error('useMix must be used within a MixProvider');
  return context;
};

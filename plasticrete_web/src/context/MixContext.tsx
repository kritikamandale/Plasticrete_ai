import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import type {
  MixInput,
  PredictionResponse,
  ScoreResponse,
  RecommendationResponse,
} from '../types';
import {
  DEFAULT_MIX,
  predictProperties,
  scoreSustainability,
  recommendApplications,
} from '../api/client';

export type MainNavRoute = 'home' | 'studio' | 'standards' | 'technology';
export type StudioSubTab = 'overview' | 'optimizer' | 'sustainability' | 'recommender' | 'explainability';

interface MixContextType {
  mix: MixInput;
  setMix: (mix: MixInput | ((prev: MixInput) => MixInput)) => void;
  prediction: PredictionResponse | null;
  score: ScoreResponse | null;
  recommendation: RecommendationResponse | null;
  loading: boolean;
  refreshAll: () => Promise<void>;
  mainRoute: MainNavRoute;
  setMainRoute: (route: MainNavRoute) => void;
  studioTab: StudioSubTab;
  setStudioTab: (tab: StudioSubTab) => void;
  applyPreset: (presetName: string) => void;
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

const MixContext = createContext<MixContextType | undefined>(undefined);

export const MixProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [mix, setMix] = useState<MixInput>(DEFAULT_MIX);
  const [prediction, setPrediction] = useState<PredictionResponse | null>(null);
  const [score, setScore] = useState<ScoreResponse | null>(null);
  const [recommendation, setRecommendation] = useState<RecommendationResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [mainRoute, setMainRoute] = useState<MainNavRoute>('home');
  const [studioTab, setStudioTab] = useState<StudioSubTab>('overview');

  const refreshAll = useCallback(async () => {
    setLoading(true);
    try {
      const pred = await predictProperties(mix);
      setPrediction(pred);
      const [sc, rec] = await Promise.all([
        scoreSustainability(mix, pred),
        recommendApplications(mix, pred),
      ]);
      setScore(sc);
      setRecommendation(rec);
    } catch (e) {
      console.error('Refresh error:', e);
    } finally {
      setLoading(false);
    }
  }, [mix]);

  useEffect(() => {
    const timer = setTimeout(() => {
      refreshAll();
    }, 200);
    return () => clearTimeout(timer);
  }, [refreshAll]);

  const applyPreset = (presetName: string) => {
    if (PRESETS[presetName]) {
      setMix(PRESETS[presetName]);
    }
  };

  return (
    <MixContext.Provider
      value={{
        mix,
        setMix,
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
      }}
    >
      {children}
    </MixContext.Provider>
  );
};

export const useMix = () => {
  const context = useContext(MixContext);
  if (!context) throw new Error('useMix must be used within MixProvider');
  return context;
};

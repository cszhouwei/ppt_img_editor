/**
 * 编辑器全局状态管理
 * 使用 Zustand 管理应用状态
 */

import { create } from 'zustand';
import type { Page, Candidate, Patch, Layer, Project } from '../types';

interface EditorState {
  // 当前页面
  currentPage: Page | null;
  setCurrentPage: (page: Page | null) => void;

  // OCR 候选框
  candidates: Candidate[];
  setCandidates: (candidates: Candidate[]) => void;

  // 选中的候选框
  selectedCandidate: Candidate | null;
  setSelectedCandidate: (candidate: Candidate | null) => void;

  // 生成的 patches
  patches: Map<string, Patch>;
  addPatch: (patch: Patch) => void;

  // 图层
  layers: Layer[];
  setLayers: (layers: Layer[]) => void;
  addLayer: (layer: Layer) => void;
  updateLayer: (layerId: string, updates: Partial<Layer>) => void;
  removeLayer: (layerId: string) => void;

  // 当前项目
  currentProject: Project | null;
  setCurrentProject: (project: Project | null) => void;

  // UI 状态
  isLoading: boolean;
  setIsLoading: (isLoading: boolean) => void;

  loadingMessage: string;
  setLoadingMessage: (message: string) => void;

  // 重置状态
  reset: () => void;
}

const initialState = {
  currentPage: null,
  candidates: [],
  selectedCandidate: null,
  patches: new Map(),
  layers: [],
  currentProject: null,
  isLoading: false,
  loadingMessage: '',
};

export const useEditorStore = create<EditorState>((set) => ({
  ...initialState,

  setCurrentPage: (page) => set({ currentPage: page }),

  setCandidates: (candidates) => set({ candidates }),

  setSelectedCandidate: (candidate) => set({ selectedCandidate: candidate }),

  addPatch: (patch) =>
    set((state) => {
      const newPatches = new Map(state.patches);
      newPatches.set(patch.candidate_id, patch);
      return { patches: newPatches };
    }),

  setLayers: (layers) => set({ layers }),

  addLayer: (layer) =>
    set((state) => ({
      layers: [...state.layers, layer],
    })),

  updateLayer: (layerId, updates) =>
    set((state) => ({
      layers: state.layers.map((layer) =>
        layer.id === layerId ? { ...layer, ...updates } : layer
      ),
    })),

  removeLayer: (layerId) =>
    set((state) => ({
      layers: state.layers.filter((layer) => layer.id !== layerId),
    })),

  setCurrentProject: (project) => set({ currentProject: project }),

  setIsLoading: (isLoading) => set({ isLoading }),

  setLoadingMessage: (loadingMessage) => set({ loadingMessage }),

  reset: () => set(initialState),
}));

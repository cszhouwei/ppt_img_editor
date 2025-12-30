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

  // 选中的图层
  selectedLayer: Layer | null;
  setSelectedLayer: (layer: Layer | null) => void;

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
  selectedLayer: null,
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
    set((state) => {
      const updatedLayers = state.layers.map((layer) =>
        layer.id === layerId ? { ...layer, ...updates } as Layer : layer
      );

      // 同步更新 selectedLayer，确保编辑器显示最新值
      const updatedSelectedLayer =
        state.selectedLayer?.id === layerId
          ? updatedLayers.find((layer) => layer.id === layerId) || state.selectedLayer
          : state.selectedLayer;

      return {
        layers: updatedLayers,
        selectedLayer: updatedSelectedLayer,
      };
    }),

  removeLayer: (layerId) =>
    set((state) => ({
      layers: state.layers.filter((layer) => layer.id !== layerId),
      selectedLayer: state.selectedLayer?.id === layerId ? null : state.selectedLayer,
    })),

  setSelectedLayer: (layer) => set({ selectedLayer: layer }),

  setCurrentProject: (project) => set({ currentProject: project }),

  setIsLoading: (isLoading) => set({ isLoading }),

  setLoadingMessage: (loadingMessage) => set({ loadingMessage }),

  reset: () => set(initialState),
}));

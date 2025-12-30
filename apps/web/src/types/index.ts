/**
 * API 类型定义
 */

// Page 相关
export interface Page {
  page_id: string;
  image_url: string;
  width: number;
  height: number;
}

// Candidate (OCR 候选框)
export interface Candidate {
  id: string;
  text: string;
  confidence: number;
  quad: [number, number][];
  bbox: {
    x: number;
    y: number;
    w: number;
    h: number;
  };
  angle_deg: number;
}

// Patch
export interface Patch {
  id: string;
  page_id: string;
  candidate_id: string;
  bbox: {
    x: number;
    y: number;
    w: number;
    h: number;
  };
  image_url: string;
  debug_info?: Record<string, any>;
}

// Text Style
export interface TextStyle {
  fontFamily: string;
  fontSize: number;
  fontWeight: number;
  fill: string;
  letterSpacing: number;
  lineHeight: number;
}

// Layer (图层)
export interface PatchLayer {
  id: string;
  kind: 'patch';
  bbox: {
    x: number;
    y: number;
    w: number;
    h: number;
  };
  image_url: string;
}

export interface TextLayer {
  id: string;
  kind: 'text';
  text: string;
  quad: [number, number][];
  style: TextStyle;
}

export type Layer = PatchLayer | TextLayer;

// Project
export interface Project {
  project_id: string;
  page: {
    page_id: string;
    image_url: string;
    width: number;
    height: number;
  };
  layers: Layer[];
  created_at?: string;
  updated_at?: string;
}

// API Responses
export interface AssetUploadResponse {
  asset_id: string;
  image_url: string;
  width: number;
  height: number;
  sha256: string;
}

export interface CreatePageResponse {
  page_id: string;
}

export interface AnalyzeResponse {
  page_id: string;
  width: number;
  height: number;
  candidates: Candidate[];
}

export interface PatchResponse {
  patch: Patch;
}

export interface EstimateStyleResponse {
  candidate_id: string;
  style: TextStyle;
}

/**
 * API 服务层
 * 封装所有后端 API 调用
 */

import axios from 'axios';
import type {
  AssetUploadResponse,
  CreatePageResponse,
  AnalyzeResponse,
  PatchResponse,
  EstimateStyleResponse,
  Project,
  ExportResponse,
} from '../types';

// 创建 axios 实例
const api = axios.create({
  baseURL: '/api',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// 响应拦截器
api.interceptors.response.use(
  (response) => response.data,
  (error) => {
    console.error('API Error:', error.response?.data || error.message);
    return Promise.reject(error);
  }
);

/**
 * 上传图片资产
 */
export async function uploadAsset(file: File): Promise<AssetUploadResponse> {
  const formData = new FormData();
  formData.append('file', file);

  return api.post('/v1/assets/upload', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
}

/**
 * 创建 Page
 */
export async function createPage(params: {
  image_url: string;
  width: number;
  height: number;
}): Promise<CreatePageResponse> {
  return api.post('/v1/pages', params);
}

/**
 * OCR 分析
 */
export async function analyzePage(
  pageId: string,
  params: {
    provider?: string;
    lang_hints?: string[];
  } = {}
): Promise<AnalyzeResponse> {
  return api.post(`/v1/pages/${pageId}/analyze`, {
    provider: params.provider || 'mock',
    lang_hints: params.lang_hints || ['zh-Hans', 'en'],
  });
}

/**
 * 获取候选框列表
 */
export async function getCandidates(pageId: string): Promise<AnalyzeResponse> {
  return api.get(`/v1/pages/${pageId}/candidates`);
}

/**
 * 生成 Patch
 */
export async function generatePatch(
  pageId: string,
  params: {
    candidate_id: string;
    padding_px?: number;
    mode?: string;
    algo_version?: string;
  }
): Promise<PatchResponse> {
  return api.post(`/v1/pages/${pageId}/patch`, {
    candidate_id: params.candidate_id,
    padding_px: params.padding_px || 8,
    mode: params.mode || 'auto',
    algo_version: params.algo_version || 'v1',
  });
}

/**
 * 估计文本样式
 */
export async function estimateStyle(
  pageId: string,
  candidateId: string
): Promise<EstimateStyleResponse> {
  return api.post(`/v1/pages/${pageId}/estimate-style`, {
    candidate_id: candidateId,
  });
}

/**
 * 创建项目
 */
export async function createProject(params: {
  page: {
    page_id: string;
    image_url: string;
    width: number;
    height: number;
  };
  layers?: any[];
}): Promise<Project> {
  return api.post('/v1/projects', {
    page: params.page,
    layers: params.layers || [],
  });
}

/**
 * 获取项目
 */
export async function getProject(projectId: string): Promise<Project> {
  return api.get(`/v1/projects/${projectId}`);
}

/**
 * 更新项目
 */
export async function updateProject(
  projectId: string,
  params: {
    page: any;
    layers: any[];
  }
): Promise<Project> {
  return api.put(`/v1/projects/${projectId}`, params);
}

/**
 * 删除项目
 */
export async function deleteProject(projectId: string): Promise<void> {
  return api.delete(`/v1/projects/${projectId}`);
}

/**
 * 导出项目为 PNG
 */
export async function exportProject(projectId: string): Promise<ExportResponse> {
  return api.post(`/v1/projects/${projectId}/export/png`);
}

/**
 * 工具栏组件
 * 包含保存、导出等操作
 */

import { useState } from 'react';
import { useEditorStore } from '../store/useEditorStore';
import { createProject, updateProject, exportProject } from '../services/api';

export function Toolbar() {
  const currentPage = useEditorStore((state) => state.currentPage);
  const layers = useEditorStore((state) => state.layers);
  const currentProject = useEditorStore((state) => state.currentProject);
  const setCurrentProject = useEditorStore((state) => state.setCurrentProject);
  const setIsLoading = useEditorStore((state) => state.setIsLoading);
  const setLoadingMessage = useEditorStore((state) => state.setLoadingMessage);
  const reset = useEditorStore((state) => state.reset);

  const [exportUrl, setExportUrl] = useState<string | null>(null);

  // 保存项目
  const handleSave = async () => {
    if (!currentPage) return;

    try {
      setIsLoading(true);
      setLoadingMessage('保存项目中...');

      if (currentProject) {
        // 更新现有项目
        const updated = await updateProject(currentProject.project_id, {
          page: currentPage,
          layers,
        });
        setCurrentProject(updated);
        alert('项目已保存!');
      } else {
        // 创建新项目
        const project = await createProject({
          page: currentPage,
          layers,
        });
        setCurrentProject(project);
        alert(`项目已创建! ID: ${project.project_id}`);
      }
    } catch (error) {
      console.error('Save failed:', error);
      alert('保存失败,请重试');
    } finally {
      setIsLoading(false);
      setLoadingMessage('');
    }
  };

  // 导出为 PNG
  const handleExport = async () => {
    if (!currentProject) {
      alert('请先保存项目');
      return;
    }

    try {
      setIsLoading(true);
      setLoadingMessage('导出 PNG 中...');

      const response = await exportProject(currentProject.project_id);
      setExportUrl(response.export_url);

      // 自动下载
      const link = document.createElement('a');
      link.href = response.export_url;
      link.download = `export_${Date.now()}.png`;
      link.click();

      alert('导出成功!');
    } catch (error) {
      console.error('Export failed:', error);
      alert('导出失败,请重试');
    } finally {
      setIsLoading(false);
      setLoadingMessage('');
    }
  };

  // 重新开始
  const handleReset = () => {
    if (confirm('确定要重新开始吗? 未保存的更改将丢失。')) {
      reset();
      setExportUrl(null);
    }
  };

  if (!currentPage) {
    return null;
  }

  return (
    <div className="toolbar">
      <div className="toolbar-left">
        <h2>PPT 文字编辑器</h2>
        {currentProject && (
          <span className="project-id">项目: {currentProject.project_id}</span>
        )}
      </div>

      <div className="toolbar-right">
        <button className="btn-secondary" onClick={handleReset}>
          重新开始
        </button>
        <button className="btn-secondary" onClick={handleSave}>
          💾 保存项目
        </button>
        <button
          className="btn-primary"
          onClick={handleExport}
          disabled={!currentProject}
        >
          📥 导出 PNG
        </button>
      </div>

      {exportUrl && (
        <div className="export-success">
          ✅ 导出成功!{' '}
          <a href={exportUrl} target="_blank" rel="noopener noreferrer">
            查看图片
          </a>
        </div>
      )}
    </div>
  );
}

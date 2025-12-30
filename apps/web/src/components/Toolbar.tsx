/**
 * 工具栏组件
 * 包含保存、导出等操作
 */

import { useState, useEffect } from 'react';
import { useEditorStore } from '../store/useEditorStore';
import { createProject, updateProject, listProjects, getProject } from '../services/api';
import type { Project } from '../types';

export function Toolbar() {
  const currentPage = useEditorStore((state) => state.currentPage);
  const layers = useEditorStore((state) => state.layers);
  const currentProject = useEditorStore((state) => state.currentProject);
  const setCurrentProject = useEditorStore((state) => state.setCurrentProject);
  const setCurrentPage = useEditorStore((state) => state.setCurrentPage);
  const setLayers = useEditorStore((state) => state.setLayers);
  const setIsLoading = useEditorStore((state) => state.setIsLoading);
  const setLoadingMessage = useEditorStore((state) => state.setLoadingMessage);
  const reset = useEditorStore((state) => state.reset);

  const [projects, setProjects] = useState<Project[]>([]);
  const [showProjectMenu, setShowProjectMenu] = useState(false);

  // 加载项目列表
  const loadProjectList = async () => {
    try {
      const projectList = await listProjects();
      setProjects(projectList);
    } catch (error) {
      console.error('Failed to load projects:', error);
    }
  };

  // 切换到指定项目
  const handleLoadProject = async (projectId: string) => {
    try {
      setIsLoading(true);
      setLoadingMessage('加载项目中...');
      setShowProjectMenu(false);

      const project = await getProject(projectId);

      // 更新 store
      setCurrentPage(project.page);
      setLayers(project.layers);
      setCurrentProject(project);

      alert(`项目已加载: ${projectId}`);
    } catch (error) {
      console.error('Failed to load project:', error);
      alert('加载项目失败,请重试');
    } finally {
      setIsLoading(false);
      setLoadingMessage('');
    }
  };

  // 切换项目菜单显示状态
  const toggleProjectMenu = () => {
    if (!showProjectMenu) {
      loadProjectList();
    }
    setShowProjectMenu(!showProjectMenu);
  };

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

  // 重新开始
  const handleReset = () => {
    if (confirm('确定要重新开始吗? 未保存的更改将丢失。')) {
      reset();
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
        <button className="btn-secondary" onClick={handleSave}>
          💾 保存项目
        </button>
        <div className="project-switcher" style={{ position: 'relative' }}>
          <button className="btn-secondary" onClick={toggleProjectMenu}>
            📂 {showProjectMenu ? '关闭' : '切换项目'}
          </button>
          {showProjectMenu && (
            <div className="project-menu" style={{
              position: 'absolute',
              top: '100%',
              right: 0,
              marginTop: '4px',
              backgroundColor: 'white',
              border: '1px solid #ccc',
              borderRadius: '4px',
              boxShadow: '0 2px 8px rgba(0,0,0,0.15)',
              minWidth: '300px',
              maxHeight: '400px',
              overflowY: 'auto',
              zIndex: 1000
            }}>
              {projects.length === 0 ? (
                <div style={{ padding: '16px', textAlign: 'center', color: '#666' }}>
                  暂无已保存的项目
                </div>
              ) : (
                <ul style={{ listStyle: 'none', margin: 0, padding: 0 }}>
                  {projects.map((project) => (
                    <li
                      key={project.project_id}
                      style={{
                        padding: '12px 16px',
                        borderBottom: '1px solid #eee',
                        cursor: 'pointer',
                        backgroundColor: project.project_id === currentProject?.project_id ? '#f0f0f0' : 'white'
                      }}
                      onClick={() => handleLoadProject(project.project_id)}
                      onMouseEnter={(e) => e.currentTarget.style.backgroundColor = '#f5f5f5'}
                      onMouseLeave={(e) => e.currentTarget.style.backgroundColor = project.project_id === currentProject?.project_id ? '#f0f0f0' : 'white'}
                    >
                      <div style={{ fontWeight: 'bold', marginBottom: '4px' }}>
                        {project.project_id}
                      </div>
                      <div style={{ fontSize: '12px', color: '#666' }}>
                        更新: {new Date(project.updated_at).toLocaleString('zh-CN')}
                      </div>
                    </li>
                  ))}
                </ul>
              )}
            </div>
          )}
        </div>
        <button className="btn-secondary" onClick={handleReset}>
          🔄 重新开始
        </button>
      </div>
    </div>
  );
}

/**
 * 图层面板组件
 * 显示和管理所有图层
 */

import { useEditorStore } from '../store/useEditorStore';
import type { Layer } from '../types';

export function LayerPanel() {
  const layers = useEditorStore((state) => state.layers);
  const removeLayer = useEditorStore((state) => state.removeLayer);

  const handleDeleteLayer = (layerId: string) => {
    if (confirm('确定要删除这个图层吗?')) {
      removeLayer(layerId);
    }
  };

  const getLayerPreview = (layer: Layer): string => {
    if (layer.kind === 'text') {
      return `文本: ${layer.text.substring(0, 20)}${
        layer.text.length > 20 ? '...' : ''
      }`;
    } else {
      return `Patch: ${layer.bbox.w}x${layer.bbox.h}`;
    }
  };

  return (
    <div className="layer-panel">
      <h3>图层列表 ({layers.length})</h3>

      {layers.length === 0 ? (
        <p className="empty-message">暂无图层</p>
      ) : (
        <div className="layer-list">
          {layers.map((layer, index) => (
            <div key={layer.id} className="layer-item">
              <div className="layer-info">
                <span className="layer-type">
                  {layer.kind === 'text' ? '📝' : '🖼️'}
                </span>
                <span className="layer-name">{getLayerPreview(layer)}</span>
                <span className="layer-index">#{index + 1}</span>
              </div>
              <button
                className="btn-delete"
                onClick={() => handleDeleteLayer(layer.id)}
                title="删除图层"
              >
                ✕
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

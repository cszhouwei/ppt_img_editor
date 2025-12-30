/**
 * 文本编辑面板组件
 * 用于编辑选中的文本图层
 *
 * 特性：
 * - 实时更新：任何修改立即生效，无需点击按钮
 * - 直接操作 store：不使用本地 state，避免同步问题
 * - 智能输入：数字框支持临时编辑，失焦或回车时生效
 */

import { useState, useMemo, useEffect } from 'react';
import { useEditorStore } from '../store/useEditorStore';
import type { TextLayer } from '../types';

export function TextEditor() {
  const selectedLayer = useEditorStore((state) => state.selectedLayer);
  const updateLayer = useEditorStore((state) => state.updateLayer);

  // 获取当前选中的文本图层
  const currentTextLayer: TextLayer | null =
    selectedLayer && selectedLayer.kind === 'text' ? selectedLayer : null;

  // 字号输入框的临时值（用于支持多位数输入）
  const [fontSizeInput, setFontSizeInput] = useState<string>('');
  const [isEditingFontSize, setIsEditingFontSize] = useState(false);

  // 当图层切换或字号变化时，更新本地输入框状态（仅在非编辑状态）
  useEffect(() => {
    if (currentTextLayer && !isEditingFontSize) {
      setFontSizeInput(String(currentTextLayer.style.fontSize));
    }
  }, [currentTextLayer?.id, currentTextLayer?.style.fontSize]);

  // 当图层切换时，强制退出编辑状态
  useEffect(() => {
    setIsEditingFontSize(false);
  }, [currentTextLayer?.id]);

  // 实时更新文本内容
  const handleTextChange = (newText: string) => {
    if (!currentTextLayer) return;
    updateLayer(currentTextLayer.id, { text: newText });
  };

  // 实时更新字号（滑块用）
  const handleFontSizeChange = (newSize: number) => {
    if (!currentTextLayer) return;
    // 限制范围
    const clampedSize = Math.max(12, Math.min(500, newSize));
    updateLayer(currentTextLayer.id, {
      style: {
        ...currentTextLayer.style,
        fontSize: clampedSize,
      },
    });
  };

  // 字号输入框开始编辑
  const handleFontSizeInputFocus = () => {
    if (!currentTextLayer) return;
    setIsEditingFontSize(true);
    setFontSizeInput(String(currentTextLayer.style.fontSize));
  };

  // 字号输入框内容变化
  const handleFontSizeInputChange = (value: string) => {
    // 允许输入空值或数字
    if (value === '' || /^\d+$/.test(value)) {
      setFontSizeInput(value);
    }
  };

  // 字号输入框失焦或回车 - 应用修改
  const handleFontSizeInputBlur = () => {
    if (!currentTextLayer) return;
    setIsEditingFontSize(false);

    const numValue = parseInt(fontSizeInput, 10);
    if (!isNaN(numValue)) {
      // 限制范围
      const clampedSize = Math.max(12, Math.min(500, numValue));
      handleFontSizeChange(clampedSize);
    }
  };

  // 字号输入框按键处理
  const handleFontSizeInputKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') {
      e.currentTarget.blur(); // 触发失焦，应用修改
    } else if (e.key === 'Escape') {
      // 取消编辑，恢复原值
      setIsEditingFontSize(false);
      if (currentTextLayer) {
        setFontSizeInput(String(currentTextLayer.style.fontSize));
      }
    }
  };

  // 实时更新字重
  const handleFontWeightChange = (newWeight: number) => {
    if (!currentTextLayer) return;
    updateLayer(currentTextLayer.id, {
      style: {
        ...currentTextLayer.style,
        fontWeight: newWeight,
      },
    });
  };

  // 实时更新颜色
  const handleColorChange = (newColor: string) => {
    if (!currentTextLayer) return;

    // 解析颜色 (#rrggbb -> rgba)
    const r = parseInt(newColor.slice(1, 3), 16);
    const g = parseInt(newColor.slice(3, 5), 16);
    const b = parseInt(newColor.slice(5, 7), 16);

    updateLayer(currentTextLayer.id, {
      style: {
        ...currentTextLayer.style,
        fill: `rgba(${r},${g},${b},1)`,
      },
    });
  };

  // 将 rgba 颜色转换为 hex 格式（用于 color input）
  // 使用 useMemo 避免每次渲染都重新计算
  const hexColor = useMemo(() => {
    if (!currentTextLayer) return '#1e1e1e';

    const match = currentTextLayer.style.fill.match(/rgba?\((\d+),(\d+),(\d+)/);
    if (match) {
      const r = parseInt(match[1]).toString(16).padStart(2, '0');
      const g = parseInt(match[2]).toString(16).padStart(2, '0');
      const b = parseInt(match[3]).toString(16).padStart(2, '0');
      return `#${r}${g}${b}`;
    }
    return '#1e1e1e';
  }, [currentTextLayer?.style.fill]);

  if (!currentTextLayer) {
    return (
      <div className="text-editor empty">
        <p>选择文本图层以编辑</p>
      </div>
    );
  }

  return (
    <div className="text-editor">
      <h3>文本编辑</h3>

      <div className="editor-field">
        <label>文本内容</label>
        <textarea
          value={currentTextLayer.text}
          onChange={(e) => handleTextChange(e.target.value)}
          rows={3}
        />
      </div>

      <div className="editor-field">
        <label>字号: {currentTextLayer.style.fontSize}px</label>
        <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
          <input
            type="range"
            min="12"
            max="500"
            value={currentTextLayer.style.fontSize}
            onChange={(e) => handleFontSizeChange(Number(e.target.value))}
            style={{ flex: 1 }}
          />
          <input
            type="number"
            min="12"
            max="500"
            value={isEditingFontSize ? fontSizeInput : currentTextLayer.style.fontSize}
            onFocus={handleFontSizeInputFocus}
            onChange={(e) => handleFontSizeInputChange(e.target.value)}
            onBlur={handleFontSizeInputBlur}
            onKeyDown={handleFontSizeInputKeyDown}
            style={{ width: '70px' }}
          />
        </div>
      </div>

      <div className="editor-field">
        <label>字重</label>
        <select
          value={currentTextLayer.style.fontWeight}
          onChange={(e) => handleFontWeightChange(Number(e.target.value))}
        >
          <option value={400}>Normal (400)</option>
          <option value={600}>Semi-bold (600)</option>
          <option value={700}>Bold (700)</option>
        </select>
      </div>

      <div className="editor-field">
        <label>颜色</label>
        <div className="color-picker">
          <input
            type="color"
            value={hexColor}
            onChange={(e) => handleColorChange(e.target.value)}
          />
          <span>{hexColor}</span>
        </div>
      </div>
    </div>
  );
}

/**
 * 文本编辑面板组件
 * 用于编辑选中的文本图层
 */

import { useState, useEffect } from 'react';
import { useEditorStore } from '../store/useEditorStore';
import type { TextLayer } from '../types';

export function TextEditor() {
  const layers = useEditorStore((state) => state.layers);
  const selectedCandidate = useEditorStore((state) => state.selectedCandidate);
  const updateLayer = useEditorStore((state) => state.updateLayer);

  // 查找当前选中候选框对应的文本图层
  const currentTextLayer = layers.find(
    (layer): layer is TextLayer =>
      layer.kind === 'text' &&
      selectedCandidate !== null &&
      layer.id.includes(selectedCandidate.id)
  );

  const [text, setText] = useState('');
  const [fontSize, setFontSize] = useState(32);
  const [fontWeight, setFontWeight] = useState(400);
  const [color, setColor] = useState('#1e1e1e');

  // 同步图层数据到本地状态
  useEffect(() => {
    if (currentTextLayer) {
      setText(currentTextLayer.text);
      setFontSize(currentTextLayer.style.fontSize);
      setFontWeight(currentTextLayer.style.fontWeight);

      // 解析颜色 (rgba(r,g,b,a) -> #rrggbb)
      const match = currentTextLayer.style.fill.match(/rgba?\((\d+),(\d+),(\d+)/);
      if (match) {
        const r = parseInt(match[1]).toString(16).padStart(2, '0');
        const g = parseInt(match[2]).toString(16).padStart(2, '0');
        const b = parseInt(match[3]).toString(16).padStart(2, '0');
        setColor(`#${r}${g}${b}`);
      }
    }
  }, [currentTextLayer]);

  // 应用更改
  const handleApplyChanges = () => {
    if (!currentTextLayer) return;

    // 解析颜色
    const r = parseInt(color.slice(1, 3), 16);
    const g = parseInt(color.slice(3, 5), 16);
    const b = parseInt(color.slice(5, 7), 16);

    updateLayer(currentTextLayer.id, {
      text,
      style: {
        ...currentTextLayer.style,
        fontSize,
        fontWeight,
        fill: `rgba(${r},${g},${b},1)`,
      },
    });
  };

  if (!currentTextLayer) {
    return (
      <div className="text-editor empty">
        <p>点击候选框以编辑文本</p>
      </div>
    );
  }

  return (
    <div className="text-editor">
      <h3>文本编辑</h3>

      <div className="editor-field">
        <label>文本内容</label>
        <textarea
          value={text}
          onChange={(e) => setText(e.target.value)}
          rows={3}
        />
      </div>

      <div className="editor-field">
        <label>字号: {fontSize}px</label>
        <input
          type="range"
          min="12"
          max="72"
          value={fontSize}
          onChange={(e) => setFontSize(Number(e.target.value))}
        />
      </div>

      <div className="editor-field">
        <label>字重</label>
        <select
          value={fontWeight}
          onChange={(e) => setFontWeight(Number(e.target.value))}
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
            value={color}
            onChange={(e) => setColor(e.target.value)}
          />
          <span>{color}</span>
        </div>
      </div>

      <button className="btn-primary" onClick={handleApplyChanges}>
        应用更改
      </button>
    </div>
  );
}

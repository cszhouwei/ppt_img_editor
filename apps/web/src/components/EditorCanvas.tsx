/**
 * 编辑器画布组件
 * 显示图片并叠加 OCR 候选框
 */

import { useEffect, useRef } from 'react';
import { useEditorStore } from '../store/useEditorStore';
import { generatePatch, estimateStyle } from '../services/api';

export function EditorCanvas() {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  const currentPage = useEditorStore((state) => state.currentPage);
  const candidates = useEditorStore((state) => state.candidates);
  const selectedCandidate = useEditorStore((state) => state.selectedCandidate);
  const setSelectedCandidate = useEditorStore((state) => state.setSelectedCandidate);
  const addPatch = useEditorStore((state) => state.addPatch);
  const addLayer = useEditorStore((state) => state.addLayer);
  const setIsLoading = useEditorStore((state) => state.setIsLoading);
  const setLoadingMessage = useEditorStore((state) => state.setLoadingMessage);

  // 绘制画布
  useEffect(() => {
    if (!currentPage || !canvasRef.current) return;

    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    // 设置画布大小
    canvas.width = currentPage.width;
    canvas.height = currentPage.height;

    // 加载并绘制图片
    const img = new Image();
    img.crossOrigin = 'anonymous';
    img.onload = () => {
      ctx.drawImage(img, 0, 0);

      // 绘制候选框
      candidates.forEach((candidate) => {
        const isSelected = selectedCandidate?.id === candidate.id;

        ctx.strokeStyle = isSelected ? '#ff0000' : '#00ff00';
        ctx.lineWidth = isSelected ? 3 : 2;
        ctx.globalAlpha = 0.7;

        // 绘制四边形
        ctx.beginPath();
        ctx.moveTo(candidate.quad[0][0], candidate.quad[0][1]);
        for (let i = 1; i < candidate.quad.length; i++) {
          ctx.lineTo(candidate.quad[i][0], candidate.quad[i][1]);
        }
        ctx.closePath();
        ctx.stroke();

        ctx.globalAlpha = 1.0;
      });
    };
    img.src = currentPage.image_url;
  }, [currentPage, candidates, selectedCandidate]);

  // 处理点击选择候选框
  const handleCanvasClick = async (e: React.MouseEvent<HTMLCanvasElement>) => {
    if (!canvasRef.current || !currentPage) return;

    const rect = canvasRef.current.getBoundingClientRect();
    const scaleX = currentPage.width / rect.width;
    const scaleY = currentPage.height / rect.height;

    const x = (e.clientX - rect.left) * scaleX;
    const y = (e.clientY - rect.top) * scaleY;

    // 查找被点击的候选框
    for (const candidate of candidates) {
      if (isPointInQuad(x, y, candidate.quad)) {
        setSelectedCandidate(candidate);

        // 自动生成 patch 和估计样式
        try {
          setIsLoading(true);
          setLoadingMessage('生成 patch 中...');

          const [patchResponse, styleResponse] = await Promise.all([
            generatePatch(currentPage.page_id, {
              candidate_id: candidate.id,
            }),
            estimateStyle(currentPage.page_id, candidate.id),
          ]);

          // 保存 patch
          addPatch(patchResponse.patch);

          // 添加图层
          addLayer({
            id: `patch_${patchResponse.patch.id}`,
            kind: 'patch',
            bbox: patchResponse.patch.bbox,
            image_url: patchResponse.patch.image_url,
          });

          addLayer({
            id: `text_${candidate.id}`,
            kind: 'text',
            text: candidate.text,
            quad: candidate.quad,
            style: styleResponse.style,
          });

          console.log('Patch and text layer created');
        } catch (error) {
          console.error('Failed to generate patch:', error);
        } finally {
          setIsLoading(false);
          setLoadingMessage('');
        }

        break;
      }
    }
  };

  // 检查点是否在四边形内
  const isPointInQuad = (
    x: number,
    y: number,
    quad: [number, number][]
  ): boolean => {
    const bbox = {
      x: Math.min(...quad.map((p) => p[0])),
      y: Math.min(...quad.map((p) => p[1])),
      w: Math.max(...quad.map((p) => p[0])) - Math.min(...quad.map((p) => p[0])),
      h: Math.max(...quad.map((p) => p[1])) - Math.min(...quad.map((p) => p[1])),
    };

    return (
      x >= bbox.x &&
      x <= bbox.x + bbox.w &&
      y >= bbox.y &&
      y <= bbox.y + bbox.h
    );
  };

  if (!currentPage) {
    return null;
  }

  return (
    <div ref={containerRef} className="canvas-container">
      <canvas
        ref={canvasRef}
        className="editor-canvas"
        onClick={handleCanvasClick}
      />
    </div>
  );
}

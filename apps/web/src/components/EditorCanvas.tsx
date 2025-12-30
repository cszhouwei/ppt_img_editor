/**
 * 编辑器画布组件
 * 显示图片并叠加 OCR 候选框
 */

import { useEffect, useRef, useState, useCallback } from 'react';
import { useEditorStore } from '../store/useEditorStore';
import { generatePatch, estimateStyle } from '../services/api';
import type { Layer } from '../types';

export function EditorCanvas() {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  const currentPage = useEditorStore((state) => state.currentPage);
  const candidates = useEditorStore((state) => state.candidates);
  const selectedCandidate = useEditorStore((state) => state.selectedCandidate);
  const setSelectedCandidate = useEditorStore((state) => state.setSelectedCandidate);
  const addPatch = useEditorStore((state) => state.addPatch);
  const addLayer = useEditorStore((state) => state.addLayer);
  const layers = useEditorStore((state) => state.layers);
  const selectedLayer = useEditorStore((state) => state.selectedLayer);
  const setSelectedLayer = useEditorStore((state) => state.setSelectedLayer);
  const updateLayer = useEditorStore((state) => state.updateLayer);
  const setIsLoading = useEditorStore((state) => state.setIsLoading);
  const setLoadingMessage = useEditorStore((state) => state.setLoadingMessage);

  // 拖动状态
  const [isDragging, setIsDragging] = useState(false);
  const dragRef = useRef({
    offset: { x: 0, y: 0 },
    currentPos: null as { x: number; y: number } | null,
  });

  // 缓存图片
  const imageCache = useRef<{
    base: HTMLImageElement | null;
    patches: Map<string, HTMLImageElement>;
  }>({
    base: null,
    patches: new Map(),
  });

  // 绘制画布
  const drawCanvas = useCallback(() => {
    if (!currentPage || !canvasRef.current) return;

    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    // 清空画布
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    // 绘制原始图片
    if (imageCache.current.base) {
      ctx.drawImage(imageCache.current.base, 0, 0);
    }

    // 绘制图层
    layers.forEach((layer) => {
      if (layer.kind === 'patch') {
        const patchImg = imageCache.current.patches.get(layer.id);
        if (!patchImg) return;

        // 如果是正在拖动的图层，使用拖动位置
        let bbox = layer.bbox;
        if (isDragging && selectedLayer?.id === layer.id && dragRef.current.currentPos) {
          bbox = {
            ...layer.bbox,
            x: dragRef.current.currentPos.x - dragRef.current.offset.x,
            y: dragRef.current.currentPos.y - dragRef.current.offset.y,
          };
        }

        ctx.drawImage(patchImg, bbox.x, bbox.y, bbox.w, bbox.h);

        // 绘制选中边框
        if (selectedLayer?.id === layer.id) {
          ctx.strokeStyle = '#0066ff';
          ctx.lineWidth = 2;
          ctx.setLineDash([5, 5]);
          ctx.strokeRect(bbox.x, bbox.y, bbox.w, bbox.h);
          ctx.setLineDash([]);
        }
      } else if (layer.kind === 'text') {
        const style = layer.style;

        // 计算文本位置
        let quad = layer.quad;
        if (isDragging && selectedLayer?.id === layer.id && dragRef.current.currentPos) {
          const deltaX = dragRef.current.currentPos.x - dragRef.current.offset.x - layer.quad[0][0];
          const deltaY = dragRef.current.currentPos.y - dragRef.current.offset.y - layer.quad[0][1];
          quad = layer.quad.map(([px, py]) => [px + deltaX, py + deltaY] as [number, number]);
        }

        const x = quad[0][0];
        const y = quad[0][1];

        // 设置文本样式
        ctx.font = `${style.fontWeight} ${style.fontSize}px ${style.fontFamily}`;
        ctx.fillStyle = style.fill;
        ctx.textBaseline = 'top';

        // 绘制文本
        ctx.fillText(layer.text, x, y);

        // 绘制选中边框
        if (selectedLayer?.id === layer.id) {
          const metrics = ctx.measureText(layer.text);
          const textWidth = metrics.width;
          const textHeight = style.fontSize * 1.2;

          ctx.strokeStyle = '#0066ff';
          ctx.lineWidth = 2;
          ctx.setLineDash([5, 5]);
          ctx.strokeRect(x - 2, y - 2, textWidth + 4, textHeight + 4);
          ctx.setLineDash([]);
        }
      }
    });

    // 绘制候选框
    candidates.forEach((candidate) => {
      const isSelected = selectedCandidate?.id === candidate.id;

      ctx.strokeStyle = isSelected ? '#ff0000' : '#00ff00';
      ctx.lineWidth = isSelected ? 3 : 2;
      ctx.globalAlpha = 0.7;

      ctx.beginPath();
      ctx.moveTo(candidate.quad[0][0], candidate.quad[0][1]);
      for (let i = 1; i < candidate.quad.length; i++) {
        ctx.lineTo(candidate.quad[i][0], candidate.quad[i][1]);
      }
      ctx.closePath();
      ctx.stroke();

      ctx.globalAlpha = 1.0;
    });
  }, [currentPage, candidates, selectedCandidate, layers, selectedLayer, isDragging]);

  // 初始化和更新画布
  useEffect(() => {
    if (!currentPage || !canvasRef.current) return;

    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    // 设置画布大小
    canvas.width = currentPage.width;
    canvas.height = currentPage.height;

    // 加载基础图片
    if (!imageCache.current.base || imageCache.current.base.src !== currentPage.image_url) {
      const img = new Image();
      img.crossOrigin = 'anonymous';
      img.onload = () => {
        imageCache.current.base = img;
        drawCanvas();
      };
      img.src = currentPage.image_url;
    } else {
      drawCanvas();
    }
  }, [currentPage, drawCanvas]);

  // 加载patch图片
  useEffect(() => {
    layers.forEach((layer) => {
      if (layer.kind === 'patch' && !imageCache.current.patches.has(layer.id)) {
        const img = new Image();
        img.crossOrigin = 'anonymous';
        img.onload = () => {
          imageCache.current.patches.set(layer.id, img);
          drawCanvas();
        };
        img.onerror = () => {
          console.error('Failed to load patch image:', layer.image_url);
        };
        img.src = layer.image_url;
      }
    });
  }, [layers, drawCanvas]);

  // 绘制更新（不依赖图片加载）
  useEffect(() => {
    drawCanvas();
  }, [candidates, selectedCandidate, selectedLayer]);

  // 获取画布坐标
  const getCanvasCoords = (e: React.MouseEvent<HTMLCanvasElement>) => {
    if (!canvasRef.current || !currentPage) return { x: 0, y: 0 };

    const rect = canvasRef.current.getBoundingClientRect();
    const scaleX = currentPage.width / rect.width;
    const scaleY = currentPage.height / rect.height;

    return {
      x: (e.clientX - rect.left) * scaleX,
      y: (e.clientY - rect.top) * scaleY,
    };
  };

  // 检查点击是否在图层内
  const getLayerAtPoint = (x: number, y: number): Layer | null => {
    for (let i = layers.length - 1; i >= 0; i--) {
      const layer = layers[i];

      if (layer.kind === 'patch') {
        const bbox = layer.bbox;
        if (x >= bbox.x && x <= bbox.x + bbox.w && y >= bbox.y && y <= bbox.y + bbox.h) {
          return layer;
        }
      } else if (layer.kind === 'text') {
        const xs = layer.quad.map((p) => p[0]);
        const ys = layer.quad.map((p) => p[1]);
        const minX = Math.min(...xs);
        const maxX = Math.max(...xs);
        const minY = Math.min(...ys);
        const maxY = Math.max(...ys);

        if (x >= minX && x <= maxX && y >= minY && y <= maxY) {
          return layer;
        }
      }
    }
    return null;
  };

  // 鼠标按下事件
  const handleMouseDown = async (e: React.MouseEvent<HTMLCanvasElement>) => {
    const { x, y } = getCanvasCoords(e);

    const clickedLayer = getLayerAtPoint(x, y);

    if (clickedLayer) {
      setSelectedLayer(clickedLayer);
      setIsDragging(true);

      // 记录偏移
      if (clickedLayer.kind === 'patch') {
        dragRef.current.offset = {
          x: x - clickedLayer.bbox.x,
          y: y - clickedLayer.bbox.y,
        };
      } else if (clickedLayer.kind === 'text') {
        dragRef.current.offset = {
          x: x - clickedLayer.quad[0][0],
          y: y - clickedLayer.quad[0][1],
        };
      }
      dragRef.current.currentPos = { x, y };
      return;
    }

    // 点击候选框
    handleCandidateClick(x, y);
  };

  // 鼠标移动事件
  const handleMouseMove = (e: React.MouseEvent<HTMLCanvasElement>) => {
    if (!isDragging || !selectedLayer) return;

    const { x, y } = getCanvasCoords(e);
    dragRef.current.currentPos = { x, y };

    // 使用 RAF 优化重绘
    requestAnimationFrame(drawCanvas);
  };

  // 鼠标释放事件
  const handleMouseUp = () => {
    if (isDragging && selectedLayer && dragRef.current.currentPos) {
      const newX = dragRef.current.currentPos.x - dragRef.current.offset.x;
      const newY = dragRef.current.currentPos.y - dragRef.current.offset.y;

      if (selectedLayer.kind === 'patch') {
        updateLayer(selectedLayer.id, {
          bbox: {
            ...selectedLayer.bbox,
            x: newX,
            y: newY,
          },
        } as Partial<Layer>);
      } else if (selectedLayer.kind === 'text') {
        const deltaX = newX - selectedLayer.quad[0][0];
        const deltaY = newY - selectedLayer.quad[0][1];
        const newQuad: [number, number][] = selectedLayer.quad.map(
          ([px, py]) => [px + deltaX, py + deltaY]
        );
        updateLayer(selectedLayer.id, { quad: newQuad } as Partial<Layer>);
      }
    }

    setIsDragging(false);
    dragRef.current.currentPos = null;
  };

  // 处理点击选择候选框
  const handleCandidateClick = async (x: number, y: number) => {
    if (!currentPage) return;

    for (const candidate of candidates) {
      if (isPointInQuad(x, y, candidate.quad)) {
        setSelectedCandidate(candidate);

        try {
          setIsLoading(true);
          setLoadingMessage('生成 patch 中...');

          const [patchResponse, styleResponse] = await Promise.all([
            generatePatch(currentPage.page_id, { candidate_id: candidate.id }),
            estimateStyle(currentPage.page_id, candidate.id),
          ]);

          addPatch(patchResponse.patch);

          const patchLayer = {
            id: `patch_${patchResponse.patch.id}`,
            kind: 'patch' as const,
            bbox: patchResponse.patch.bbox,
            image_url: patchResponse.patch.image_url,
          };

          const textLayer = {
            id: `text_${candidate.id}`,
            kind: 'text' as const,
            text: candidate.text,
            quad: candidate.quad,
            style: styleResponse.style,
          };

          addLayer(patchLayer);
          addLayer(textLayer);

          // 自动选中新创建的文本图层
          setSelectedLayer(textLayer);

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
  const isPointInQuad = (x: number, y: number, quad: [number, number][]): boolean => {
    const bbox = {
      x: Math.min(...quad.map((p) => p[0])),
      y: Math.min(...quad.map((p) => p[1])),
      w: Math.max(...quad.map((p) => p[0])) - Math.min(...quad.map((p) => p[0])),
      h: Math.max(...quad.map((p) => p[1])) - Math.min(...quad.map((p) => p[1])),
    };

    return x >= bbox.x && x <= bbox.x + bbox.w && y >= bbox.y && y <= bbox.y + bbox.h;
  };

  if (!currentPage) {
    return null;
  }

  return (
    <div ref={containerRef} className="canvas-container">
      <canvas
        ref={canvasRef}
        className="editor-canvas"
        onMouseDown={handleMouseDown}
        onMouseMove={handleMouseMove}
        onMouseUp={handleMouseUp}
        onMouseLeave={handleMouseUp}
        style={{ cursor: isDragging ? 'grabbing' : 'default' }}
      />
    </div>
  );
}

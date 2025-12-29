/**
 * 图片上传组件
 * 支持拖拽上传和点击上传
 */

import { useState, useRef } from 'react';
import { uploadAsset, createPage, analyzePage } from '../services/api';
import { useEditorStore } from '../store/useEditorStore';

export function ImageUploader() {
  const [isDragging, setIsDragging] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const setCurrentPage = useEditorStore((state) => state.setCurrentPage);
  const setCandidates = useEditorStore((state) => state.setCandidates);
  const setIsLoading = useEditorStore((state) => state.setIsLoading);
  const setLoadingMessage = useEditorStore((state) => state.setLoadingMessage);

  const handleFile = async (file: File) => {
    if (!file.type.startsWith('image/')) {
      alert('请选择图片文件');
      return;
    }

    try {
      setIsLoading(true);
      setLoadingMessage('上传图片中...');

      // 1. 上传图片
      const asset = await uploadAsset(file);
      console.log('Asset uploaded:', asset);

      setLoadingMessage('创建页面中...');

      // 2. 创建 page
      const pageResponse = await createPage({
        image_url: asset.image_url,
        width: asset.width,
        height: asset.height,
      });
      console.log('Page created:', pageResponse);

      setLoadingMessage('OCR 识别中...');

      // 3. OCR 分析 (不指定 provider,使用后端配置的默认值)
      const analyzeResponse = await analyzePage(pageResponse.page_id);
      console.log('OCR completed:', analyzeResponse);

      // 4. 更新状态
      setCurrentPage({
        page_id: pageResponse.page_id,
        image_url: asset.image_url,
        width: asset.width,
        height: asset.height,
      });
      setCandidates(analyzeResponse.candidates);

      setLoadingMessage('完成!');
    } catch (error) {
      console.error('Upload failed:', error);
      alert('上传失败,请重试');
    } finally {
      setIsLoading(false);
      setLoadingMessage('');
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);

    const file = e.dataTransfer.files[0];
    if (file) {
      handleFile(file);
    }
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = () => {
    setIsDragging(false);
  };

  const handleClick = () => {
    fileInputRef.current?.click();
  };

  const handleFileInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      handleFile(file);
    }
  };

  return (
    <div
      className={`upload-area ${isDragging ? 'dragging' : ''}`}
      onDrop={handleDrop}
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onClick={handleClick}
    >
      <input
        ref={fileInputRef}
        type="file"
        accept="image/*"
        onChange={handleFileInputChange}
        style={{ display: 'none' }}
      />
      <div className="upload-content">
        <svg
          className="upload-icon"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
          xmlns="http://www.w3.org/2000/svg"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"
          />
        </svg>
        <p className="upload-text">点击或拖拽 PPT 截图到此处</p>
        <p className="upload-hint">支持 PNG, JPG, JPEG 格式</p>
      </div>
    </div>
  );
}

# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [Unreleased]

### Added
- Project switching functionality with dropdown menu to browse and load saved projects
- List projects API endpoint (`GET /v1/projects`)
- Loading state indicators for project operations
- Project list display with timestamps in Chinese locale format
- Current project highlighting in project switcher menu

### Changed
- Reorganized toolbar button layout: Save → Switch Project → Reset
- Removed PNG export functionality from frontend
- Added 🔄 icon to Reset button for better visual distinction

### Fixed
- Editor controls now properly sync with canvas changes (fixed Zustand state management)
- All text editor inputs (font size, color, content) now display correct current values

## [2024-12-30] - Phase 2: UI/UX Improvements & Bug Fixes

### Added
- Real-time text editing without "Apply Changes" button
- Extended font size range from 200px to 500px
- Project save/load functionality with database persistence
- PNG export with automatic download through backend proxy
- CORS-free file download using `/api/v1/assets/download` endpoint

### Changed
- Text editor now updates canvas immediately on any change
- Font size slider and number input work independently with proper synchronization
- Color picker updates in real-time
- Export function auto-saves project before rendering to ensure latest data

### Fixed
- **Critical**: Editor controls not updating issue - synchronized `selectedLayer` with `layers` array in Zustand store
- **Critical**: PNG export Docker networking issue - URL translation from `localhost:9000` to `minio:9000`
- **Critical**: Async event loop nesting error - converted `blend_patch_layer` to async function
- Font size number input losing focus bug
- Color picker not reflecting current text color
- Export using stale data - added auto-save before export
- Browser download dialog not appearing - implemented backend proxy with Blob URLs
- Exported image not matching canvas content

### Technical Debt Paid
- Proper async/await usage throughout export pipeline
- Removed `asyncio.run()` calls from running event loops
- Zustand shallow comparison properly handled with reference updates

## [2024-12-29] - Phase 1: Core Features & OCR Integration

### Added
- **OCR Integration**: Google Cloud Vision API support with automatic provider selection
- **Text Style Estimation**: Enhanced color estimation with multiple algorithms (kmeans, median, edge, mean)
- **Font Size Estimation**: Improved estimation with support for 12-500px range
- **Chinese Text Support**: Optimized DetectedBreak handling for Chinese characters
- Patch generation with transparent PNG output
- Background type analysis (solid/gradient/complex)
- Text layer rendering with PIL ImageDraw
- Projects CRUD API endpoints
- Frontend React + TypeScript + Vite application
- Canvas-based interactive editor
- Layer management panel
- Drag-to-reposition text functionality

### Changed
- OCR provider configurable via `OCR_PROVIDER` environment variable
- Color estimation method configurable via API parameter
- Font size now dynamically calculated based on bounding box dimensions
- DetectedBreak logic optimized for better Chinese text layout

### Fixed
- Docker network access for patch generation and style estimation
- MinIO connectivity from doc_process container
- OCR result parsing and normalization
- Background fitting for complex textures

## [2024-12-26] - Initial Release

### Added
- Monorepo structure with workspace configuration
- Docker Compose development environment
- FastAPI backend service with health check
- PostgreSQL database with SQLAlchemy models
- MinIO object storage integration
- Mock OCR provider for testing
- Asset upload endpoint (`POST /v1/assets/upload`)
- Page creation endpoint (`POST /v1/pages`)
- OCR analyze endpoint (`POST /v1/pages/{id}/analyze`)
- Patch generation endpoint (`POST /v1/pages/{id}/patch`)
- Style estimation endpoint (`POST /v1/pages/{id}/estimate-style`)

### Technical Stack
- **Backend**: Python 3.11, FastAPI, Uvicorn
- **Frontend**: React 18, TypeScript 5, Vite 5, Zustand 4
- **Database**: PostgreSQL 15 with SQLAlchemy 2
- **Storage**: MinIO (S3-compatible)
- **Image Processing**: OpenCV 4, Pillow 10, NumPy
- **OCR**: Azure Computer Vision, Google Cloud Vision (with Mock fallback)
- **Containerization**: Docker, Docker Compose

---

## Documentation Updates

### Phase 2 Documentation
- `selectedLayer同步修复说明.md` - Zustand state synchronization fix
- `TextEditor修复验证指南.md` - Text editor testing guide
- `导出PNG修复说明.md` - PNG export Docker networking fix
- `导出功能完整修复说明.md` - Complete export functionality fix

### Phase 1 Documentation
- `DetectedBreak优化说明.md` - Chinese text layout optimization
- `字体大小估算优化说明.md` - Font size estimation improvements
- `文字颜色估计优化说明.md` - Color estimation algorithm
- `实时编辑功能说明.md` - Real-time editing implementation
- `Docker网络访问修复说明.md` - Docker networking fixes
- `Patch生成修复说明.md` - Patch generation troubleshooting
- `Google-OCR-配置指南.md` - Google Cloud Vision setup
- `OCR-Provider-切换指南.md` - OCR provider switching

### Core Documentation
- `PRD-PPT截图文字可编辑化-MVP.md` - Product requirements
- `TechSpec-PPT截图文字可编辑化-MVP.md` - Technical specification
- `Codex执行计划与任务分解-PPT截图文字可编辑化-MVP.md` - Implementation plan
- `验收指引.md` - Acceptance testing guide
- `开发流程指南.md` - Development workflow guide

---

## Known Issues

None currently tracked.

## Future Enhancements

- [ ] Batch processing for multiple pages
- [ ] Advanced text formatting (bold, italic, underline)
- [ ] Custom font support
- [ ] Undo/redo functionality
- [ ] Keyboard shortcuts
- [ ] Text alignment controls
- [ ] Layer z-index management
- [ ] Export to multiple formats (PDF, SVG)
- [ ] Collaborative editing
- [ ] Version history for projects

---

## Migration Notes

### Breaking Changes
- None in current version

### API Changes
- Added `GET /v1/projects` endpoint for listing projects
- Export endpoint now requires project to be saved first

### Environment Variables
- `OCR_PROVIDER`: Set to `mock`, `azure`, or `google` (default: `mock`)
- `GOOGLE_CREDENTIALS_PATH`: Path to Google Cloud credentials JSON
- `AZURE_VISION_ENDPOINT`: Azure Computer Vision endpoint URL
- `AZURE_VISION_KEY`: Azure Computer Vision API key

---

## Contributors

- Development team working on PPT text editability tool

## Support

For issues and questions, please refer to:
- [README.md](README.md) - Quick start and setup
- [docs/验收指引.md](docs/验收指引.md) - Testing and validation
- [docs/开发流程指南.md](docs/开发流程指南.md) - Development workflow

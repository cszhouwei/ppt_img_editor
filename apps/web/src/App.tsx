import { ImageUploader } from './components/ImageUploader';
import { EditorCanvas } from './components/EditorCanvas';
import { Toolbar } from './components/Toolbar';
import { TextEditor } from './components/TextEditor';
import { LayerPanel } from './components/LayerPanel';
import { useEditorStore } from './store/useEditorStore';
import './App.css';

function App() {
  const currentPage = useEditorStore((state) => state.currentPage);
  const isLoading = useEditorStore((state) => state.isLoading);
  const loadingMessage = useEditorStore((state) => state.loadingMessage);

  return (
    <div className="app">
      {!currentPage ? (
        <>
          <header className="app-header">
            <h1>PPT 截图文字编辑器</h1>
          </header>
          <main className="app-main">
            <ImageUploader />
          </main>
        </>
      ) : (
        <>
          <Toolbar />
          <div className="editor-layout">
            <aside className="sidebar-left">
              <LayerPanel />
            </aside>
            <main className="editor-main">
              <EditorCanvas />
            </main>
            <aside className="sidebar-right">
              <TextEditor />
            </aside>
          </div>
        </>
      )}

      {isLoading && (
        <div className="loading-overlay">
          <div className="loading-spinner"></div>
          <p>{loadingMessage}</p>
        </div>
      )}
    </div>
  );
}

export default App;

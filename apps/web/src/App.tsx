import { ImageUploader } from './components/ImageUploader';
import { EditorCanvas } from './components/EditorCanvas';
import { useEditorStore } from './store/useEditorStore';
import './App.css';

function App() {
  const currentPage = useEditorStore((state) => state.currentPage);
  const isLoading = useEditorStore((state) => state.isLoading);
  const loadingMessage = useEditorStore((state) => state.loadingMessage);

  return (
    <div className="app">
      <header className="app-header">
        <h1>PPT 截图文字编辑器</h1>
      </header>

      <main className="app-main">
        {!currentPage ? (
          <ImageUploader />
        ) : (
          <EditorCanvas />
        )}
      </main>

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

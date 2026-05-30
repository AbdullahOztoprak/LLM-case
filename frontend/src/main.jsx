import React, { useEffect, useMemo, useState } from "react";
import { createRoot } from "react-dom/client";
import {
  Clock3,
  Database,
  FileText,
  Loader2,
  Search,
  Server,
  SlidersHorizontal
} from "lucide-react";
import "./styles.css";

const SOURCES = [
  { id: "github_docs", label: "GitHub" },
  { id: "fastapi_docs", label: "FastAPI" },
  { id: "python_docs", label: "Python" },
  { id: "docker_docs", label: "Docker" }
];

const RETRIEVAL_MODES = ["hybrid", "vector", "bm25"];

function formatScore(value) {
  if (typeof value !== "number") return "0.000";
  return value.toFixed(3);
}

function App() {
  const [question, setQuestion] = useState("How can I create a pull request from a fork?");
  const [selectedSources, setSelectedSources] = useState([]);
  const [topK, setTopK] = useState(5);
  const [retrievalMode, setRetrievalMode] = useState("hybrid");
  const [models, setModels] = useState([]);
  const [modelStatus, setModelStatus] = useState("Checking local models...");
  const [generationModel, setGenerationModel] = useState("");
  const [embeddingModel, setEmbeddingModel] = useState("");
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    async function loadModels() {
      try {
        const response = await fetch("/models");
        const payload = await response.json();
        const discovered = payload.available ? payload.models : payload.fallback_models;
        setModels(discovered || []);
        setModelStatus(payload.available ? "Ollama connected" : "Using fallback model names");
        const preferredGeneration =
          discovered?.find((model) => model.toLowerCase().includes("qwen")) ||
          discovered?.[0] ||
          "llama3.1";
        setGenerationModel(preferredGeneration);
        setEmbeddingModel(
          discovered?.find((model) => model.includes("embed")) || "nomic-embed-text"
        );
      } catch {
        setModels(["llama3.1", "nomic-embed-text"]);
        setGenerationModel("llama3.1");
        setEmbeddingModel("nomic-embed-text");
        setModelStatus("Backend not reachable");
      }
    }
    loadModels();
  }, []);

  const usedSources = useMemo(() => {
    if (!selectedSources.length) return "All documentation sources";
    return selectedSources
      .map((source) => SOURCES.find((item) => item.id === source)?.label || source)
      .join(", ");
  }, [selectedSources]);

  async function askQuestion(event) {
    event.preventDefault();
    setLoading(true);
    setError("");
    try {
      const response = await fetch("/ask", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          question,
          generation_model: generationModel,
          embedding_model: embeddingModel,
          top_k: topK,
          source_filter: selectedSources,
          retrieval_mode: retrievalMode
        })
      });
      if (!response.ok) {
        throw new Error(`Backend returned ${response.status}`);
      }
      setResult(await response.json());
    } catch (err) {
      setError(err.message || "Request failed.");
    } finally {
      setLoading(false);
    }
  }

  function toggleSource(sourceId) {
    setSelectedSources((current) =>
      current.includes(sourceId)
        ? current.filter((item) => item !== sourceId)
        : [...current, sourceId]
    );
  }

  const topChunks = result?.retrieved_chunks?.slice(0, 3) || [];

  return (
    <main className="shell">
      <header className="topbar">
        <div>
          <p className="eyebrow">Local docs retrieval</p>
          <h1>Docs RAG</h1>
          <p className="subtitle">Ask indexed developer docs and inspect the cited sources.</p>
        </div>
        <div className="status-pill">
          <Server size={16} />
          <span>{modelStatus}</span>
        </div>
      </header>

      <form className="layout" onSubmit={askQuestion}>
        <aside className="panel search-panel">
          <div className="panel-title">
            <Search size={17} />
            <h2>Search</h2>
          </div>

          <textarea
            aria-label="Question"
            value={question}
            onChange={(event) => setQuestion(event.target.value)}
            rows={5}
          />

          <div className="field-group">
            <div className="label-row">
              <Database size={15} />
              <span>Sources</span>
            </div>
            <div className="source-grid">
              {SOURCES.map((source) => (
                <button
                  type="button"
                  key={source.id}
                  className={selectedSources.includes(source.id) ? "chip active" : "chip"}
                  onClick={() => toggleSource(source.id)}
                >
                  {source.label}
                </button>
              ))}
            </div>
          </div>

          <div className="field-group">
            <div className="label-row">
              <SlidersHorizontal size={15} />
              <span>Retrieval</span>
            </div>
            <div className="segmented">
              {RETRIEVAL_MODES.map((mode) => (
                <button
                  type="button"
                  key={mode}
                  className={retrievalMode === mode ? "active" : ""}
                  onClick={() => setRetrievalMode(mode)}
                >
                  {mode}
                </button>
              ))}
            </div>
            <label className="range-label">
              <span>Top K</span>
              <strong>{topK}</strong>
            </label>
            <input
              type="range"
              min="1"
              max="10"
              value={topK}
              onChange={(event) => setTopK(Number(event.target.value))}
            />
          </div>

          <details className="settings-panel">
            <summary>Model settings</summary>
            <label>
              <span>Generation</span>
              <select
                value={generationModel}
                onChange={(event) => setGenerationModel(event.target.value)}
              >
                {models.map((model) => (
                  <option key={model} value={model}>
                    {model}
                  </option>
                ))}
              </select>
            </label>
            <label>
              <span>Embedding</span>
              <select
                value={embeddingModel}
                onChange={(event) => setEmbeddingModel(event.target.value)}
              >
                {models.map((model) => (
                  <option key={model} value={model}>
                    {model}
                  </option>
                ))}
                {!models.includes("nomic-embed-text") && (
                  <option value="nomic-embed-text">nomic-embed-text</option>
                )}
              </select>
            </label>
          </details>

          <button className="primary-action" type="submit" disabled={loading || !question.trim()}>
            {loading ? <Loader2 className="spin" size={18} /> : <Search size={18} />}
            Search docs
          </button>
        </aside>

        <section className="content-column">
          <div className="result-grid">
            <section className="panel answer-panel">
              <div className="answer-header">
                <div>
                  <p className="eyebrow">Answer</p>
                  <h2>{result ? "Response from retrieved context" : "Ready"}</h2>
                </div>
                <div className="metric-row">
                  <span>
                    <Clock3 size={14} />
                    {result ? `${result.latency_ms} ms` : "No query yet"}
                  </span>
                  <span>{result?.retrieval_mode || retrievalMode}</span>
                </div>
              </div>

              {error && <div className="error-box">{error}</div>}
              <article className="answer-box">
                {result ? result.answer : "Enter a question and run a search."}
              </article>

              <div className="run-summary">
                <div>
                  <span>Sources</span>
                  <strong>{usedSources}</strong>
                </div>
                <div>
                  <span>Generation model</span>
                  <strong>{result?.generation_model || generationModel || "Not selected"}</strong>
                </div>
                <div>
                  <span>Answer mode</span>
                  <strong>{result?.fallback_used ? "Retrieval preview" : "Model answer"}</strong>
                </div>
              </div>
            </section>

            <section className="panel sources-panel">
              <div className="panel-title">
                <FileText size={17} />
                <h2>Sources</h2>
              </div>
              <div className="source-list">
                {(result?.sources || []).slice(0, 4).map((source, index) => (
                  <article className="source-card" key={`${source.path}-${index}`}>
                    <div>
                      <span className="source-number">[{index + 1}]</span>
                      <strong>{source.title}</strong>
                      <p>{source.section}</p>
                      <code>{source.path}</code>
                    </div>
                    <span className="score">{source.score}</span>
                  </article>
                ))}
                {!result?.sources?.length && <p className="empty-state">No sources yet.</p>}
              </div>
            </section>
          </div>

          <section className="panel chunks-panel">
            <div className="panel-title">
              <SlidersHorizontal size={17} />
              <h2>Retrieval details</h2>
            </div>
            <div className="chunk-list">
              {topChunks.map((chunk) => (
                <article className="chunk-row" key={chunk.id}>
                  <div>
                    <strong>{chunk.metadata.title}</strong>
                    <p>{chunk.metadata.source} / {chunk.metadata.section}</p>
                  </div>
                  <div className="score-row">
                    <span>Combined {formatScore(chunk.combined_score ?? chunk.score)}</span>
                    <span>Vector {formatScore(chunk.vector_score)}</span>
                    <span>BM25 {formatScore(chunk.bm25_score ?? chunk.keyword_score)}</span>
                  </div>
                </article>
              ))}
              {!topChunks.length && <p className="empty-state">No retrieved chunks yet.</p>}
            </div>
          </section>
        </section>
      </form>
    </main>
  );
}

createRoot(document.getElementById("root")).render(<App />);

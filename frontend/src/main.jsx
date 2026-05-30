import React, { useEffect, useMemo, useState } from "react";
import { createRoot } from "react-dom/client";
import {
  Braces,
  Clock3,
  Database,
  FileText,
  Gauge,
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
  const [modelStatus, setModelStatus] = useState("Checking Ollama models...");
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
        setModelStatus(payload.message);
        const preferredGeneration =
          discovered?.find((model) => model.toLowerCase().includes("qwen")) ||
          discovered?.[0] ||
          "llama3.1";
        setGenerationModel(preferredGeneration);
        const embed =
          discovered?.find((model) => model.includes("embed")) || "nomic-embed-text";
        setEmbeddingModel(embed);
      } catch {
        setModels(["llama3.1", "nomic-embed-text"]);
        setGenerationModel("llama3.1");
        setEmbeddingModel("nomic-embed-text");
        setModelStatus("Backend is not reachable yet.");
      }
    }
    loadModels();
  }, []);

  const usedSources = useMemo(() => {
    if (!selectedSources.length) return "All sources";
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

  return (
    <main className="shell">
      <header className="topbar">
        <div>
          <p className="eyebrow">Local documentation retrieval</p>
          <h1>Docs RAG</h1>
        </div>
        <div className="status-pill">
          <Server size={16} />
          <span>{modelStatus}</span>
        </div>
      </header>

      <form className="workspace" onSubmit={askQuestion}>
        <aside className="panel controls">
          <section>
            <div className="section-title">
              <Search size={16} />
              <span>Query</span>
            </div>
            <textarea
              value={question}
              onChange={(event) => setQuestion(event.target.value)}
              rows={7}
            />
          </section>

          <section>
            <div className="section-title">
              <Database size={16} />
              <span>Source filter</span>
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
          </section>

          <section className="stack">
            <label>
              <span>Generation model</span>
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
              <span>Embedding model</span>
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
          </section>

          <section>
            <div className="section-title">
              <SlidersHorizontal size={16} />
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
          </section>

          <button className="primary-action" type="submit" disabled={loading || !question.trim()}>
            {loading ? <Loader2 className="spin" size={18} /> : <Search size={18} />}
            Search docs
          </button>
        </aside>

        <section className="panel answer-panel">
          <div className="panel-heading">
            <div>
              <p className="eyebrow">Result</p>
              <h2>Answer</h2>
            </div>
            <div className="meta-row">
              <span>
                <Clock3 size={14} />
                {result ? `${result.latency_ms} ms` : "Waiting"}
              </span>
              <span>
                <Gauge size={14} />
                {retrievalMode}
              </span>
            </div>
          </div>

          {error && <div className="error-box">{error}</div>}
          <article className="answer-box">
            {result ? result.answer : "Enter a documentation question to see the answer and sources."}
          </article>

          <div className="metadata-grid">
            <div>
              <span>Generation</span>
              <strong>{result?.generation_model || generationModel || "Not selected"}</strong>
            </div>
            <div>
              <span>Embedding</span>
              <strong>{result?.embedding_model || embeddingModel || "Not selected"}</strong>
            </div>
            <div>
              <span>Sources</span>
              <strong>{usedSources}</strong>
            </div>
            <div>
              <span>Mode</span>
              <strong>{result?.fallback_used ? "Retrieval preview" : "Model answer"}</strong>
            </div>
          </div>
        </section>

        <aside className="panel evidence-panel">
          <div className="panel-heading compact">
            <div>
              <p className="eyebrow">References</p>
              <h2>Sources</h2>
            </div>
          </div>

          <div className="source-list">
            {(result?.sources || []).map((source, index) => (
              <article className="source-card" key={`${source.path}-${index}`}>
                <div className="source-card-title">
                  <span>[{index + 1}]</span>
                  <strong>{source.title}</strong>
                </div>
                <p>{source.section}</p>
                <code>{source.path}</code>
                <footer>
                  <span>{source.source}</span>
                  <span>{source.score}</span>
                </footer>
              </article>
            ))}
            {!result?.sources?.length && (
              <p className="empty-state">No sources yet.</p>
            )}
          </div>
        </aside>
      </form>

      <section className="panel chunks-panel">
        <div className="panel-heading compact">
          <div>
            <p className="eyebrow">Retrieval details</p>
            <h2>Retrieved chunks</h2>
          </div>
          <Braces size={18} />
        </div>
        <div className="chunk-grid">
          {(result?.retrieved_chunks || []).map((chunk) => (
            <article className="chunk-card" key={chunk.id}>
              <header>
                <FileText size={16} />
                <strong>{chunk.metadata.title}</strong>
              </header>
              <p>{chunk.text}</p>
              <div className="score-row">
                <span>Combined {formatScore(chunk.combined_score ?? chunk.score)}</span>
                <span>Vector {formatScore(chunk.vector_score)}</span>
                <span>BM25 {formatScore(chunk.bm25_score ?? chunk.keyword_score)}</span>
              </div>
              <code>
                {chunk.metadata.source} / {chunk.metadata.section}
              </code>
            </article>
          ))}
          {!result?.retrieved_chunks?.length && (
            <p className="empty-state">No retrieved chunks yet.</p>
          )}
        </div>
      </section>
    </main>
  );
}

createRoot(document.getElementById("root")).render(<App />);

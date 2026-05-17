'use client';

import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import dynamic from 'next/dynamic';
import type { GraphData, GraphNode, GraphEdge } from '@/types/api';

// SSR-safe: canvas APIs aren't available server-side
const ForceGraph2D = dynamic(() => import('react-force-graph-2d'), { ssr: false });

// ─── Domain colour helpers ──────────────────────────────────────────────────

function domainColor(domainId: string, allDomainIds: string[]): string {
  const idx = allDomainIds.indexOf(domainId);
  const hue = (270 + idx * 30) % 360;
  return `hsl(${hue}, 60%, 55%)`;
}

// ─── Node radius by degree ──────────────────────────────────────────────────

function nodeRadius(degree: number, maxDegree: number): number {
  if (maxDegree === 0) return 5;
  const t = Math.sqrt(degree / maxDegree);
  return 3 + t * 11;
}

// ─── Internal node shape (extends GraphNode with pre-computed display props) ─

interface RichNode extends GraphNode {
  x?: number;
  y?: number;
  __color: string;
  __radius: number;
}

// ─── Side panel ─────────────────────────────────────────────────────────────

interface SidePanelProps {
  node: RichNode;
  allNodes: RichNode[];
  allEdges: GraphEdge[];
  domainIds: string[];
  onClose: () => void;
  onNavigate: (nodeId: string) => void;
}

function SidePanel({ node, allNodes, allEdges, domainIds, onClose, onNavigate }: SidePanelProps) {
  const neighborIds = useMemo(() => {
    const ids = new Set<string>();
    for (const e of allEdges) {
      if (e.source === node.id) ids.add(e.target);
      if (e.target === node.id) ids.add(e.source);
    }
    return ids;
  }, [node.id, allEdges]);

  const neighbors = allNodes.filter((n) => neighborIds.has(n.id));

  return (
    <div
      style={{
        position: 'absolute',
        top: 0,
        right: 0,
        width: '400px',
        height: '100%',
        backgroundColor: 'var(--surface)',
        borderLeft: '1px solid var(--border)',
        display: 'flex',
        flexDirection: 'column',
        zIndex: 20,
        animation: 'slide-in-right 220ms ease-out',
        overflow: 'hidden',
      }}
    >
      <div
        style={{
          padding: '1.25rem 1.25rem 1rem',
          borderBottom: '1px solid var(--border)',
          display: 'flex',
          alignItems: 'flex-start',
          justifyContent: 'space-between',
          gap: '0.75rem',
          flexShrink: 0,
        }}
      >
        <div style={{ minWidth: 0 }}>
          <h2
            style={{
              fontFamily: "'Instrument Serif', Georgia, serif",
              fontSize: '1.375rem',
              fontWeight: 400,
              color: 'var(--text)',
              margin: '0 0 0.25rem',
              lineHeight: 1.2,
              wordBreak: 'break-word',
            }}
          >
            {node.label}
          </h2>
          <span
            style={{
              display: 'inline-block',
              fontFamily: 'var(--font-mono)',
              fontSize: '0.6875rem',
              color: 'var(--text-dim)',
              backgroundColor: 'var(--surface-elevated)',
              border: '1px solid var(--border)',
              borderRadius: '4px',
              padding: '0.15em 0.5em',
            }}
          >
            {node.domain}
          </span>
        </div>
        <button
          onClick={onClose}
          style={{
            background: 'none',
            border: 'none',
            cursor: 'pointer',
            color: 'var(--text-dim)',
            fontSize: '1.125rem',
            lineHeight: 1,
            padding: '0.125rem',
            flexShrink: 0,
          }}
          aria-label="Close"
        >
          ✕
        </button>
      </div>

      <div style={{ flex: 1, overflowY: 'auto', padding: '1rem 1.25rem' }}>
        <div style={{ marginBottom: '1rem' }}>
          <div style={labelStyle}>File</div>
          <code style={{ fontFamily: 'var(--font-mono)', fontSize: '0.8125rem', color: 'var(--text-muted)', wordBreak: 'break-all' }}>
            {node.file}
          </code>
        </div>

        <div style={{ marginBottom: '1rem' }}>
          <div style={labelStyle}>Signature</div>
          <pre
            style={{
              margin: 0,
              padding: '0.625rem 0.75rem',
              backgroundColor: 'var(--surface-elevated)',
              border: '1px solid var(--border)',
              borderRadius: '6px',
              fontFamily: 'var(--font-mono)',
              fontSize: '0.75rem',
              color: 'var(--accent)',
              overflowX: 'auto',
              lineHeight: 1.5,
              whiteSpace: 'pre-wrap',
              wordBreak: 'break-word',
            }}
          >
            {node.signature}
          </pre>
        </div>

        <div style={{ marginBottom: '1.25rem' }}>
          <div style={labelStyle}>Domain</div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <span style={{ width: '10px', height: '10px', borderRadius: '50%', backgroundColor: domainColor(node.domainId, domainIds), flexShrink: 0 }} />
            <span style={{ fontFamily: 'var(--font-sans)', fontSize: '0.875rem', color: 'var(--text-muted)' }}>{node.domain}</span>
          </div>
        </div>

        <div style={{ marginBottom: '1.25rem' }}>
          <div style={labelStyle}>Connections</div>
          <span style={{ fontFamily: 'var(--font-mono)', fontSize: '0.875rem', color: 'var(--text-muted)' }}>{node.degree}</span>
        </div>

        {neighbors.length > 0 && (
          <div>
            <div style={labelStyle}>Neighbors ({neighbors.length})</div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.25rem' }}>
              {neighbors.slice(0, 20).map((n) => (
                <button
                  key={n.id}
                  onClick={() => onNavigate(n.id)}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '0.5rem',
                    padding: '0.375rem 0.5rem',
                    backgroundColor: 'transparent',
                    border: '1px solid var(--border)',
                    borderRadius: '5px',
                    cursor: 'pointer',
                    textAlign: 'left',
                  }}
                >
                  <span style={{ width: '7px', height: '7px', borderRadius: '50%', backgroundColor: domainColor(n.domainId, domainIds), flexShrink: 0 }} />
                  <span style={{ fontFamily: 'var(--font-mono)', fontSize: '0.75rem', color: 'var(--text-muted)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                    {n.label}
                  </span>
                  <span style={{ fontFamily: 'var(--font-sans)', fontSize: '0.6875rem', color: 'var(--text-dim)', marginLeft: 'auto', flexShrink: 0 }}>
                    {n.domain}
                  </span>
                </button>
              ))}
              {neighbors.length > 20 && (
                <span style={{ fontFamily: 'var(--font-sans)', fontSize: '0.75rem', color: 'var(--text-dim)', padding: '0.25rem 0.5rem' }}>
                  +{neighbors.length - 20} more
                </span>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

const labelStyle: React.CSSProperties = {
  fontFamily: 'var(--font-sans)',
  fontSize: '0.6875rem',
  color: 'var(--text-dim)',
  textTransform: 'uppercase',
  letterSpacing: '0.08em',
  marginBottom: '0.25rem',
};

// ─── Controls ────────────────────────────────────────────────────────────────

interface ControlsProps {
  repos: { id: string; name: string }[];
  selectedRepo: string;
  onRepoChange: (id: string) => void;
  domainIds: string[];
  domainNames: Record<string, string>;
  hiddenDomains: Set<string>;
  onToggleDomain: (id: string) => void;
  onResetView: () => void;
}

function Controls({ repos, selectedRepo, onRepoChange, domainIds, domainNames, hiddenDomains, onToggleDomain, onResetView }: ControlsProps) {
  return (
    <div
      style={{
        position: 'absolute',
        top: '1rem',
        left: '1rem',
        zIndex: 10,
        backgroundColor: 'rgba(20, 20, 20, 0.92)',
        border: '1px solid var(--border)',
        borderRadius: '8px',
        padding: '0.875rem',
        width: '220px',
        backdropFilter: 'blur(8px)',
        display: 'flex',
        flexDirection: 'column',
        gap: '0.875rem',
      }}
    >
      <div>
        <div style={labelStyle}>Repository</div>
        <select
          value={selectedRepo}
          onChange={(e) => onRepoChange(e.target.value)}
          style={{
            width: '100%',
            fontFamily: 'var(--font-mono)',
            fontSize: '0.75rem',
            color: 'var(--text-muted)',
            backgroundColor: 'var(--surface-elevated)',
            border: '1px solid var(--border)',
            borderRadius: '5px',
            padding: '0.375rem 0.5rem',
            outline: 'none',
            cursor: 'pointer',
          }}
        >
          <option value="">All repositories</option>
          {repos.map((r) => (
            <option key={r.id} value={r.id}>{r.name}</option>
          ))}
        </select>
      </div>

      <div>
        <div style={labelStyle}>Domains</div>
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.3rem' }}>
          {domainIds.map((id) => {
            const hidden = hiddenDomains.has(id);
            const color = domainColor(id, domainIds);
            return (
              <button
                key={id}
                onClick={() => onToggleDomain(id)}
                title={domainNames[id]}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.3rem',
                  padding: '0.2rem 0.45rem',
                  borderRadius: '4px',
                  border: `1px solid ${hidden ? 'var(--border)' : color}`,
                  backgroundColor: hidden ? 'transparent' : `${color}22`,
                  cursor: 'pointer',
                  opacity: hidden ? 0.45 : 1,
                  transition: 'opacity 150ms',
                }}
              >
                <span style={{ width: '7px', height: '7px', borderRadius: '50%', backgroundColor: color, flexShrink: 0 }} />
                <span style={{ fontFamily: 'var(--font-sans)', fontSize: '0.6rem', color: 'var(--text-dim)', maxWidth: '100px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                  {domainNames[id]}
                </span>
              </button>
            );
          })}
        </div>
      </div>

      <button
        onClick={onResetView}
        style={{
          fontFamily: 'var(--font-sans)',
          fontSize: '0.75rem',
          color: 'var(--text-muted)',
          backgroundColor: 'var(--surface-elevated)',
          border: '1px solid var(--border)',
          borderRadius: '5px',
          padding: '0.375rem 0.625rem',
          cursor: 'pointer',
          textAlign: 'center',
        }}
      >
        Reset view
      </button>
    </div>
  );
}

// ─── Main component ──────────────────────────────────────────────────────────

interface DomainGraphProps {
  data: GraphData;
  repos: { id: string; name: string }[];
  selectedRepo: string;
  onRepoChange: (id: string) => void;
}

export function DomainGraph({ data, repos, selectedRepo, onRepoChange }: DomainGraphProps) {
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const fgRef = useRef<any>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const [dimensions, setDimensions] = useState({ width: 800, height: 600 });
  const [hoveredId, setHoveredId] = useState<string | null>(null);
  const [selectedNode, setSelectedNode] = useState<RichNode | null>(null);
  const [hiddenDomains, setHiddenDomains] = useState<Set<string>>(new Set());
  const [canvasVisible, setCanvasVisible] = useState(false);

  useEffect(() => {
    const el = containerRef.current;
    if (!el) return;
    const obs = new ResizeObserver(([entry]) => {
      const r = entry?.contentRect;
      if (r) setDimensions({ width: r.width, height: r.height });
    });
    obs.observe(el);
    setDimensions({ width: el.clientWidth, height: el.clientHeight });
    return () => obs.disconnect();
  }, []);

  const domainIds = useMemo(
    () => [...new Set(data.nodes.map((n) => n.domainId))].sort(),
    [data.nodes],
  );

  const domainNames = useMemo(() => {
    const map: Record<string, string> = {};
    for (const n of data.nodes) map[n.domainId] = n.domain;
    return map;
  }, [data.nodes]);

  const maxDegree = useMemo(
    () => Math.max(1, ...data.nodes.map((n) => n.degree)),
    [data.nodes],
  );

  const richNodes = useMemo<RichNode[]>(
    () =>
      data.nodes.map((n) => ({
        ...n,
        __color: domainColor(n.domainId, domainIds),
        __radius: nodeRadius(n.degree, maxDegree),
      })),
    [data.nodes, domainIds, maxDegree],
  );

  const neighborSet = useMemo(() => {
    if (!hoveredId) return new Set<string>();
    const s = new Set<string>();
    for (const e of data.edges) {
      if (e.source === hoveredId) s.add(e.target);
      if (e.target === hoveredId) s.add(e.source);
    }
    return s;
  }, [hoveredId, data.edges]);

  // react-force-graph-2d expects { nodes, links }
  const fgData = useMemo(
    () => ({
      nodes: richNodes,
      links: data.edges,
    }),
    [richNodes, data.edges],
  );

  const nodeCanvasObject = useCallback(
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    (rawNode: any, ctx: CanvasRenderingContext2D) => {
      const n = rawNode as RichNode;
      const x: number = n.x ?? 0;
      const y: number = n.y ?? 0;
      const hidden = hiddenDomains.has(n.domainId);

      let alpha = 1;
      if (hidden) alpha = 0.05;
      else if (hoveredId) {
        if (n.id === hoveredId) alpha = 1;
        else if (neighborSet.has(n.id)) alpha = 0.85;
        else alpha = 0.12;
      }

      const r = n.__radius;

      // Glow ring on hovered node
      if (n.id === hoveredId && !hidden) {
        const grd = ctx.createRadialGradient(x, y, r, x, y, r + 5);
        grd.addColorStop(0, `${n.__color}55`);
        grd.addColorStop(1, `${n.__color}00`);
        ctx.beginPath();
        ctx.arc(x, y, r + 5, 0, 2 * Math.PI);
        ctx.fillStyle = grd;
        ctx.fill();
      }

      ctx.globalAlpha = alpha;
      ctx.beginPath();
      ctx.arc(x, y, r, 0, 2 * Math.PI);
      ctx.fillStyle = n.__color;
      ctx.fill();
      ctx.globalAlpha = 1;

      // Label on hover
      if (!hidden && hoveredId && (n.id === hoveredId || neighborSet.has(n.id))) {
        const fontSize = Math.max(8, r * 0.9);
        ctx.font = `${fontSize}px monospace`;
        ctx.textAlign = 'center';
        ctx.textBaseline = 'top';
        ctx.fillStyle = 'rgba(245,245,245,0.85)';
        ctx.globalAlpha = alpha;
        ctx.fillText(n.label.slice(0, 22), x, y + r + 3);
        ctx.globalAlpha = 1;
      }
    },
    [hoveredId, neighborSet, hiddenDomains],
  );

  const nodePointerAreaPaint = useCallback(
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    (rawNode: any, color: string, ctx: CanvasRenderingContext2D) => {
      const n = rawNode as RichNode;
      ctx.fillStyle = color;
      ctx.beginPath();
      ctx.arc(n.x ?? 0, n.y ?? 0, n.__radius + 2, 0, 2 * Math.PI);
      ctx.fill();
    },
    [],
  );

  const linkColor = useCallback(
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    (link: any): string => {
      const srcId = typeof link.source === 'object' ? link.source?.id : link.source;
      const tgtId = typeof link.target === 'object' ? link.target?.id : link.target;
      if (!hoveredId) return 'rgba(255,255,255,0.12)';
      if (srcId === hoveredId || tgtId === hoveredId) return 'rgba(139,92,246,0.65)';
      return 'rgba(255,255,255,0.04)';
    },
    [hoveredId],
  );

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const handleNodeHover = useCallback((node: any) => {
    setHoveredId(node ? (node as RichNode).id : null);
  }, []);

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const handleNodeClick = useCallback((node: any) => {
    setSelectedNode(node as RichNode);
  }, []);

  const handleNavigate = useCallback(
    (nodeId: string) => {
      const n = richNodes.find((nd) => nd.id === nodeId);
      if (!n) return;
      setSelectedNode(n);
      fgRef.current?.centerAt(n.x ?? 0, n.y ?? 0, 600);
      fgRef.current?.zoom(2.5, 600);
    },
    [richNodes],
  );

  const handleResetView = useCallback(() => {
    fgRef.current?.zoomToFit(400, 60);
  }, []);

  const toggleDomain = useCallback((id: string) => {
    setHiddenDomains((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  }, []);

  const handleEngineStop = useCallback(() => {
    setCanvasVisible(true);
    setTimeout(() => fgRef.current?.zoomToFit(400, 80), 50);
  }, []);

  return (
    <div
      ref={containerRef}
      style={{ position: 'relative', width: '100%', height: '100%', overflow: 'hidden' }}
    >
      {/* Grain overlay */}
      <div
        aria-hidden="true"
        style={{
          position: 'absolute',
          inset: 0,
          zIndex: 1,
          pointerEvents: 'none',
          opacity: 0.04,
          backgroundImage: `url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='200' height='200'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.85' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='200' height='200' filter='url(%23n)'/%3E%3C/svg%3E")`,
          backgroundRepeat: 'repeat',
        }}
      />

      {/* Canvas fade-in wrapper */}
      <div
        style={{
          opacity: canvasVisible ? 1 : 0,
          transition: 'opacity 400ms ease-in',
          position: 'absolute',
          inset: 0,
        }}
      >
        <ForceGraph2D
          ref={fgRef}
          graphData={fgData}
          width={dimensions.width}
          height={dimensions.height}
          backgroundColor="#0a0a0a"
          nodeId="id"
          nodeCanvasObject={nodeCanvasObject}
          nodeCanvasObjectMode={() => 'replace'}
          nodePointerAreaPaint={nodePointerAreaPaint}
          linkColor={linkColor}
          linkWidth={1}
          linkDirectionalArrowLength={0}
          warmupTicks={300}
          cooldownTicks={0}
          onEngineStop={handleEngineStop}
          onNodeHover={handleNodeHover}
          onNodeClick={handleNodeClick}
          enableNodeDrag
          enableZoomInteraction
          enablePanInteraction
        />
      </div>

      <Controls
        repos={repos}
        selectedRepo={selectedRepo}
        onRepoChange={onRepoChange}
        domainIds={domainIds}
        domainNames={domainNames}
        hiddenDomains={hiddenDomains}
        onToggleDomain={toggleDomain}
        onResetView={handleResetView}
      />

      {selectedNode && (
        <>
          <div
            style={{ position: 'absolute', inset: 0, zIndex: 19 }}
            onClick={() => setSelectedNode(null)}
          />
          <SidePanel
            node={selectedNode}
            allNodes={richNodes}
            allEdges={data.edges}
            domainIds={domainIds}
            onClose={() => setSelectedNode(null)}
            onNavigate={handleNavigate}
          />
        </>
      )}
    </div>
  );
}

"use client";

import { useEffect, useState } from "react";
import {
  Filter,
  Layers,
  Network,
  RefreshCw,
  Share2,
  ZoomIn,
  ZoomOut,
} from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";

interface GraphNode {
  id: string;
  label: string;
  group: string;
  size: number;
}

interface GraphLink {
  source: string;
  target: string;
  relationship: string;
  weight: number;
}

interface KnowledgeGraphData {
  nodes: GraphNode[];
  links: GraphLink[];
  summary: Record<string, any>;
}

interface DocumentItem {
  id: number;
  filename: string;
}

const GROUP_COLORS: Record<string, string> = {
  DOCUMENT: "#6366f1",
  SKILL: "#10b981",
  CONCEPT: "#f59e0b",
  ORGANIZATION: "#a855f7",
  PERSON: "#f43f5e",
  TOOL: "#06b6d4",
  OTHER: "#94a3b8",
};

export function KnowledgeGraphVisualizer({
  apiBaseUrl,
  documents,
  initialDocId,
}: {
  apiBaseUrl: string;
  documents: DocumentItem[];
  initialDocId?: number | null;
}) {
  const [selectedDocId, setSelectedDocId] = useState<number | null>(
    initialDocId || (documents[0]?.id ?? null)
  );
  const [viewMode, setViewMode] = useState<"document" | "workspace">("workspace");
  const [graphData, setGraphData] = useState<KnowledgeGraphData | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [selectedGroup, setSelectedGroup] = useState<string>("ALL");
  const [hoveredNode, setHoveredNode] = useState<GraphNode | null>(null);
  const [zoomLevel, setZoomLevel] = useState<number>(1);

  const fetchGraph = async () => {
    setIsLoading(true);
    try {
      const endpoint =
        viewMode === "workspace"
          ? `${apiBaseUrl}/api/entities/workspace-graph`
          : `${apiBaseUrl}/api/entities/graph/${selectedDocId}`;
      const res = await fetch(endpoint, { credentials: "include" });
      if (res.ok) {
        const data = await res.json();
        setGraphData(data);
      }
    } catch (err) {
      console.error("Failed to load graph:", err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchGraph();
  }, [viewMode, selectedDocId, apiBaseUrl]);

  const rawNodes = graphData?.nodes || [];
  const rawLinks = graphData?.links || [];

  const visibleNodes =
    selectedGroup === "ALL"
      ? rawNodes
      : rawNodes.filter((n) => n.group === selectedGroup || n.group === "DOCUMENT");

  const visibleNodeIds = new Set(visibleNodes.map((n) => n.id));
  const visibleLinks = rawLinks.filter(
    (l) => visibleNodeIds.has(l.source) && visibleNodeIds.has(l.target)
  );

  const width = 800;
  const height = 520;
  const cx = width / 2;
  const cy = height / 2;

  const nodePositions: Record<string, { x: number; y: number }> = {};
  const docNodes = visibleNodes.filter((n) => n.group === "DOCUMENT");
  const nonDocNodes = visibleNodes.filter((n) => n.group !== "DOCUMENT");

  if (docNodes.length === 1) {
    nodePositions[docNodes[0].id] = { x: cx, y: cy };
  } else {
    docNodes.forEach((dn, i) => {
      const angle = (i / Math.max(docNodes.length, 1)) * 2 * Math.PI;
      const r = 90;
      nodePositions[dn.id] = {
        x: cx + r * Math.cos(angle),
        y: cy + r * Math.sin(angle),
      };
    });
  }

  nonDocNodes.forEach((node, idx) => {
    const angle = (idx / Math.max(nonDocNodes.length, 1)) * 2 * Math.PI;
    const radius = 170 + ((idx % 3) * 28);
    nodePositions[node.id] = {
      x: cx + radius * Math.cos(angle),
      y: cy + radius * Math.sin(angle),
    };
  });

  const availableGroups = Array.from(new Set(rawNodes.map((n) => n.group)));

  return (
    <div className="space-y-6">
      <Card className="border-border/80 bg-card/60">
        <CardHeader className="pb-3">
          <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
            <div>
              <CardTitle className="text-xl flex items-center gap-2">
                <Network className="h-5 w-5 text-primary" />
                <span>Entity &amp; Knowledge Graph Visualizer</span>
              </CardTitle>
              <CardDescription className="text-xs">
                Explore named entities, technologies, concepts, and relationships across your documents
              </CardDescription>
            </div>

            <div className="flex items-center gap-2">
              <div className="grid grid-cols-2 rounded-lg border border-border p-1 bg-muted/40 text-xs">
                <button
                  type="button"
                  onClick={() => setViewMode("workspace")}
                  className={`px-3 py-1 rounded font-medium transition-colors ${
                    viewMode === "workspace"
                      ? "bg-card text-foreground shadow-sm"
                      : "text-muted-foreground hover:text-foreground"
                  }`}
                >
                  Workspace Graph
                </button>
                <button
                  type="button"
                  onClick={() => setViewMode("document")}
                  className={`px-3 py-1 rounded font-medium transition-colors ${
                    viewMode === "document"
                      ? "bg-card text-foreground shadow-sm"
                      : "text-muted-foreground hover:text-foreground"
                  }`}
                >
                  Single Document
                </button>
              </div>

              {viewMode === "document" && (
                <select
                  value={selectedDocId || ""}
                  onChange={(e) => setSelectedDocId(Number(e.target.value))}
                  className="text-xs rounded-lg border border-border bg-background px-2.5 py-1.5 text-foreground focus:outline-none"
                >
                  {documents.map((d) => (
                    <option key={d.id} value={d.id}>
                      {d.filename}
                    </option>
                  ))}
                </select>
              )}

              <Button
                variant="outline"
                size="sm"
                onClick={fetchGraph}
                disabled={isLoading}
                className="h-8 px-2.5 gap-1.5 text-xs"
              >
                <RefreshCw className={`h-3.5 w-3.5 ${isLoading ? "animate-spin" : ""}`} />
              </Button>
            </div>
          </div>
        </CardHeader>

        <CardContent className="space-y-4">
          <div className="flex flex-wrap items-center justify-between gap-3 text-xs border-b border-border/40 pb-3">
            <div className="flex flex-wrap items-center gap-1.5">
              <span className="text-muted-foreground flex items-center gap-1 mr-1">
                <Filter className="h-3 w-3" /> Filter by Type:
              </span>
              <button
                type="button"
                onClick={() => setSelectedGroup("ALL")}
                className={`px-2.5 py-1 rounded-md text-[11px] font-medium transition-colors ${
                  selectedGroup === "ALL"
                    ? "bg-primary text-white"
                    : "bg-muted text-muted-foreground hover:text-foreground"
                }`}
              >
                All ({rawNodes.length})
              </button>
              {availableGroups.map((grp) => (
                <button
                  key={grp}
                  type="button"
                  onClick={() => setSelectedGroup(grp)}
                  className={`px-2.5 py-1 rounded-md text-[11px] font-medium transition-colors flex items-center gap-1.5 ${
                    selectedGroup === grp
                      ? "bg-foreground text-background"
                      : "bg-muted text-muted-foreground hover:text-foreground"
                  }`}
                >
                  <span
                    className="h-2 w-2 rounded-full"
                    style={{ backgroundColor: GROUP_COLORS[grp] || GROUP_COLORS.OTHER }}
                  />
                  <span>{grp}</span>
                </button>
              ))}
            </div>

            <div className="flex items-center gap-1 font-mono text-[11px] text-muted-foreground">
              <span>Zoom:</span>
              <button
                type="button"
                onClick={() => setZoomLevel((z) => Math.max(0.6, z - 0.15))}
                className="p-1 rounded hover:bg-muted"
                title="Zoom Out"
              >
                <ZoomOut className="h-3.5 w-3.5" />
              </button>
              <span>{Math.round(zoomLevel * 100)}%</span>
              <button
                type="button"
                onClick={() => setZoomLevel((z) => Math.min(1.8, z + 0.15))}
                className="p-1 rounded hover:bg-muted"
                title="Zoom In"
              >
                <ZoomIn className="h-3.5 w-3.5" />
              </button>
            </div>
          </div>

          <div className="relative overflow-hidden rounded-xl border border-border/80 bg-background/95 h-[520px]">
            {isLoading && (
              <div className="absolute inset-0 flex items-center justify-center bg-background/60 backdrop-blur-sm z-20">
                <div className="flex items-center gap-2 text-xs text-muted-foreground">
                  <RefreshCw className="h-4 w-4 animate-spin text-primary" />
                  <span>Generating Knowledge Graph...</span>
                </div>
              </div>
            )}

            <svg
              viewBox={`0 0 ${width} ${height}`}
              className="h-full w-full select-none cursor-grab active:cursor-grabbing"
              style={{ transform: `scale(${zoomLevel})`, transformOrigin: "center center", transition: "transform 0.15s ease" }}
            >
              {visibleLinks.map((link, idx) => {
                const s = nodePositions[link.source];
                const t = nodePositions[link.target];
                if (!s || !t) return null;
                const isHovered =
                  hoveredNode && (hoveredNode.id === link.source || hoveredNode.id === link.target);
                return (
                  <line
                    key={idx}
                    x1={s.x}
                    y1={s.y}
                    x2={t.x}
                    y2={t.y}
                    stroke={isHovered ? "#6366f1" : "currentColor"}
                    strokeOpacity={isHovered ? 0.8 : 0.18}
                    strokeWidth={isHovered ? 2 : 1}
                  />
                );
              })}

              {visibleNodes.map((node) => {
                const pos = nodePositions[node.id];
                if (!pos) return null;
                const isDoc = node.group === "DOCUMENT";
                const isHovered = hoveredNode?.id === node.id;
                const nodeColor = GROUP_COLORS[node.group] || GROUP_COLORS.OTHER;
                const radius = isDoc ? 22 : Math.max(9, Math.min(node.size, 18));

                return (
                  <g
                    key={node.id}
                    transform={`translate(${pos.x}, ${pos.y})`}
                    className="cursor-pointer transition-transform duration-150"
                    onMouseEnter={() => setHoveredNode(node)}
                    onMouseLeave={() => setHoveredNode(null)}
                  >
                    <circle
                      r={radius + (isHovered ? 4 : 0)}
                      fill={nodeColor}
                      fillOpacity={isDoc ? 0.95 : 0.85}
                      stroke={isHovered ? "#ffffff" : "#000000"}
                      strokeWidth={isHovered ? 2.5 : 1}
                      strokeOpacity={0.4}
                    />
                    <text
                      dy={radius + 12}
                      textAnchor="middle"
                      className="fill-foreground text-[10px] font-medium pointer-events-none"
                    >
                      {node.label.length > 18 ? node.label.slice(0, 16) + "…" : node.label}
                    </text>
                  </g>
                );
              })}
            </svg>

            {hoveredNode && (
              <div className="absolute bottom-3 left-3 bg-popover/95 border border-border p-3 rounded-xl shadow-lg backdrop-blur text-xs space-y-1 max-w-xs z-10">
                <div className="flex items-center gap-2 font-bold text-foreground">
                  <span
                    className="h-2.5 w-2.5 rounded-full"
                    style={{ backgroundColor: GROUP_COLORS[hoveredNode.group] || GROUP_COLORS.OTHER }}
                  />
                  <span>{hoveredNode.label}</span>
                </div>
                <p className="text-[11px] text-muted-foreground">
                  Type: <b className="text-foreground">{hoveredNode.group}</b>
                </p>
                <p className="text-[10px] text-muted-foreground">Node ID: {hoveredNode.id}</p>
              </div>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

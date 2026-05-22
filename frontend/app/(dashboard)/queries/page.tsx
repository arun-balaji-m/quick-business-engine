"use client";

import { useState, useRef } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { queryApi, ticketApi } from "@/lib/api/endpoints";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "@/components/ui/dialog";
import {
  BarChart, Bar, LineChart, Line, PieChart, Pie, Cell,
  ResponsiveContainer, XAxis, YAxis, Tooltip, Legend,
} from "recharts";
import {
  Zap, Download, CheckCircle, XCircle, Loader2,
  Code2, Table, BarChart3, Lightbulb, Clock, Hash,
} from "lucide-react";
import type { QueryResponse, ChartConfig } from "@/types/api";
import { formatDate, formatDateTime, cn } from "@/lib/utils";

const CHART_COLORS = ["#6272f6", "#22c55e", "#f59e0b", "#ef4444", "#8b5cf6", "#06b6d4"];

const EXAMPLE_QUESTIONS = [
  "Show me all cancelled invoices from last month",
  "How many appointments were completed by each department?",
  "List the top 10 patients by total invoice amount",
  "What is the revenue trend over the last 6 months?",
  "Show overdue invoices with patient details",
  "How many appointments were cancelled yesterday?",
];

function ResultTable({ columns, rows }: { columns: { name: string; type: string }[]; rows: Record<string, unknown>[] }) {
  if (rows.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-16 text-center">
        <Table className="w-10 h-10 text-muted-foreground/40 mb-3" />
        <p className="text-muted-foreground font-medium">No records returned</p>
        <p className="text-sm text-muted-foreground/70">Try adjusting your question or filters</p>
      </div>
    );
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b bg-muted/50">
            {columns.map((col) => (
              <th key={col.name} className="px-3 py-2.5 text-left font-medium text-muted-foreground whitespace-nowrap">
                {col.name}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, i) => (
            <tr key={i} className="border-b hover:bg-muted/30 transition-colors">
              {columns.map((col) => (
                <td key={col.name} className="px-3 py-2 text-sm whitespace-nowrap max-w-xs truncate" title={String(row[col.name] ?? "")}>
                  {row[col.name] === null || row[col.name] === undefined ? (
                    <span className="text-muted-foreground/50">—</span>
                  ) : (
                    String(row[col.name])
                  )}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function ChartView({ chart }: { chart: ChartConfig }) {
  if (!chart.data || chart.data.length === 0) return null;

  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-sm">{chart.title}</CardTitle>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={200}>
          {chart.chart_type === "pie" ? (
            <PieChart>
              <Pie data={chart.data} dataKey={chart.y_keys[0]} nameKey={chart.x_key} cx="50%" cy="50%" outerRadius={70}>
                {chart.data.map((_, idx) => (
                  <Cell key={idx} fill={CHART_COLORS[idx % CHART_COLORS.length]} />
                ))}
              </Pie>
              <Tooltip />
              <Legend />
            </PieChart>
          ) : chart.chart_type === "line" ? (
            <LineChart data={chart.data} margin={{ top: 0, right: 0, left: -20, bottom: 0 }}>
              <XAxis dataKey={chart.x_key} tick={{ fontSize: 11 }} />
              <YAxis tick={{ fontSize: 11 }} />
              <Tooltip />
              <Legend />
              {chart.y_keys.map((key, i) => (
                <Line key={key} type="monotone" dataKey={key} stroke={CHART_COLORS[i % CHART_COLORS.length]} strokeWidth={2} dot={false} />
              ))}
            </LineChart>
          ) : (
            <BarChart data={chart.data} margin={{ top: 0, right: 0, left: -20, bottom: 0 }}>
              <XAxis dataKey={chart.x_key} tick={{ fontSize: 11 }} />
              <YAxis tick={{ fontSize: 11 }} />
              <Tooltip />
              <Legend />
              {chart.y_keys.map((key, i) => (
                <Bar key={key} dataKey={key} fill={CHART_COLORS[i % CHART_COLORS.length]} radius={[4, 4, 0, 0]} />
              ))}
            </BarChart>
          )}
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
}

export default function QueryPage() {
  const [question, setQuestion] = useState("");
  const [result, setResult] = useState<QueryResponse | null>(null);
  const [showSatisfactionDialog, setShowSatisfactionDialog] = useState(false);
  const queryClient = useQueryClient();
  const textAreaRef = useRef<HTMLTextAreaElement>(null);

  const askMutation = useMutation({
    mutationFn: queryApi.ask,
    onSuccess: (data) => {
      setResult(data);
      setShowSatisfactionDialog(true);
      queryClient.invalidateQueries({ queryKey: ["tickets"] });
      queryClient.invalidateQueries({ queryKey: ["dashboard"] });
    },
  });

  const closeMutation = useMutation({
    mutationFn: ({ id, satisfied }: { id: number; satisfied: boolean }) =>
      ticketApi.close(id, { is_satisfied: satisfied }),
    onSuccess: () => {
      setShowSatisfactionDialog(false);
      queryClient.invalidateQueries({ queryKey: ["tickets"] });
    },
  });

  const handleDownload = async (format: "csv" | "excel") => {
    if (!result) return;
    try {
      const blob = format === "csv"
        ? await queryApi.exportCsv(result.id)
        : await queryApi.exportExcel(result.id);
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `qube_query_${result.id}.${format === "csv" ? "csv" : "xlsx"}`;
      a.click();
      URL.revokeObjectURL(url);
    } catch (e) {
      console.error("Export failed", e);
    }
  };

  return (
    <div className="space-y-4 animate-fade-in">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Query Workspace</h1>
        <p className="text-sm text-muted-foreground mt-1">
          Ask questions in plain English — AI converts them to SQL
        </p>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-4 gap-4">
        {/* LEFT: Examples + Ticket Status */}
        <div className="space-y-4">
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm flex items-center gap-2">
                <Lightbulb className="w-4 h-4 text-amber-500" />
                Example Questions
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-1.5">
              {EXAMPLE_QUESTIONS.map((q) => (
                <button
                  key={q}
                  className="w-full text-left text-xs text-muted-foreground hover:text-foreground hover:bg-muted px-2 py-1.5 rounded-md transition-colors"
                  onClick={() => {
                    setQuestion(q);
                    textAreaRef.current?.focus();
                  }}
                >
                  {q}
                </button>
              ))}
            </CardContent>
          </Card>

          {result?.ticket_id && (
            <Card>
              <CardContent className="p-4 space-y-2">
                <p className="text-xs font-medium text-muted-foreground uppercase tracking-widest">
                  Current Ticket
                </p>
                <div className="flex items-center justify-between">
                  <Badge variant="warning">OPEN</Badge>
                  <span className="text-xs text-muted-foreground">#{result.ticket_id}</span>
                </div>
                <p className="text-xs text-muted-foreground truncate">{result.question}</p>
              </CardContent>
            </Card>
          )}
        </div>

        {/* CENTER: Input + Results */}
        <div className="xl:col-span-2 space-y-4">
          {/* Question Input */}
          <Card>
            <CardContent className="p-4 space-y-3">
              <Textarea
                ref={textAreaRef}
                value={question}
                onChange={(e) => setQuestion(e.target.value)}
                placeholder="Ask a question about your data…&#10;e.g. Show cancelled invoices from last month"
                className="min-h-[120px] resize-none text-base font-light"
                onKeyDown={(e) => {
                  if (e.key === "Enter" && (e.ctrlKey || e.metaKey)) {
                    e.preventDefault();
                    if (question.trim()) askMutation.mutate(question.trim());
                  }
                }}
              />
              <div className="flex items-center justify-between">
                <p className="text-xs text-muted-foreground">Press Ctrl+Enter to submit</p>
                <Button
                  onClick={() => question.trim() && askMutation.mutate(question.trim())}
                  disabled={!question.trim() || askMutation.isPending}
                >
                  {askMutation.isPending ? (
                    <>
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                      Analyzing…
                    </>
                  ) : (
                    <>
                      <Zap className="mr-2 h-4 w-4" />
                      Ask QuBE
                    </>
                  )}
                </Button>
              </div>
            </CardContent>
          </Card>

          {/* Error state */}
          {askMutation.isError && (
            <Card className="border-destructive/30 bg-destructive/5">
              <CardContent className="p-4">
                <div className="flex gap-3 items-start">
                  <XCircle className="w-5 h-5 text-destructive shrink-0 mt-0.5" />
                  <div>
                    <p className="text-sm font-medium text-destructive">Query failed</p>
                    <p className="text-xs text-muted-foreground mt-1">
                      {(askMutation.error as {response?: {data?: {detail?: string}}})?.response?.data?.detail || "An error occurred"}
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>
          )}

          {/* Loading skeleton */}
          {askMutation.isPending && (
            <Card>
              <CardContent className="p-4 space-y-2">
                <Skeleton className="h-4 w-3/4" />
                <Skeleton className="h-4 w-full" />
                <Skeleton className="h-4 w-1/2" />
                <div className="mt-4 space-y-2">
                  <Skeleton className="h-8 w-full" />
                  {[...Array(5)].map((_, i) => <Skeleton key={i} className="h-6 w-full" />)}
                </div>
              </CardContent>
            </Card>
          )}

          {/* Results */}
          {result && !askMutation.isPending && (
            <Card>
              <CardContent className="p-0">
                <Tabs defaultValue="table">
                  <div className="flex items-center justify-between px-4 pt-4 pb-2">
                    <TabsList>
                      <TabsTrigger value="table" className="gap-1.5">
                        <Table className="w-3.5 h-3.5" />
                        Table
                      </TabsTrigger>
                      <TabsTrigger value="sql" className="gap-1.5">
                        <Code2 className="w-3.5 h-3.5" />
                        SQL
                      </TabsTrigger>
                    </TabsList>

                    <div className="flex items-center gap-2">
                      <div className="flex items-center gap-3 text-xs text-muted-foreground">
                        <span className="flex items-center gap-1">
                          <Hash className="w-3 h-3" />
                          {result.row_count} rows
                        </span>
                        <span className="flex items-center gap-1">
                          <Clock className="w-3 h-3" />
                          {result.execution_time_ms}ms
                        </span>
                      </div>
                      <div className="flex gap-1">
                        <Button variant="outline" size="sm" onClick={() => handleDownload("csv")}>
                          <Download className="w-3 h-3 mr-1" />
                          CSV
                        </Button>
                        <Button variant="outline" size="sm" onClick={() => handleDownload("excel")}>
                          <Download className="w-3 h-3 mr-1" />
                          Excel
                        </Button>
                      </div>
                    </div>
                  </div>

                  <TabsContent value="table" className="mt-0 border-t">
                    <ResultTable columns={result.columns} rows={result.rows} />
                  </TabsContent>

                  <TabsContent value="sql" className="mt-0 border-t">
                    <div className="p-4">
                      <pre className="sql-display text-xs">{result.generated_sql}</pre>
                    </div>
                  </TabsContent>
                </Tabs>
              </CardContent>
            </Card>
          )}
        </div>

        {/* RIGHT: Insights + Charts */}
        <div className="space-y-4">
          {result && !askMutation.isPending ? (
            <>
              {/* Explanation */}
              <Card>
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm flex items-center gap-2">
                    <Lightbulb className="w-4 h-4 text-amber-500" />
                    AI Insights
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-sm text-muted-foreground leading-relaxed">
                    {result.explanation}
                  </p>
                </CardContent>
              </Card>

              {/* Charts */}
              {result.charts.map((chart, i) => (
                <ChartView key={i} chart={chart} />
              ))}
            </>
          ) : (
            <Card className="border-dashed">
              <CardContent className="py-10 flex flex-col items-center text-center gap-2">
                <BarChart3 className="w-8 h-8 text-muted-foreground/40" />
                <p className="text-sm text-muted-foreground">Charts and insights appear here</p>
              </CardContent>
            </Card>
          )}
        </div>
      </div>

      {/* Satisfaction Dialog */}
      <Dialog open={showSatisfactionDialog} onOpenChange={setShowSatisfactionDialog}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle>Are you satisfied with the result?</DialogTitle>
          </DialogHeader>
          <p className="text-sm text-muted-foreground">
            A support ticket has been created for this query. Let us know if the results met your needs.
          </p>
          <DialogFooter className="gap-2 sm:gap-2">
            <Button
              variant="outline"
              onClick={() => {
                if (result?.ticket_id) {
                  closeMutation.mutate({ id: result.ticket_id, satisfied: false });
                } else {
                  setShowSatisfactionDialog(false);
                }
              }}
            >
              <XCircle className="w-4 h-4 mr-2 text-destructive" />
              Not satisfied
            </Button>
            <Button
              onClick={() => {
                if (result?.ticket_id) {
                  closeMutation.mutate({ id: result.ticket_id, satisfied: true });
                } else {
                  setShowSatisfactionDialog(false);
                }
              }}
            >
              <CheckCircle className="w-4 h-4 mr-2" />
              Yes, close ticket
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}

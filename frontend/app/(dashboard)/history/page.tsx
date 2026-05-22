"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { queryApi } from "@/lib/api/endpoints";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Dialog, DialogContent, DialogHeader, DialogTitle,
} from "@/components/ui/dialog";
import { CheckCircle, XCircle, Clock, Code2, Hash } from "lucide-react";
import type { QueryHistoryItem } from "@/types/api";
import { formatDateTime } from "@/lib/utils";

function QueryDetailModal({
  item,
  onClose,
}: {
  item: QueryHistoryItem | null;
  onClose: () => void;
}) {
  if (!item) return null;
  return (
    <Dialog open onOpenChange={onClose}>
      <DialogContent className="max-w-2xl">
        <DialogHeader>
          <DialogTitle>Query Details</DialogTitle>
        </DialogHeader>
        <div className="space-y-4">
          <div>
            <p className="text-xs font-medium text-muted-foreground uppercase tracking-widest mb-1">Question</p>
            <p className="text-sm">{item.question}</p>
          </div>
          {item.generated_sql && (
            <div>
              <p className="text-xs font-medium text-muted-foreground uppercase tracking-widest mb-1 flex items-center gap-1">
                <Code2 className="w-3 h-3" /> Generated SQL
              </p>
              <pre className="sql-display text-xs max-h-52 overflow-y-auto">{item.generated_sql}</pre>
            </div>
          )}
          {item.explanation && (
            <div>
              <p className="text-xs font-medium text-muted-foreground uppercase tracking-widest mb-1">AI Explanation</p>
              <p className="text-sm text-muted-foreground">{item.explanation}</p>
            </div>
          )}
          <div className="grid grid-cols-3 gap-3 text-xs text-muted-foreground">
            <div><span className="font-medium text-foreground block">Rows</span>{item.result_count ?? "—"}</div>
            <div><span className="font-medium text-foreground block">Time</span>{item.execution_time_ms ? `${item.execution_time_ms}ms` : "—"}</div>
            <div><span className="font-medium text-foreground block">Status</span>
              {item.is_successful ? "Success" : "Failed"}
            </div>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}

export default function HistoryPage() {
  const [page, setPage] = useState(1);
  const [selected, setSelected] = useState<QueryHistoryItem | null>(null);

  const { data, isLoading } = useQuery({
    queryKey: ["query-history", page],
    queryFn: () => queryApi.history(page, 25),
    staleTime: 10000,
  });

  return (
    <div className="space-y-5 animate-fade-in">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Query History</h1>
          <p className="text-sm text-muted-foreground mt-1">All past queries and their results</p>
        </div>
        <Badge variant="outline" className="text-sm px-3 py-1">
          {data?.total ?? "—"} queries
        </Badge>
      </div>

      <Card>
        <CardContent className="p-0">
          {isLoading ? (
            <div className="p-4 space-y-2">
              {[...Array(10)].map((_, i) => <Skeleton key={i} className="h-12 w-full" />)}
            </div>
          ) : !data?.items.length ? (
            <div className="flex flex-col items-center py-16 text-center gap-2">
              <Clock className="w-10 h-10 text-muted-foreground/40" />
              <p className="font-medium text-muted-foreground">No query history yet</p>
              <p className="text-sm text-muted-foreground/70">
                Questions you ask will appear here.
              </p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b bg-muted/50">
                    <th className="px-4 py-3 text-left font-medium text-muted-foreground">Question</th>
                    <th className="px-4 py-3 text-left font-medium text-muted-foreground">Rows</th>
                    <th className="px-4 py-3 text-left font-medium text-muted-foreground">Time</th>
                    <th className="px-4 py-3 text-left font-medium text-muted-foreground">Status</th>
                    <th className="px-4 py-3 text-left font-medium text-muted-foreground">Date</th>
                  </tr>
                </thead>
                <tbody>
                  {data.items.map((item) => (
                    <tr
                      key={item.id}
                      className="border-b hover:bg-muted/30 cursor-pointer transition-colors"
                      onClick={() => setSelected(item)}
                    >
                      <td className="px-4 py-3 max-w-sm truncate">{item.question}</td>
                      <td className="px-4 py-3 text-muted-foreground">
                        {item.result_count !== null ? (
                          <span className="flex items-center gap-1">
                            <Hash className="w-3 h-3" />{item.result_count}
                          </span>
                        ) : "—"}
                      </td>
                      <td className="px-4 py-3 text-muted-foreground whitespace-nowrap text-xs">
                        {item.execution_time_ms ? `${item.execution_time_ms}ms` : "—"}
                      </td>
                      <td className="px-4 py-3">
                        {item.is_successful ? (
                          <Badge variant="success">Success</Badge>
                        ) : (
                          <Badge variant="destructive">Failed</Badge>
                        )}
                      </td>
                      <td className="px-4 py-3 text-muted-foreground whitespace-nowrap text-xs">
                        {formatDateTime(item.created_at)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>

      {data && data.total_pages > 1 && (
        <div className="flex justify-center gap-2">
          <Button variant="outline" size="sm" disabled={page === 1} onClick={() => setPage(page - 1)}>
            Previous
          </Button>
          <span className="flex items-center text-sm text-muted-foreground px-2">
            Page {page} of {data.total_pages}
          </span>
          <Button variant="outline" size="sm" disabled={page >= data.total_pages} onClick={() => setPage(page + 1)}>
            Next
          </Button>
        </div>
      )}

      <QueryDetailModal item={selected} onClose={() => setSelected(null)} />
    </div>
  );
}

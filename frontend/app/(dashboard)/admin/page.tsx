"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { adminApi } from "@/lib/api/endpoints";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { Separator } from "@/components/ui/separator";
import { Database, RefreshCw, Table2, Server } from "lucide-react";
import { formatNumber } from "@/lib/utils";

export default function AdminPage() {
  const queryClient = useQueryClient();

  const { data: schemaTables, isLoading: tablesLoading } = useQuery({
    queryKey: ["admin", "schema-tables"],
    queryFn: adminApi.schemaTables,
  });

  const { data: rowCounts, isLoading: countsLoading, refetch: refetchCounts } = useQuery({
    queryKey: ["admin", "row-counts"],
    queryFn: adminApi.rowCounts,
    staleTime: 30000,
  });

  const reseedMutation = useMutation({
    mutationFn: adminApi.reseed,
    onSuccess: () => {
      setTimeout(() => {
        queryClient.invalidateQueries({ queryKey: ["admin"] });
        queryClient.invalidateQueries({ queryKey: ["dashboard"] });
      }, 3000);
    },
  });

  return (
    <div className="space-y-6 animate-fade-in">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Admin</h1>
        <p className="text-sm text-muted-foreground mt-1">Database management and demo controls</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Reseed */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base flex items-center gap-2">
              <Database className="w-4 h-4" />
              Demo Data
            </CardTitle>
            <CardDescription>
              Reseed the database with fresh demo data. This clears and recreates all records.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="p-3 bg-amber-50 dark:bg-amber-900/20 rounded-lg">
              <p className="text-xs text-amber-800 dark:text-amber-400">
                ⚠️ Reseeding will clear all existing demo data including tickets and query history.
              </p>
            </div>
            <Button
              variant="outline"
              onClick={() => reseedMutation.mutate()}
              disabled={reseedMutation.isPending}
            >
              <RefreshCw className={`w-4 h-4 mr-2 ${reseedMutation.isPending ? "animate-spin" : ""}`} />
              {reseedMutation.isPending ? "Reseeding…" : "Reseed Database"}
            </Button>
            {reseedMutation.isSuccess && (
              <p className="text-xs text-emerald-600">Reseeding started in background. Check logs.</p>
            )}
          </CardContent>
        </Card>

        {/* Schema Info */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base flex items-center gap-2">
              <Server className="w-4 h-4" />
              Schema Info
            </CardTitle>
          </CardHeader>
          <CardContent>
            {tablesLoading ? (
              <Skeleton className="h-20 w-full" />
            ) : (
              <div className="space-y-2">
                <div className="flex items-center justify-between text-sm">
                  <span className="text-muted-foreground">Schema</span>
                  <Badge variant="outline" className="font-mono text-xs">
                    {schemaTables?.schema}
                  </Badge>
                </div>
                <div className="flex items-center justify-between text-sm">
                  <span className="text-muted-foreground">Tables</span>
                  <span className="font-medium">{schemaTables?.tables?.length}</span>
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Row Counts */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle className="text-base flex items-center gap-2">
              <Table2 className="w-4 h-4" />
              Database Row Counts
            </CardTitle>
            <Button variant="ghost" size="sm" onClick={() => refetchCounts()}>
              <RefreshCw className="w-3.5 h-3.5 mr-1" />
              Refresh
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          {countsLoading ? (
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
              {[...Array(12)].map((_, i) => <Skeleton key={i} className="h-16 rounded-lg" />)}
            </div>
          ) : (
            <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-5 gap-3">
              {rowCounts?.counts &&
                Object.entries(rowCounts.counts).map(([table, count]) => (
                  <div key={table} className="border rounded-lg p-3 space-y-0.5">
                    <p className="text-xs font-mono text-muted-foreground">{table}</p>
                    <p className="text-xl font-bold">
                      {formatNumber(count as number)}
                    </p>
                  </div>
                ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Tables List */}
      {schemaTables?.tables && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Table Schema Browser</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
              {schemaTables.tables.map((t: { table: string; columns: number }) => (
                <div key={t.table} className="flex items-center justify-between px-3 py-2 bg-muted/50 rounded-md text-sm">
                  <span className="font-mono text-xs">{t.table}</span>
                  <Badge variant="outline" className="text-[10px]">{t.columns} cols</Badge>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}

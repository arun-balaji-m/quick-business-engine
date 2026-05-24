"use client";

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { ticketApi } from "@/lib/api/endpoints";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "@/components/ui/dialog";
import { CheckCircle, Clock, XCircle, ExternalLink, Code2 } from "lucide-react";
import type { Ticket, TicketStatus } from "@/types/api";
import { formatDateTime, cn } from "@/lib/utils";

const statusConfig: Record<
  TicketStatus,
  { label: string; variant: "warning" | "info" | "success"; icon: React.ElementType }
> = {
  OPEN: { label: "Open", variant: "warning", icon: Clock },
  IN_PROGRESS: { label: "In Progress", variant: "info", icon: ExternalLink },
  CLOSED: { label: "Closed", variant: "success", icon: CheckCircle },
};

function TicketStatusBadge({ status }: { status: TicketStatus }) {
  const config = statusConfig[status];
  return <Badge variant={config.variant}>{config.label}</Badge>;
}

function TicketDetailModal({
  ticket,
  onClose,
}: {
  ticket: Ticket | null;
  onClose: () => void;
}) {
  const queryClient = useQueryClient();
  const closeMutation = useMutation({
    mutationFn: ({ satisfied }: { satisfied: boolean }) =>
      ticketApi.close(ticket!.id, { is_satisfied: satisfied }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["tickets"] });
      onClose();
    },
  });

  if (!ticket) return null;

  return (
    <Dialog open onOpenChange={onClose}>
      <DialogContent className="max-w-lg">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-3">
            <span className="font-mono text-sm text-muted-foreground">{ticket.ticket_number}</span>
            <TicketStatusBadge status={ticket.status} />
          </DialogTitle>
        </DialogHeader>

        <div className="space-y-4">
          <div>
            <p className="text-xs font-medium text-muted-foreground uppercase tracking-widest mb-1">Question</p>
            <p className="text-sm">{ticket.title}</p>
          </div>

          {ticket.query?.generated_sql && (
            <div>
              <p className="text-xs font-medium text-muted-foreground uppercase tracking-widest mb-1 flex items-center gap-1">
                <Code2 className="w-3 h-3" />
                Generated SQL
              </p>
              <pre className="sql-display text-xs max-h-32 overflow-y-auto">
                {ticket.query?.generated_sql}
              </pre>
            </div>
          )}

          <div className="grid grid-cols-2 gap-3 text-xs text-muted-foreground">
            <div>
              <span className="font-medium text-foreground block">Created</span>
              {formatDateTime(ticket.created_at)}
            </div>
            {ticket.closed_at && (
              <div>
                <span className="font-medium text-foreground block">Closed</span>
                {formatDateTime(ticket.closed_at)}
              </div>
            )}
            {ticket.query?.result_count !== null && (
              <div>
                <span className="font-medium text-foreground block">Result Rows</span>
                {ticket.query?.result_count}
              </div>
            )}
            {ticket.query?.execution_time_ms !== null && (
              <div>
                <span className="font-medium text-foreground block">Execution Time</span>
                {ticket.query?.execution_time_ms}ms
              </div>
            )}
          </div>

          {ticket.resolution_notes && (
            <div>
              <p className="text-xs font-medium text-muted-foreground uppercase tracking-widest mb-1">Notes</p>
              <p className="text-sm">{ticket.resolution_notes}</p>
            </div>
          )}

          {ticket.is_satisfied !== null && (
            <div className="flex items-center gap-2">
              {ticket.is_satisfied ? (
                <CheckCircle className="w-4 h-4 text-emerald-500" />
              ) : (
                <XCircle className="w-4 h-4 text-destructive" />
              )}
              <span className="text-sm text-muted-foreground">
                {ticket.is_satisfied ? "User was satisfied" : "User was not satisfied"}
              </span>
            </div>
          )}
        </div>

        {ticket.status !== "CLOSED" && (
          <DialogFooter className="gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => closeMutation.mutate({ satisfied: false })}
              disabled={closeMutation.isPending}
            >
              <XCircle className="w-4 h-4 mr-1.5 text-destructive" />
              Close as unsatisfied
            </Button>
            <Button
              size="sm"
              onClick={() => closeMutation.mutate({ satisfied: true })}
              disabled={closeMutation.isPending}
            >
              <CheckCircle className="w-4 h-4 mr-1.5" />
              Close as satisfied
            </Button>
          </DialogFooter>
        )}
      </DialogContent>
    </Dialog>
  );
}

export default function TicketsPage() {
  const [statusFilter, setStatusFilter] = useState<string>("all");
  const [page, setPage] = useState(1);
  const [selectedTicket, setSelectedTicket] = useState<Ticket | null>(null);

  const { data, isLoading } = useQuery({
    queryKey: ["tickets", statusFilter, page],
    queryFn: () =>
      ticketApi.list({
        status: statusFilter === "all" ? undefined : statusFilter,
        page,
        page_size: 20,
      }),
    staleTime: 10000,
  });

  return (
    <div className="space-y-5 animate-fade-in">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Tickets</h1>
          <p className="text-sm text-muted-foreground mt-1">Track and manage query support tickets</p>
        </div>
        <Badge variant="outline" className="text-sm px-3 py-1">
          {data?.total ?? "—"} total
        </Badge>
      </div>

      {/* Status Filter Tabs */}
      <Tabs value={statusFilter} onValueChange={(v) => { setStatusFilter(v); setPage(1); }}>
        <TabsList>
          <TabsTrigger value="all">All</TabsTrigger>
          <TabsTrigger value="OPEN">Open</TabsTrigger>
          <TabsTrigger value="IN_PROGRESS">In Progress</TabsTrigger>
          <TabsTrigger value="CLOSED">Closed</TabsTrigger>
        </TabsList>
      </Tabs>

      {/* Tickets Table */}
      <Card>
        <CardContent className="p-0">
          {isLoading ? (
            <div className="p-4 space-y-2">
              {[...Array(8)].map((_, i) => <Skeleton key={i} className="h-12 w-full" />)}
            </div>
          ) : !data?.items.length ? (
            <div className="flex flex-col items-center py-16 text-center gap-2">
              <CheckCircle className="w-10 h-10 text-muted-foreground/40" />
              <p className="font-medium text-muted-foreground">No tickets found</p>
              <p className="text-sm text-muted-foreground/70">
                {statusFilter === "all"
                  ? "Tickets are created automatically when you ask questions."
                  : `No ${statusFilter.toLowerCase()} tickets.`}
              </p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b bg-muted/50">
                    <th className="px-4 py-3 text-left font-medium text-muted-foreground">Ticket</th>
                    <th className="px-4 py-3 text-left font-medium text-muted-foreground">Question</th>
                    <th className="px-4 py-3 text-left font-medium text-muted-foreground">Status</th>
                    <th className="px-4 py-3 text-left font-medium text-muted-foreground">Created</th>
                    <th className="px-4 py-3 text-left font-medium text-muted-foreground">Updated</th>
                  </tr>
                </thead>
                <tbody>
                  {data.items.map((ticket) => (
                    <tr
                      key={ticket.id}
                      className="border-b hover:bg-muted/30 cursor-pointer transition-colors"
                      onClick={() => setSelectedTicket(ticket)}
                    >
                      <td className="px-4 py-3 font-mono text-xs text-muted-foreground">
                        {ticket.ticket_number}
                      </td>
                      <td className="px-4 py-3 max-w-xs truncate">{ticket.title}</td>
                      <td className="px-4 py-3">
                        <TicketStatusBadge status={ticket.status} />
                      </td>
                      <td className="px-4 py-3 text-muted-foreground whitespace-nowrap text-xs">
                        {formatDateTime(ticket.created_at)}
                      </td>
                      <td className="px-4 py-3 text-muted-foreground whitespace-nowrap text-xs">
                        {formatDateTime(ticket.updated_at)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Pagination */}
      {data && data.total_pages > 1 && (
        <div className="flex justify-center gap-2">
          <Button variant="outline" size="sm" disabled={page === 1} onClick={() => setPage(page - 1)}>
            Previous
          </Button>
          <span className="flex items-center text-sm text-muted-foreground px-2">
            Page {page} of {data.total_pages}
          </span>
          <Button
            variant="outline"
            size="sm"
            disabled={page >= data.total_pages}
            onClick={() => setPage(page + 1)}
          >
            Next
          </Button>
        </div>
      )}

      {selectedTicket && (
        <TicketDetailModal
          ticket={selectedTicket}
          onClose={() => setSelectedTicket(null)}
        />
      )}
    </div>
  );
}

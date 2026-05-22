"use client";

import { Bell, LogOut, User } from "lucide-react";
import { useAuth } from "@/lib/auth/auth-context";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { useQuery } from "@tanstack/react-query";
import { ticketApi } from "@/lib/api/endpoints";

export function Navbar() {
  const { user, logout } = useAuth();

  const { data: tickets } = useQuery({
    queryKey: ["tickets", "open"],
    queryFn: () => ticketApi.list({ status: "OPEN", page_size: 1 }),
    enabled: !!user,
    staleTime: 30000,
  });

  const openCount = tickets?.total || 0;

  return (
    <header className="h-14 border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60 flex items-center justify-between px-6 shrink-0">
      <div className="flex items-center gap-2">
        <p className="text-sm text-muted-foreground">
          Welcome back, <span className="font-medium text-foreground">{user?.full_name || user?.username}</span>
        </p>
      </div>

      <div className="flex items-center gap-3">
        {/* Notifications */}
        <Button variant="ghost" size="icon" className="relative" asChild>
          <a href="/tickets">
            <Bell className="h-4 w-4" />
            {openCount > 0 && (
              <Badge
                variant="destructive"
                className="absolute -top-1 -right-1 h-4 w-4 p-0 flex items-center justify-center text-[10px] rounded-full"
              >
                {openCount > 9 ? "9+" : openCount}
              </Badge>
            )}
          </a>
        </Button>

        {/* User info */}
        <div className="flex items-center gap-2 pl-2 border-l">
          <div className="flex items-center justify-center w-7 h-7 rounded-full bg-primary/10 text-primary">
            <User className="w-3.5 h-3.5" />
          </div>
          <div className="hidden sm:block">
            <p className="text-xs font-medium leading-none">{user?.username}</p>
            <p className="text-[10px] text-muted-foreground capitalize mt-0.5">{user?.role}</p>
          </div>
        </div>

        {/* Logout */}
        <Button variant="ghost" size="icon" onClick={logout} title="Logout">
          <LogOut className="h-4 w-4" />
        </Button>
      </div>
    </header>
  );
}

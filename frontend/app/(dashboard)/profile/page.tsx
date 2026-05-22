"use client";

import { useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { useAuth } from "@/lib/auth/auth-context";
import { authApi } from "@/lib/api/endpoints";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { User, Shield, Key, CheckCircle } from "lucide-react";
import type { AxiosError } from "axios";
import type { APIError } from "@/types/api";
import { formatDate } from "@/lib/utils";

export default function ProfilePage() {
  const { user } = useAuth();
  const [passwordSuccess, setPasswordSuccess] = useState(false);
  const [passwordError, setPasswordError] = useState("");

  const passwordMutation = useMutation({
    mutationFn: (data: { current_password: string; new_password: string }) =>
      authApi.changePassword(data),
    onSuccess: () => {
      setPasswordSuccess(true);
      setPasswordError("");
      setTimeout(() => setPasswordSuccess(false), 3000);
    },
    onError: (err: AxiosError<APIError>) => {
      setPasswordError(err.response?.data?.detail || "Failed to change password");
    },
  });

  const handlePasswordSubmit = (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setPasswordError("");
    const fd = new FormData(e.currentTarget);
    passwordMutation.mutate({
      current_password: fd.get("current_password") as string,
      new_password: fd.get("new_password") as string,
    });
    (e.target as HTMLFormElement).reset();
  };

  return (
    <div className="space-y-6 animate-fade-in max-w-2xl">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Profile</h1>
        <p className="text-sm text-muted-foreground mt-1">Manage your account settings</p>
      </div>

      {/* Account Info */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-base">
            <User className="w-4 h-4" />
            Account Information
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center gap-4">
            <div className="flex items-center justify-center w-14 h-14 rounded-full bg-primary/10 text-primary text-xl font-bold">
              {user?.full_name?.charAt(0) || user?.username?.charAt(0).toUpperCase()}
            </div>
            <div>
              <p className="font-semibold text-lg">{user?.full_name || user?.username}</p>
              <p className="text-sm text-muted-foreground">{user?.email}</p>
              <div className="flex items-center gap-2 mt-1">
                <Badge variant="outline" className="capitalize text-xs">
                  <Shield className="w-3 h-3 mr-1" />
                  {user?.role}
                </Badge>
                {user?.is_active && (
                  <Badge variant="success" className="text-xs">Active</Badge>
                )}
              </div>
            </div>
          </div>

          <Separator />

          <div className="grid grid-cols-2 gap-4 text-sm">
            <div>
              <p className="text-muted-foreground text-xs font-medium uppercase tracking-widest mb-1">
                Username
              </p>
              <p className="font-mono">{user?.username}</p>
            </div>
            <div>
              <p className="text-muted-foreground text-xs font-medium uppercase tracking-widest mb-1">
                Member Since
              </p>
              <p>{user?.created_at ? formatDate(user.created_at) : "—"}</p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Change Password */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-base">
            <Key className="w-4 h-4" />
            Change Password
          </CardTitle>
          <CardDescription>Update your account password</CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handlePasswordSubmit} className="space-y-4 max-w-sm">
            <div className="space-y-2">
              <Label htmlFor="current_password">Current Password</Label>
              <Input
                id="current_password"
                name="current_password"
                type="password"
                required
                placeholder="••••••••"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="new_password">New Password</Label>
              <Input
                id="new_password"
                name="new_password"
                type="password"
                required
                minLength={8}
                placeholder="Min. 8 characters"
              />
            </div>

            {passwordError && (
              <p className="text-sm text-destructive bg-destructive/10 px-3 py-2 rounded-md">
                {passwordError}
              </p>
            )}
            {passwordSuccess && (
              <div className="flex items-center gap-2 text-sm text-emerald-600 bg-emerald-50 dark:bg-emerald-900/20 px-3 py-2 rounded-md">
                <CheckCircle className="w-4 h-4" />
                Password updated successfully
              </div>
            )}

            <Button type="submit" disabled={passwordMutation.isPending}>
              {passwordMutation.isPending ? "Updating…" : "Update Password"}
            </Button>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}

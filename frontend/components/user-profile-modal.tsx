"use client";

import { useState } from "react";
import {
  Calendar,
  CheckCircle2,
  Eye,
  EyeOff,
  KeyRound,
  Mail,
  Shield,
  User,
  X,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";

interface UserProfileModalProps {
  isOpen: boolean;
  onClose: () => void;
  currentUser: string;
  emailAddress?: string;
  role?: string;
  isVerified?: boolean;
  createdAt?: string;
  totalDocuments?: number;
}

export function UserProfileModal({
  isOpen,
  onClose,
  currentUser,
  emailAddress = "user@tokenbrief.ai",
  role = "User",
  isVerified = true,
  createdAt,
  totalDocuments = 0,
}: UserProfileModalProps) {
  const [showPassword, setShowPassword] = useState(false);
  const [testPasswordInput, setTestPasswordInput] = useState("");

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
      <div className="relative w-full max-w-md rounded-2xl border border-border bg-card p-6 shadow-2xl space-y-5 animate-in fade-in-50 zoom-in-95">
        <button
          type="button"
          onClick={onClose}
          className="absolute right-4 top-4 text-muted-foreground hover:text-foreground p-1 rounded-lg hover:bg-muted"
        >
          <X className="h-4 w-4" />
        </button>

        <div className="flex items-center gap-3.5 border-b border-border/60 pb-4">
          <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-2xl bg-gradient-to-tr from-primary to-indigo-500 text-lg font-bold text-white shadow-md shadow-primary/20">
            {currentUser.slice(0, 1).toUpperCase()}
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h3 className="text-base font-extrabold tracking-tight">{currentUser}</h3>
              {isVerified && (
                <Badge variant="secondary" className="bg-emerald-500/10 text-emerald-600 text-[10px] gap-1">
                  <CheckCircle2 className="h-3 w-3" /> Verified
                </Badge>
              )}
            </div>
            <p className="text-xs text-muted-foreground">{emailAddress}</p>
          </div>
        </div>

        <div className="space-y-3 text-xs">
          <div className="grid grid-cols-2 gap-2.5">
            <div className="p-3 rounded-xl border border-border/60 bg-muted/20">
              <span className="text-muted-foreground flex items-center gap-1.5 text-[11px]">
                <Shield className="h-3.5 w-3.5 text-primary" /> Role
              </span>
              <p className="mt-1 font-semibold text-foreground capitalize">{role}</p>
            </div>
            <div className="p-3 rounded-xl border border-border/60 bg-muted/20">
              <span className="text-muted-foreground flex items-center gap-1.5 text-[11px]">
                <Calendar className="h-3.5 w-3.5 text-indigo-500" /> Documents
              </span>
              <p className="mt-1 font-semibold text-foreground">{totalDocuments} indexed</p>
            </div>
          </div>

          <div className="space-y-2 pt-2 border-t border-border/40">
            <label className="text-xs font-semibold text-muted-foreground flex items-center justify-between">
              <span className="flex items-center gap-1.5">
                <KeyRound className="h-3.5 w-3.5 text-amber-500" /> Password Visibility Check
              </span>
              <span className="text-[10px] text-muted-foreground">Toggle to view</span>
            </label>
            <div className="relative">
              <input
                type={showPassword ? "text" : "password"}
                placeholder="Type password to test visibility..."
                value={testPasswordInput}
                onChange={(e) => setTestPasswordInput(e.target.value)}
                className="w-full text-xs rounded-lg border border-border bg-background px-3 py-2 pr-9 text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-1 focus:ring-primary"
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="absolute right-2.5 top-2.5 text-muted-foreground hover:text-foreground"
                title={showPassword ? "Hide password" : "Show password"}
              >
                {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
              </button>
            </div>
            <p className="text-[11px] text-muted-foreground">
              Verify your password characters clearly with one click before logging in or saving credentials.
            </p>
          </div>
        </div>

        <div className="flex justify-end pt-2 border-t border-border/60">
          <Button size="sm" onClick={onClose} className="text-xs h-8 px-4">
            Close
          </Button>
        </div>
      </div>
    </div>
  );
}

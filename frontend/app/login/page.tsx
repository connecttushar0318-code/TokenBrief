"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { ThemeToggle } from "@/components/theme-toggle";
import { DinoRangerLogo } from "@/components/dino-ranger-logo";
import { loginSchema, registrationSchema } from "@/lib/validations";
import {
  ShieldCheck,
  Mail,
  Lock,
  User,
  ArrowRight,
  ArrowLeft,
  CheckCircle2,
  AlertCircle,
  KeyRound,
  RotateCcw,
  Sparkles,
  Eye,
  EyeOff,
} from "lucide-react";

type AuthMode = "login" | "register" | "verify_otp" | "forgot_password" | "reset_password";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function LoginPage() {
  const router = useRouter();
  const [mode, setMode] = useState<AuthMode>("login");
  const [formData, setFormData] = useState({
    username: "",
    email: "",
    password: "",
    otp_code: "",
    new_password: "",
  });
  const [showPassword, setShowPassword] = useState(false);
  const [showNewPassword, setShowNewPassword] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [sandboxOtp, setSandboxOtp] = useState<string | null>(null);

  const resetMessages = () => {
    setError(null);
    setSuccessMsg(null);
  };

  const handleModeChange = (newMode: AuthMode) => {
    resetMessages();
    setMode(newMode);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    resetMessages();
    setIsLoading(true);

    try {
      if (mode === "login") {
        const validation = loginSchema.safeParse({
          username: formData.username,
          password: formData.password,
        });
        if (!validation.success) {
          throw new Error(validation.error.errors[0]?.message);
        }

        const res = await fetch(`${API_BASE_URL}/api/auth/login`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          credentials: "include",
          body: JSON.stringify({
            username: formData.username.trim(),
            password: formData.password,
          }),
        });

        const data = await res.json().catch(() => ({}));

        if (!res.ok) {
          if (res.status === 403 && data.detail && typeof data.detail === "string" && data.detail.includes("not verified")) {
            setFormData((prev) => ({
              ...prev,
              email: formData.username.includes("@") ? formData.username : prev.email,
            }));
            setSuccessMsg("Please verify your email to activate your account.");
            setMode("verify_otp");
            return;
          }
          const errorMsg = typeof data.detail === "string" 
            ? data.detail 
            : Array.isArray(data.detail) 
              ? data.detail.map((d: any) => d.msg).join(", ") 
              : "Authentication failed. Check your username and password.";
          throw new Error(errorMsg);
        }

        router.push("/dashboard");
      } else if (mode === "register") {
        const validation = registrationSchema.safeParse({
          username: formData.username,
          email: formData.email,
          password: formData.password,
        });
        if (!validation.success) {
          throw new Error(validation.error.errors[0]?.message);
        }

        const res = await fetch(`${API_BASE_URL}/api/auth/register`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          credentials: "include",
          body: JSON.stringify({
            username: formData.username.trim(),
            email_address: formData.email.trim(),
            password: formData.password,
          }),
        });

        const data = await res.json().catch(() => ({}));
        if (!res.ok) {
          const errorMsg = typeof data.detail === "string" 
            ? data.detail 
            : Array.isArray(data.detail) 
              ? data.detail.map((d: any) => d.msg).join(", ") 
              : "Registration failed";
          throw new Error(errorMsg);
        }

        const otpMatch = data.message?.match(/Sandbox OTP:\s*(\d+)/);
        if (otpMatch) {
          setSandboxOtp(otpMatch[1]);
          setFormData((prev) => ({ ...prev, otp_code: otpMatch[1] }));
        }

        setSuccessMsg(data.message || `Verification OTP sent to ${formData.email}`);
        setMode("verify_otp");
      } else if (mode === "verify_otp") {
        if (!formData.otp_code || formData.otp_code.trim().length !== 6) {
          throw new Error("Please enter a valid 6-digit OTP code");
        }

        const res = await fetch(`${API_BASE_URL}/api/auth/verify-email`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          credentials: "include",
          body: JSON.stringify({
            email_address: formData.email.trim(),
            otp_code: formData.otp_code.trim(),
          }),
        });

        const data = await res.json().catch(() => ({}));
        if (!res.ok) {
          throw new Error(data.detail || "Invalid or expired OTP");
        }

        router.push("/dashboard");
      } else if (mode === "forgot_password") {
        if (!formData.email.trim()) {
          throw new Error("Please enter your registered email address");
        }

        const res = await fetch(`${API_BASE_URL}/api/auth/forgot-password`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          credentials: "include",
          body: JSON.stringify({
            email_address: formData.email.trim(),
          }),
        });

        const data = await res.json().catch(() => ({}));
        if (!res.ok) {
          throw new Error(data.detail || "Failed to initiate password reset");
        }

        const otpMatch = data.message?.match(/Sandbox OTP:\s*(\d+)/);
        if (otpMatch) {
          setSandboxOtp(otpMatch[1]);
          setFormData((prev) => ({ ...prev, otp_code: otpMatch[1] }));
        }

        setSuccessMsg(data.message || "Password reset OTP dispatched to your email");
        setMode("reset_password");
      } else if (mode === "reset_password") {
        if (!formData.otp_code || formData.otp_code.trim().length !== 6) {
          throw new Error("Please enter a valid 6-digit reset code");
        }
        if (!formData.new_password || formData.new_password.length < 4) {
          throw new Error("New password must be at least 4 characters long");
        }

        const res = await fetch(`${API_BASE_URL}/api/auth/reset-password`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          credentials: "include",
          body: JSON.stringify({
            email_address: formData.email.trim(),
            otp_code: formData.otp_code.trim(),
            new_password: formData.new_password,
          }),
        });

        const data = await res.json().catch(() => ({}));
        if (!res.ok) {
          throw new Error(data.detail || "Password reset failed");
        }

        setSuccessMsg("Password reset successfully! Please sign in with your new password.");
        setMode("login");
      }
    } catch (err: any) {
      if (err.name === "TypeError" && (err.message === "Failed to fetch" || err.message?.includes("fetch"))) {
        setError("Connecting to cloud server... On Render free tier, the backend takes ~30-45s to wake up from idle. Please wait 10 seconds and try again.");
      } else {
        setError(err.message || "An unexpected error occurred");
      }
    } finally {
      setIsLoading(false);
    }
  };

  const handleResendOtp = async () => {
    if (!formData.email.trim()) {
      setError("Please provide your email address first");
      return;
    }
    setIsLoading(true);
    resetMessages();
    try {
      const res = await fetch(`${API_BASE_URL}/api/auth/resend-otp`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({ email_address: formData.email.trim() }),
      });
      const data = await res.json().catch(() => ({}));
      if (!res.ok) {
        throw new Error(data.detail || "Failed to resend OTP");
      }
      const otpMatch = data.message?.match(/Sandbox OTP:\s*(\d+)/);
      if (otpMatch) {
        setSandboxOtp(otpMatch[1]);
        setFormData((prev) => ({ ...prev, otp_code: otpMatch[1] }));
      }
      setSuccessMsg(data.message || "Fresh OTP dispatched to your inbox");
    } catch (err: any) {
      if (err.name === "TypeError" && (err.message === "Failed to fetch" || err.message?.includes("fetch"))) {
        setError("Connecting to cloud server... The backend is waking up, please retry in a moment.");
      } else {
        setError(err.message || "Failed to resend code");
      }
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="page-surface min-h-screen bg-background text-foreground flex flex-col justify-center items-center p-4 sm:p-6 relative">
      <div className="absolute left-4 sm:left-6 top-5 sm:top-6 flex items-center gap-2 sm:gap-3">
        <Link
          href="/"
          className="inline-flex items-center gap-1.5 text-xs font-medium text-muted-foreground hover:text-foreground transition-colors py-1.5 px-2 rounded-lg hover:bg-muted"
          aria-label="Back to Home"
        >
          <ArrowLeft className="h-4 w-4" />
          <span className="hidden sm:inline">Back to Home</span>
        </Link>
        <div className="h-4 w-px bg-border/80 hidden sm:block" />
        <Link href="/" className="flex items-center gap-2 group" aria-label="TokenBrief home">
          <DinoRangerLogo size={32} className="group-hover:rotate-3" />
          <span className="text-base font-extrabold tracking-tight">
            Token<span className="text-primary">Brief</span>
          </span>
        </Link>
      </div>

      <div className="absolute top-5 sm:top-6 right-4 sm:right-6">
        <ThemeToggle />
      </div>

      <div className="w-full max-w-md space-y-6 pt-16 sm:pt-0">
        <div className="text-center space-y-2">
          <div className="inline-flex items-center justify-center mb-1">
            <DinoRangerLogo size={56} animated={true} />
          </div>
          <h1 className="text-2xl font-bold tracking-tight">
            Token<span className="text-primary">Brief</span> Workspace
          </h1>
          <p className="text-xs sm:text-sm text-muted-foreground">
            Sign in to access your intelligent document workspace.
          </p>
        </div>

        <Card className="bg-card/95 shadow-[0_12px_36px_rgba(15,23,42,0.08)] border-border/80">
          <CardHeader className="space-y-1 pb-4">
            <div>
              <CardTitle className="text-lg font-semibold">
                {mode === "login" && "Welcome Back"}
                {mode === "register" && "Create Account"}
                {mode === "verify_otp" && "Verify your email"}
                {mode === "forgot_password" && "Forgot Password"}
                {mode === "reset_password" && "Set New Password"}
              </CardTitle>
            </div>
            <CardDescription className="text-xs sm:text-sm leading-5">
              {mode === "login" && "Enter your credentials to access your document workspace."}
              {mode === "register" && "Create an account to start asking smart questions across your files."}
              {mode === "verify_otp" && `Enter the six-digit code sent to ${formData.email || "your email"}.`}
              {mode === "forgot_password" && "We will send a one-time reset code to your email address."}
              {mode === "reset_password" && "Enter the OTP code and choose your new password."}
            </CardDescription>
          </CardHeader>

          <form onSubmit={handleSubmit}>
            <CardContent className="space-y-3.5">
              {error && (
                <div className="p-3 rounded-lg text-xs flex items-center gap-2 bg-destructive/15 text-destructive border border-destructive/30">
                  <AlertCircle className="h-4 w-4 shrink-0" />
                  <span>{error}</span>
                </div>
              )}

              {successMsg && (
                <div className="p-3 rounded-lg text-xs flex items-center gap-2 bg-emerald-500/15 text-emerald-500 border border-emerald-500/30">
                  <CheckCircle2 className="h-4 w-4 shrink-0" />
                  <span>{successMsg}</span>
                </div>
              )}

              {sandboxOtp && mode === "verify_otp" && (
                <div className="p-2.5 rounded-lg text-xs bg-primary/10 border border-primary/30 flex items-center justify-between text-primary">
                  <span className="flex items-center gap-1.5 font-medium">
                    <Sparkles className="h-3.5 w-3.5" /> Verification code: <strong>{sandboxOtp}</strong>
                  </span>
                  <button
                    type="button"
                    onClick={() => setFormData({ ...formData, otp_code: sandboxOtp })}
                    className="underline text-[11px] font-semibold hover:opacity-80"
                  >
                    Apply
                  </button>
                </div>
              )}

              {(mode === "login" || mode === "register") && (
                <div className="space-y-1.5">
                  <label className="text-xs font-medium text-muted-foreground flex items-center gap-1.5">
                    <User className="h-3.5 w-3.5" /> Username or Email
                  </label>
                  <Input
                    type="text"
                    placeholder="tushar"
                    value={formData.username}
                    onChange={(e) => setFormData({ ...formData, username: e.target.value })}
                    required
                  />
                </div>
              )}

              {(mode === "register" || mode === "forgot_password" || (mode === "verify_otp" && !formData.email)) && (
                <div className="space-y-1.5">
                  <label className="text-xs font-medium text-muted-foreground flex items-center gap-1.5">
                    <Mail className="h-3.5 w-3.5" /> Email Address
                  </label>
                  <Input
                    type="email"
                    placeholder="user@gmail.com"
                    value={formData.email}
                    onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                    required
                  />
                </div>
              )}

              {(mode === "login" || mode === "register") && (
                <div className="space-y-1.5">
                  <div className="flex items-center justify-between">
                    <label className="text-xs font-medium text-muted-foreground flex items-center gap-1.5">
                      <Lock className="h-3.5 w-3.5" /> Password
                    </label>
                    {mode === "login" && (
                      <button
                        type="button"
                        onClick={() => handleModeChange("forgot_password")}
                        className="text-[11px] text-primary hover:underline"
                      >
                        Forgot?
                      </button>
                    )}
                  </div>
                  <div className="relative">
                    <Input
                      type={showPassword ? "text" : "password"}
                      placeholder="••••••••"
                      value={formData.password}
                      onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                      className="pr-10"
                      required
                    />
                    <button
                      type="button"
                      onClick={() => setShowPassword(!showPassword)}
                      className="absolute right-3 top-2.5 text-muted-foreground hover:text-foreground transition-colors"
                      tabIndex={-1}
                      aria-label={showPassword ? "Hide password" : "Show password"}
                    >
                      {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                    </button>
                  </div>
                </div>
              )}

              {(mode === "verify_otp" || mode === "reset_password") && (
                <div className="space-y-1.5">
                  <div className="flex items-center justify-between">
                    <label className="text-xs font-medium text-muted-foreground flex items-center gap-1.5">
                      <ShieldCheck className="h-3.5 w-3.5 text-primary" /> 6-Digit OTP Code
                    </label>
                    <button
                      type="button"
                      onClick={handleResendOtp}
                      className="text-[11px] text-primary hover:underline flex items-center gap-1"
                    >
                      <RotateCcw className="h-3 w-3" /> Resend
                    </button>
                  </div>
                  <Input
                    type="text"
                    maxLength={6}
                    placeholder="123456"
                    className="text-center font-mono text-xl tracking-[0.5em]"
                    value={formData.otp_code}
                    onChange={(e) => setFormData({ ...formData, otp_code: e.target.value })}
                    required
                  />
                </div>
              )}

              {mode === "reset_password" && (
                <div className="space-y-1.5">
                  <label className="text-xs font-medium text-muted-foreground flex items-center gap-1.5">
                    <KeyRound className="h-3.5 w-3.5" /> New Password
                  </label>
                  <div className="relative">
                    <Input
                      type={showNewPassword ? "text" : "password"}
                      placeholder="Enter at least 4 characters"
                      value={formData.new_password}
                      onChange={(e) => setFormData({ ...formData, new_password: e.target.value })}
                      className="pr-10"
                      required
                    />
                    <button
                      type="button"
                      onClick={() => setShowNewPassword(!showNewPassword)}
                      className="absolute right-3 top-2.5 text-muted-foreground hover:text-foreground transition-colors"
                      tabIndex={-1}
                      aria-label={showNewPassword ? "Hide new password" : "Show new password"}
                    >
                      {showNewPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                    </button>
                  </div>
                </div>
              )}
            </CardContent>

            <CardFooter className="flex flex-col gap-3 pt-2">
              <Button type="submit" disabled={isLoading} className="w-full gap-2">
                {isLoading ? (
                  <span>Processing...</span>
                ) : mode === "login" ? (
                  <>
                    <span>Sign In</span>
                    <ArrowRight className="h-4 w-4" />
                  </>
                ) : mode === "register" ? (
                  <>
                    <span>Create Account</span>
                    <ArrowRight className="h-4 w-4" />
                  </>
                ) : mode === "verify_otp" ? (
                  <span>Verify and Continue</span>
                ) : mode === "forgot_password" ? (
                  <span>Send Reset Code</span>
                ) : (
                  <span>Save New Password</span>
                )}
              </Button>

              <div className="text-xs text-center text-muted-foreground space-y-1">
                {mode === "login" ? (
                  <p>
                    Don&apos;t have an account?{" "}
                    <button
                      type="button"
                      onClick={() => handleModeChange("register")}
                      className="text-primary font-semibold hover:underline"
                    >
                      Sign Up
                    </button>
                  </p>
                ) : mode === "register" ? (
                  <p>
                    Already have an account?{" "}
                    <button
                      type="button"
                      onClick={() => handleModeChange("login")}
                      className="text-primary font-semibold hover:underline"
                    >
                      Sign In
                    </button>
                  </p>
                ) : (
                  <p>
                    Back to{" "}
                    <button
                      type="button"
                      onClick={() => handleModeChange("login")}
                      className="text-primary font-semibold hover:underline"
                    >
                      Sign In
                    </button>
                  </p>
                )}
              </div>
            </CardFooter>
          </form>
        </Card>
      </div>
    </div>
  );
}

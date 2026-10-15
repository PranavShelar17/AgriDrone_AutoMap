import React from "react";
import { Info, AlertTriangle, AlertCircle, CheckCircle2 } from "lucide-react";

interface AlertBannerProps {
  type: "info" | "warning" | "error" | "success";
  title?: string;
  message: string;
  actionText?: string;
  onAction?: () => void;
  className?: string;
}

export function AlertBanner({
  type,
  title,
  message,
  actionText,
  onAction,
  className = "",
}: AlertBannerProps) {
  const styles = {
    info: "bg-blue-50 border-blue-200 text-blue-900",
    warning: "bg-amber-50 border-amber-200 text-amber-900",
    error: "bg-rose-50 border-rose-200 text-rose-900",
    success: "bg-emerald-50 border-emerald-200 text-emerald-900",
  }[type];

  const Icon = {
    info: Info,
    warning: AlertTriangle,
    error: AlertCircle,
    success: CheckCircle2,
  }[type];

  const iconColor = {
    info: "text-blue-600",
    warning: "text-amber-600",
    error: "text-rose-600",
    success: "text-emerald-600",
  }[type];

  return (
    <div className={`p-4 rounded-xl border flex items-start gap-3.5 ${styles} ${className}`}>
      <Icon className={`w-5 h-5 shrink-0 mt-0.5 ${iconColor}`} />
      <div className="flex-1 text-sm">
        {title && <h4 className="font-semibold mb-0.5">{title}</h4>}
        <p className="leading-relaxed opacity-90">{message}</p>
        {actionText && (
          <button
            onClick={onAction}
            className="mt-2 text-xs font-semibold underline hover:no-underline"
          >
            {actionText}
          </button>
        )}
      </div>
    </div>
  );
}

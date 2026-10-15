import React from "react";
import { CheckCircle2, Clock, AlertCircle, Loader2, UploadCloud } from "lucide-react";

interface StatusBadgeProps {
  status: string;
}

export function StatusBadge({ status }: StatusBadgeProps) {
  const norm = (status || "").toUpperCase();

  if (norm === "DONE" || norm === "COMPLETED" || norm === "SUCCESS" || norm === "ELIGIBLE") {
    return (
      <span className="badge-done">
        <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
        {status}
      </span>
    );
  }

  if (norm === "PROCESSING" || norm === "RUNNING") {
    return (
      <span className="badge-processing">
        <Loader2 className="w-3.5 h-3.5 text-blue-600 animate-spin" />
        Processing
      </span>
    );
  }

  if (norm === "QUEUED" || norm === "READY" || norm === "DRAFT") {
    return (
      <span className="badge-queued">
        <Clock className="w-3.5 h-3.5 text-slate-500" />
        {status}
      </span>
    );
  }

  if (norm === "FAILED" || norm === "INVALID" || norm === "ERROR") {
    return (
      <span className="badge-failed">
        <AlertCircle className="w-3.5 h-3.5 text-rose-600" />
        {status}
      </span>
    );
  }

  return (
    <span className="badge-uploading">
      <UploadCloud className="w-3.5 h-3.5 text-amber-600" />
      {status || "Uploading"}
    </span>
  );
}

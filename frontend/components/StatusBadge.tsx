import React from "react";
import { CheckCircle2, Clock, AlertCircle, Loader2, UploadCloud, XCircle } from "lucide-react";

interface StatusBadgeProps {
  status: string;
}

export function StatusBadge({ status }: StatusBadgeProps) {
  const norm = (status || "").toUpperCase();

  if (norm === "DONE" || norm === "COMPLETED" || norm === "SUCCESS" || norm === "ELIGIBLE" || norm === "VALIDATED") {
    return (
      <span className="badge-done">
        <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
        {status}
      </span>
    );
  }

  if (
    norm === "PROCESSING" ||
    norm === "RUNNING" ||
    norm === "PREPARING" ||
    norm === "UPLOADING" ||
    norm === "FINALIZING" ||
    norm === "CANCEL_REQUESTED"
  ) {
    return (
      <span className="badge-processing">
        <Loader2 className="w-3.5 h-3.5 text-blue-600 animate-spin" />
        {status}
      </span>
    );
  }

  if (norm === "QUEUED" || norm === "SUBMITTED" || norm === "READY" || norm === "DRAFT") {
    return (
      <span className="badge-queued">
        <Clock className="w-3.5 h-3.5 text-slate-500" />
        {status}
      </span>
    );
  }

  if (norm === "FAILED" || norm === "INVALID" || norm === "ERROR" || norm === "REJECTED") {
    return (
      <span className="badge-failed">
        <AlertCircle className="w-3.5 h-3.5 text-rose-600" />
        {status}
      </span>
    );
  }

  if (norm === "CANCELLED" || norm === "CANCELED") {
    return (
      <span className="badge-failed bg-slate-100 text-slate-700 border-slate-300">
        <XCircle className="w-3.5 h-3.5 text-slate-500" />
        Cancelled
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

export function recLabel(value: string) {
  const map: Record<string, string> = {
    strong_hire: "Strong hire",
    interview: "Interview",
    maybe: "Maybe",
    reject: "Reject",
  };
  return map[value] || value || "Pending";
}

export function recClass(value: string) {
  if (value === "strong_hire") return "bg-emerald-50 text-emerald-700";
  if (value === "interview") return "bg-sky-50 text-sky-700";
  if (value === "maybe") return "bg-amber-50 text-amber-700";
  if (value === "reject") return "bg-rose-50 text-rose-700";
  return "bg-slate-100 text-slate-600";
}

export function statusClass(value: string) {
  if (value === "shortlisted") return "bg-teal-50 text-teal-700";
  if (value === "rejected") return "bg-rose-50 text-rose-700";
  if (value === "screened") return "bg-indigo-50 text-indigo-700";
  return "bg-slate-100 text-slate-600";
}

export function scoreColor(score: number | null) {
  if (score == null) return "text-slate-400";
  if (score >= 80) return "text-emerald-600";
  if (score >= 65) return "text-sky-600";
  if (score >= 45) return "text-amber-600";
  return "text-rose-600";
}

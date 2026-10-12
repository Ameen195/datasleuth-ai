
import { useMemo, useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import {
  Activity,
  AlertCircle,
  AlertTriangle,
  ArrowDownToLine,
  ArrowUpRight,
  BrainCircuit,
  CheckCircle2,
  ChevronRight,
  CircleHelp,
  Clock3,
  Database,
  FileSearch,
  FileText,
  FlaskConical,
  LayoutDashboard,
  LoaderCircle,
  Menu,
  Network,
  Plus,
  ScanSearch,
  Settings2,
  ShieldCheck,
  Sparkles,
  UploadCloud,
  X,
} from "lucide-react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

const API_URL = (
  import.meta.env.VITE_API_URL || "http://127.0.0.1:8000"
).replace(/\/+$/, "");

const navigation = [
  { label: "Overview", icon: LayoutDashboard },
  { label: "Investigations", icon: FileSearch },
  { label: "Datasets", icon: Database },
];

function getFindings(report) {
  if (Array.isArray(report?.findings)) {
    return report.findings;
  }

  if (Array.isArray(report?.incident_report?.findings)) {
    return report.incident_report.findings;
  }

  return [];
}

function MetricCard({ label, value, caption, icon: Icon, accent }) {
  return (
    <div className="rounded-2xl border border-slate-800/90 bg-[#101626] p-5 transition hover:border-slate-700">
      <div className="flex items-start justify-between">
        <p className="text-sm text-slate-400">{label}</p>

        <div
          className={`rounded-xl border border-slate-700/70 bg-slate-800/60 p-2 ${accent}`}
        >
          <Icon size={18} />
        </div>
      </div>

      <p className="mt-5 text-3xl font-semibold tracking-tight text-slate-100">
        {value}
      </p>

      <p className="mt-2 text-xs text-slate-500">{caption}</p>
    </div>
  );
}

function FilePicker({ label, description, file, onChange }) {
  return (
    <label className="group flex min-h-40 cursor-pointer flex-col items-center justify-center rounded-xl border border-dashed border-slate-700 bg-[#0b1120] p-5 text-center transition hover:border-indigo-400/70 hover:bg-indigo-500/[0.04]">
      <input
        type="file"
        accept=".csv,text/csv"
        className="sr-only"
        onChange={(event) => onChange(event.target.files?.[0] || null)}
      />

      <div className="mb-3 rounded-xl border border-slate-700 bg-slate-800/70 p-3 text-indigo-300 transition group-hover:border-indigo-400/50">
        <UploadCloud size={22} />
      </div>

      <p className="text-sm font-medium text-slate-200">{label}</p>

      <p className="mt-1 text-xs text-slate-500">{description}</p>

      <p className="mt-3 max-w-full truncate text-xs text-indigo-300">
        {file ? file.name : "Choose CSV file"}
      </p>
    </label>
  );
}

function SeverityBadge({ severity }) {
  const level = String(severity || "unknown").toLowerCase();

  const styles = {
    critical: "border-rose-500/20 bg-rose-500/10 text-rose-300",
    high: "border-red-500/20 bg-red-500/10 text-red-300",
    medium: "border-amber-500/20 bg-amber-500/10 text-amber-300",
    low: "border-sky-500/20 bg-sky-500/10 text-sky-300",
  };

  return (
    <span
      className={`inline-flex rounded-full border px-2.5 py-1 text-xs font-medium ${
        styles[level] ||
        "border-slate-700 bg-slate-800 text-slate-300"
      }`}
    >
      {level.charAt(0).toUpperCase() + level.slice(1)}
    </span>
  );
}

/**
 * Render Markdown without requiring the Tailwind Typography plugin.
 */
function MarkdownContent({ content }) {
  if (!content) return null;

  return (
    <div className="mt-5 space-y-4 break-words text-sm leading-7 text-slate-300 [&_h1]:text-xl [&_h1]:font-semibold [&_h1]:text-white [&_h2]:mt-6 [&_h2]:text-lg [&_h2]:font-semibold [&_h2]:text-slate-100 [&_h3]:mt-5 [&_h3]:font-semibold [&_h3]:text-slate-100 [&_p]:my-3 [&_strong]:font-semibold [&_strong]:text-slate-100 [&_ul]:my-3 [&_ul]:list-disc [&_ul]:space-y-2 [&_ul]:pl-6 [&_ol]:my-3 [&_ol]:list-decimal [&_ol]:space-y-2 [&_ol]:pl-6 [&_li]:pl-1 [&_code]:rounded [&_code]:bg-slate-800 [&_code]:px-1.5 [&_code]:py-0.5 [&_code]:text-indigo-300 [&_blockquote]:border-l-2 [&_blockquote]:border-indigo-400 [&_blockquote]:pl-4 [&_blockquote]:text-slate-400 [&_a]:text-indigo-300 [&_a]:underline">
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        components={{
          a: ({ children, ...props }) => (
            <a {...props} target="_blank" rel="noreferrer">
              {children}
            </a>
          ),
        }}
      >
        {content}
      </ReactMarkdown>
    </div>
  );
}

function App() {
  const [baseline, setBaseline] = useState(null);
  const [current, setCurrent] = useState(null);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [activeNav, setActiveNav] = useState("Overview");
  const [sidebarOpen, setSidebarOpen] = useState(false);

  const report = result?.incident_report || {};
  const findings = getFindings(report);
  const summary = result?.evidence_summary || "";
  const diagnosis = result?.diagnosis || "";

  const severityData = useMemo(() => {
    const counts = {
      Critical: 0,
      High: 0,
      Medium: 0,
      Low: 0,
    };

    findings.forEach((finding) => {
      const level = String(finding.severity || "").toLowerCase();

      const matchingSeverity = Object.keys(counts).find(
        (severity) => severity.toLowerCase() === level
      );

      if (matchingSeverity) {
        counts[matchingSeverity] += 1;
      }
    });

    return Object.entries(counts).map(([severity, count]) => ({
      severity,
      count,
    }));
  }, [findings]);

  const rowCount =
    report.current_rows ??
    report.current_row_count ??
    report.row_counts?.current ??
    "—";

  const incidentId = report.incident_id || "Pending investigation";

  const severityCount = findings.filter((finding) =>
    ["critical", "high"].includes(
      String(finding.severity || "").toLowerCase()
    )
  ).length;

  async function runInvestigation(event) {
    event.preventDefault();
    setError("");
    setResult(null);

    if (!baseline || !current) {
      setError("Please select both the baseline and current CSV files.");
      return;
    }

    if (
      !baseline.name.toLowerCase().endsWith(".csv") ||
      !current.name.toLowerCase().endsWith(".csv")
    ) {
      setError("Both uploads must be CSV files.");
      return;
    }

    if (baseline.size === 0 || current.size === 0) {
      setError("The selected CSV files cannot be empty.");
      return;
    }

    const maxSize = 20 * 1024 * 1024;

    if (baseline.size > maxSize || current.size > maxSize) {
      setError("Each CSV file must be 20 MB or smaller.");
      return;
    }

    const formData = new FormData();
    formData.append("baseline", baseline);
    formData.append("current", current);

    setLoading(true);

    try {
      const response = await fetch(
        `${API_URL}/api/v1/investigations`,
        {
          method: "POST",
          body: formData,
        }
      );

      const data = await response.json().catch(() => ({}));

      if (!response.ok) {
        const detail = data.detail;

        throw new Error(
          typeof detail === "string"
            ? detail
            : `The API returned HTTP ${response.status}.`
        );
      }

      if (!data || typeof data !== "object") {
        throw new Error("The API returned an invalid response.");
      }

      setResult(data);
      setActiveNav("Overview");
    } catch (err) {
      const message = err instanceof Error ? err.message : String(err);

      if (
        message.toLowerCase().includes("failed to fetch") ||
        message.toLowerCase().includes("networkerror")
      ) {
        setError(
          `Cannot reach the API at ${API_URL}. Ensure FastAPI is running and CORS allows this frontend origin.`
        );
      } else {
        setError(message);
      }
    } finally {
      setLoading(false);
    }
  }

  function resetInvestigation() {
    setBaseline(null);
    setCurrent(null);
    setResult(null);
    setError("");
    setActiveNav("Overview");
  }

  function downloadReport() {
    if (!result) return;

    const blob = new Blob(
      [JSON.stringify(result, null, 2)],
      { type: "application/json" }
    );

    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");

    link.href = url;
    link.download = "datasleuth-incident-report.json";

    document.body.appendChild(link);
    link.click();
    link.remove();

    URL.revokeObjectURL(url);
  }

  return (
    <div className="min-h-screen bg-[#080b14] text-slate-100">
      {sidebarOpen && (
        <button
          aria-label="Close navigation overlay"
          onClick={() => setSidebarOpen(false)}
          className="fixed inset-0 z-30 bg-black/60 lg:hidden"
        />
      )}

      <aside
        className={`fixed inset-y-0 left-0 z-40 flex w-64 flex-col border-r border-slate-800/80 bg-[#0b101d] transition-transform lg:translate-x-0 ${
          sidebarOpen ? "translate-x-0" : "-translate-x-full"
        }`}
      >
        <div className="flex h-[76px] items-center gap-3 border-b border-slate-800/80 px-5">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-indigo-500 text-white shadow-lg shadow-indigo-500/20">
            <ScanSearch size={22} />
          </div>

          <div>
            <h1 className="text-base font-semibold tracking-tight">
              DataSleuth <span className="text-indigo-400">AI</span>
            </h1>
            <p className="mt-0.5 text-[10px] tracking-[0.16em] text-slate-500">
              DATA INTELLIGENCE
            </p>
          </div>

          <button
            onClick={() => setSidebarOpen(false)}
            className="ml-auto text-slate-500 lg:hidden"
            aria-label="Close sidebar"
          >
            <X size={19} />
          </button>
        </div>

        <div className="px-4 pt-7">
          <p className="mb-3 px-3 text-[10px] font-semibold tracking-[0.18em] text-slate-600">
            WORKSPACE
          </p>

          <nav className="space-y-1">
            {navigation.map(({ label, icon: Icon }) => (
              <button
                key={label}
                onClick={() => {
                  setActiveNav(label);
                  setSidebarOpen(false);
                }}
                className={`flex w-full items-center gap-3 rounded-lg px-3 py-2.5 text-sm transition ${
                  activeNav === label
                    ? "border border-indigo-500/15 bg-indigo-500/10 text-indigo-300"
                    : "text-slate-400 hover:bg-slate-800/60 hover:text-slate-200"
                }`}
              >
                <Icon size={18} />
                {label}

                {label === "Investigations" && result && (
                  <span className="ml-auto rounded-md bg-slate-800 px-2 py-0.5 text-xs text-slate-400">
                    1
                  </span>
                )}
              </button>
            ))}
          </nav>
        </div>

        <div className="mt-8 px-4">
          <p className="mb-3 px-3 text-[10px] font-semibold tracking-[0.18em] text-slate-600">
            INTELLIGENCE
          </p>

          <div className="space-y-1">
            <button
              onClick={() => {
                setActiveNav("AI diagnosis");
                document
                  .getElementById("ai-diagnosis")
                  ?.scrollIntoView({ behavior: "smooth" });
              }}
              className="flex w-full items-center gap-3 rounded-lg px-3 py-2.5 text-left text-sm text-slate-400 hover:bg-slate-800/60 hover:text-slate-200"
            >
              <BrainCircuit size={18} />
              AI diagnosis
            </button>

            <button
              onClick={() => {
                setActiveNav("Evidence analysis");
                document
                  .getElementById("evidence-summary")
                  ?.scrollIntoView({ behavior: "smooth" });
              }}
              className="flex w-full items-center gap-3 rounded-lg px-3 py-2.5 text-left text-sm text-slate-400 hover:bg-slate-800/60 hover:text-slate-200"
            >
              <Network size={18} />
              Evidence analysis
            </button>
          </div>
        </div>

        <div className="mt-auto p-4">
          <div className="rounded-xl border border-slate-800 bg-[#101626] p-4">
            <div className="flex items-center gap-2 text-xs font-medium text-slate-300">
              <ShieldCheck size={16} className="text-emerald-400" />
              Investigation engine
            </div>

            <p className="mt-2 text-xs leading-5 text-slate-500">
              Deterministic checks with evidence-grounded AI analysis.
            </p>

            <div className="mt-3 flex items-center gap-2 text-[11px] text-slate-400">
              <span className="h-1.5 w-1.5 rounded-full bg-emerald-400" />
              API endpoint configured
            </div>
          </div>

          <div className="mt-4 flex items-center gap-3 px-2">
            <div className="flex h-9 w-9 items-center justify-center rounded-full border border-slate-700 bg-slate-800 text-xs font-semibold text-indigo-300">
              DS
            </div>

            <div className="min-w-0 flex-1">
              <p className="text-xs font-medium text-slate-300">
                Data Analyst
              </p>
              <p className="mt-1 text-[10px] text-slate-500">
                Personal workspace
              </p>
            </div>

            <Settings2 size={16} className="text-slate-600" />
          </div>
        </div>
      </aside>

      <main className="min-h-screen lg:pl-64">
        <header className="sticky top-0 z-20 flex h-[76px] items-center justify-between border-b border-slate-800/80 bg-[#080b14]/90 px-5 backdrop-blur-xl sm:px-8">
          <div className="flex items-center gap-3">
            <button
              onClick={() => setSidebarOpen(true)}
              className="text-slate-400 lg:hidden"
              aria-label="Open navigation"
            >
              <Menu size={22} />
            </button>

            <div>
              <p className="text-sm font-medium text-slate-200">
                {activeNav}
              </p>
              <p className="mt-1 text-xs text-slate-500">
                Data quality intelligence workspace
              </p>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <span className="hidden items-center gap-2 rounded-full border border-slate-800 bg-slate-900/60 px-3 py-2 text-xs text-slate-400 sm:flex">
              <span className="h-1.5 w-1.5 rounded-full bg-indigo-400" />
              AI-assisted analysis
            </span>

            <button
              onClick={resetInvestigation}
              className="flex items-center gap-2 rounded-lg bg-indigo-500 px-3 py-2.5 text-xs font-semibold text-white transition hover:bg-indigo-400 sm:px-4 sm:text-sm"
            >
              <Plus size={16} />
              <span className="hidden sm:inline">New investigation</span>
              <span className="sm:hidden">New</span>
            </button>
          </div>
        </header>

        <div className="mx-auto max-w-[1500px] space-y-8 p-5 sm:p-8">
          <section className="relative overflow-hidden rounded-2xl border border-slate-800 bg-gradient-to-br from-[#121a30] via-[#0f1526] to-[#0b101d] p-6 sm:p-8">
            <div className="pointer-events-none absolute -right-20 -top-28 h-72 w-72 rounded-full bg-indigo-500/[0.09] blur-3xl" />

            <div className="relative flex flex-col justify-between gap-5 md:flex-row md:items-center">
              <div>
                <div className="mb-4 inline-flex items-center gap-2 rounded-full border border-indigo-400/20 bg-indigo-400/[0.07] px-3 py-1.5 text-[10px] font-semibold tracking-[0.16em] text-indigo-300">
                  <Sparkles size={13} />
                  INTELLIGENT DATA INVESTIGATION
                </div>

                <h2 className="text-2xl font-semibold tracking-tight text-white sm:text-3xl">
                  Find what broke.
                  <span className="text-indigo-400">
                    {" "}Understand why.
                  </span>
                </h2>

                <p className="mt-3 max-w-xl text-sm leading-6 text-slate-400">
                  Compare datasets, uncover data-quality anomalies, and
                  investigate incidents with evidence-grounded AI.
                </p>
              </div>

              <div className="flex shrink-0 items-center gap-3 rounded-xl border border-slate-700/70 bg-black/15 p-4">
                <div className="rounded-xl bg-indigo-500/10 p-3 text-indigo-300">
                  <FlaskConical size={23} />
                </div>

                <div>
                  <p className="text-xs text-slate-400">
                    Investigation status
                  </p>
                  <p className="mt-1 text-sm font-medium text-slate-200">
                    {loading
                      ? "Analyzing datasets…"
                      : result
                        ? "Completed"
                        : "Ready to analyze"}
                  </p>
                </div>
              </div>
            </div>
          </section>

          <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
            <MetricCard
              label="Findings detected"
              value={result ? findings.length : "—"}
              caption={
                result
                  ? "Across the current investigation"
                  : "Run an investigation to begin"
              }
              icon={ScanSearch}
              accent="text-indigo-300"
            />

            <MetricCard
              label="High-priority findings"
              value={result ? severityCount : "—"}
              caption="Critical and high severity"
              icon={AlertTriangle}
              accent="text-rose-300"
            />

            <MetricCard
              label="Current dataset rows"
              value={rowCount}
              caption="Rows in the uploaded current dataset"
              icon={Database}
              accent="text-sky-300"
            />

            <MetricCard
              label="AI tool calls"
              value={result ? (result.tool_calls_used ?? 0) : "—"}
              caption="Calls made during the investigation"
              icon={BrainCircuit}
              accent="text-emerald-300"
            />
          </section>

          <section className="grid items-start gap-6 xl:grid-cols-[1.1fr_0.9fr]">
            <div className="rounded-2xl border border-slate-800 bg-[#0e1422] p-5 sm:p-6">
              <div className="mb-5 flex items-start justify-between gap-4">
                <div>
                  <h3 className="text-base font-semibold text-slate-100">
                    New investigation
                  </h3>
                  <p className="mt-1 text-xs leading-5 text-slate-500">
                    Upload two CSV snapshots to compare data quality.
                  </p>
                </div>

                <div className="rounded-lg border border-slate-800 bg-slate-900 p-2 text-slate-400">
                  <FileSearch size={18} />
                </div>
              </div>

              <form onSubmit={runInvestigation}>
                <div className="grid gap-3 sm:grid-cols-2">
                  <FilePicker
                    label="Baseline dataset"
                    description="Your reference or previous snapshot"
                    file={baseline}
                    onChange={setBaseline}
                  />

                  <FilePicker
                    label="Current dataset"
                    description="The dataset you want to investigate"
                    file={current}
                    onChange={setCurrent}
                  />
                </div>

                <div className="mt-4 flex items-start gap-2 rounded-lg border border-slate-800/80 bg-[#0a0f1a] p-3">
                  <CircleHelp
                    size={15}
                    className="mt-0.5 shrink-0 text-slate-500"
                  />
                  <p className="text-xs leading-5 text-slate-500">
                    CSV files only. Each file must be 20 MB or smaller.
                    Uploaded files are processed by your configured backend.
                  </p>
                </div>

                {error && (
                  <div
                    role="alert"
                    className="mt-4 flex gap-2 rounded-lg border border-rose-500/20 bg-rose-500/[0.07] p-3 text-sm text-rose-300"
                  >
                    <AlertCircle
                      size={17}
                      className="mt-0.5 shrink-0"
                    />
                    <span>{error}</span>
                  </div>
                )}

                <button
                  type="submit"
                  disabled={loading}
                  className="mt-5 flex w-full items-center justify-center gap-2 rounded-xl bg-indigo-500 px-4 py-3 text-sm font-semibold text-white transition hover:bg-indigo-400 disabled:cursor-not-allowed disabled:opacity-60"
                >
                  {loading ? (
                    <>
                      <LoaderCircle size={18} className="animate-spin" />
                      Investigating datasets…
                    </>
                  ) : (
                    <>
                      <Sparkles size={17} />
                      Run investigation
                      <ChevronRight size={17} />
                    </>
                  )}
                </button>
              </form>
            </div>

            <div className="rounded-2xl border border-slate-800 bg-[#0e1422] p-5 sm:p-6">
              <div className="flex items-start justify-between">
                <div>
                  <h3 className="text-base font-semibold text-slate-100">
                    Severity distribution
                  </h3>
                  <p className="mt-1 text-xs text-slate-500">
                    Findings grouped by detector severity
                  </p>
                </div>
                <Activity size={19} className="text-indigo-300" />
              </div>

              {result && findings.length > 0 ? (
                <div className="mt-5 h-56 w-full">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart
                      data={severityData}
                      margin={{
                        top: 8,
                        right: 4,
                        left: -22,
                        bottom: 0,
                      }}
                    >
                      <CartesianGrid
                        stroke="#202b3e"
                        strokeDasharray="3 3"
                        vertical={false}
                      />
                      <XAxis
                        dataKey="severity"
                        tick={{ fill: "#94a3b8", fontSize: 11 }}
                        axisLine={false}
                        tickLine={false}
                      />
                      <YAxis
                        allowDecimals={false}
                        tick={{ fill: "#64748b", fontSize: 11 }}
                        axisLine={false}
                        tickLine={false}
                      />
                      <Tooltip
                        contentStyle={{
                          background: "#111827",
                          border: "1px solid #334155",
                          borderRadius: 10,
                          color: "#e2e8f0",
                        }}
                        cursor={{ fill: "rgba(99,102,241,0.07)" }}
                      />
                      <Bar
                        dataKey="count"
                        name="Findings"
                        fill="#818cf8"
                        radius={[5, 5, 0, 0]}
                        maxBarSize={38}
                      />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              ) : (
                <div className="flex h-56 flex-col items-center justify-center text-center">
                  <div className="rounded-2xl border border-slate-800 bg-slate-900/70 p-4 text-slate-500">
                    <Activity size={25} />
                  </div>

                  <p className="mt-4 text-sm font-medium text-slate-300">
                    No investigation data yet
                  </p>
                  <p className="mt-1 text-xs text-slate-500">
                    Your chart will appear after the first analysis.
                  </p>
                </div>
              )}
            </div>
          </section>

          <section className="overflow-hidden rounded-2xl border border-slate-800 bg-[#0e1422]">
            <div className="flex flex-col justify-between gap-4 border-b border-slate-800 p-5 sm:flex-row sm:items-center sm:px-6">
              <div>
                <div className="flex items-center gap-2">
                  <h3 className="text-base font-semibold text-slate-100">
                    Investigation findings
                  </h3>

                  {result && (
                    <span className="rounded-md border border-slate-700 bg-slate-800/70 px-2 py-0.5 text-xs text-slate-300">
                      {findings.length}
                    </span>
                  )}
                </div>

                <p className="mt-1 text-xs text-slate-500">
                  Deterministic detector results and supporting evidence
                </p>
              </div>

              {result && (
                <button
                  type="button"
                  onClick={downloadReport}
                  className="flex items-center justify-center gap-2 rounded-lg border border-slate-700 bg-slate-900 px-3 py-2 text-xs font-medium text-slate-300 transition hover:border-indigo-400/50 hover:text-white"
                >
                  <ArrowDownToLine size={15} />
                  Export JSON
                </button>
              )}
            </div>

            {!result ? (
              <div className="flex flex-col items-center px-5 py-14 text-center">
                <div className="rounded-2xl border border-slate-800 bg-slate-900/70 p-4 text-slate-500">
                  <FileText size={25} />
                </div>

                <p className="mt-4 text-sm font-medium text-slate-300">
                  Your findings will appear here
                </p>
                <p className="mt-2 max-w-sm text-xs leading-5 text-slate-500">
                  Upload your baseline and current datasets, then run an
                  investigation to view confirmed anomalies and evidence.
                </p>
              </div>
            ) : findings.length === 0 ? (
              <div className="flex items-center gap-3 p-6 text-sm text-emerald-300">
                <CheckCircle2 size={20} />
                No findings were returned in the report.
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full min-w-[760px] text-left">
                  <thead className="bg-[#0a0f1b] text-[10px] uppercase tracking-[0.12em] text-slate-500">
                    <tr>
                      <th className="px-6 py-4 font-medium">Anomaly</th>
                      <th className="px-4 py-4 font-medium">Column / key</th>
                      <th className="px-4 py-4 font-medium">Severity</th>
                      <th className="px-6 py-4 font-medium">Evidence</th>
                    </tr>
                  </thead>

                  <tbody className="divide-y divide-slate-800/80">
                    {findings.map((finding, index) => (
                      <tr
                        key={`${finding.anomaly_type || "finding"}-${finding.column || finding.key_column || index}-${index}`}
                        className="transition hover:bg-slate-800/20"
                      >
                        <td className="px-6 py-4">
                          <p className="text-sm font-medium capitalize text-slate-200">
                            {String(
                              finding.anomaly_type || "Finding"
                            ).replace(/_/g, " ")}
                          </p>
                        </td>

                        <td className="px-4 py-4 font-mono text-xs text-indigo-300">
                          {finding.column || finding.key_column || "—"}
                        </td>

                        <td className="px-4 py-4">
                          <SeverityBadge severity={finding.severity} />
                        </td>

                        <td className="max-w-sm px-6 py-4 text-xs leading-5 text-slate-400">
                          {finding.evidence ||
                            finding.description ||
                            finding.details ||
                            (finding.anomaly_type === "duplicate_keys"
                              ? `Duplicate key detected in: ${
                                  finding.key_columns?.join(", ") ||
                                  finding.key_column ||
                                  "configured key columns"
                                }.`
                              : finding.anomaly_type === "null_values"
                                ? `Missing or null values detected in column: ${
                                    finding.column || "unknown column"
                                  }.`
                                : finding.anomaly_type === "invalid_numeric_values"
                                  ? `Numeric constraint violation detected in column: ${
                                      finding.column || "unknown column"
                                    }.`
                                  : "See the AI diagnosis and evidence summary for additional context.")}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </section>

          <section className="grid gap-6 xl:grid-cols-2">
            <div
              id="ai-diagnosis"
              className="scroll-mt-24 rounded-2xl border border-slate-800 bg-[#0e1422] p-5 sm:p-6"
            >
              <div className="flex items-center gap-3">
                <div className="rounded-xl border border-indigo-500/20 bg-indigo-500/10 p-2.5 text-indigo-300">
                  <BrainCircuit size={20} />
                </div>

                <div>
                  <h3 className="text-base font-semibold text-slate-100">
                    AI diagnosis
                  </h3>
                  <p className="mt-1 text-xs text-slate-500">
                    Evidence-grounded investigation analysis
                  </p>
                </div>
              </div>

              {diagnosis ? (
                <MarkdownContent content={diagnosis} />
              ) : (
                <p className="mt-5 text-sm leading-6 text-slate-500">
                  The AI diagnosis will be displayed here after an
                  investigation.
                </p>
              )}
            </div>

            <div
              id="evidence-summary"
              className="scroll-mt-24 rounded-2xl border border-slate-800 bg-[#0e1422] p-5 sm:p-6"
            >
              <div className="flex items-center gap-3">
                <div className="rounded-xl border border-emerald-500/20 bg-emerald-500/10 p-2.5 text-emerald-300">
                  <ShieldCheck size={20} />
                </div>

                <div>
                  <h3 className="text-base font-semibold text-slate-100">
                    Evidence summary
                  </h3>
                  <p className="mt-1 text-xs text-slate-500">
                    Confirmed findings, hypotheses, and next steps
                  </p>
                </div>
              </div>

              {summary ? (
                <MarkdownContent content={summary} />
              ) : (
                <p className="mt-5 text-sm leading-6 text-slate-500">
                  The evidence summary will be displayed here after an
                  investigation.
                </p>
              )}
            </div>
          </section>

          <footer className="flex flex-col justify-between gap-2 border-t border-slate-800/80 py-5 text-xs text-slate-600 sm:flex-row sm:items-center">
            <p>DataSleuth AI · Data incident intelligence</p>

            <p className="flex items-center gap-2">
              <Clock3 size={13} />
              {result
                ? `Incident: ${incidentId}`
                : "Ready for your first investigation"}
              <ArrowUpRight size={13} />
            </p>
          </footer>
        </div>
      </main>
    </div>
  );
}

export default App;

type Props = {
  title: string;
  value: string;
  detail?: string;
};

export function KpiCard({ title, value, detail }: Props) {
  return (
    <div className="panel" style={{ padding: "1rem", minHeight: 110 }}>
      <small style={{ color: "var(--muted)", display: "block", marginBottom: 8 }}>{title}</small>
      <strong style={{ fontSize: "1.5rem", display: "block", marginBottom: 6 }}>{value}</strong>
      {detail ? <small style={{ color: "var(--muted)" }}>{detail}</small> : null}
    </div>
  );
}

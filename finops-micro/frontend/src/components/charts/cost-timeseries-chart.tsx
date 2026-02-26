"use client";

import { Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

type Props = {
  points: Array<{ date: string; total: number }>;
};

export function CostTimeseriesChart({ points }: Props) {
  return (
    <div className="panel" style={{ width: "100%", height: 340, padding: "1rem" }}>
      <h3 style={{ marginTop: 0 }}>Série diária</h3>
      <ResponsiveContainer width="100%" height="85%">
        <LineChart data={points}>
          <XAxis dataKey="date" />
          <YAxis />
          <Tooltip />
          <Line type="monotone" dataKey="total" stroke="#0f766e" strokeWidth={2.4} dot={false} />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}

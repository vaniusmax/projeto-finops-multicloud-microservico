import { z } from "zod";

export const summarySchema = z.object({
  totalWeek: z.number(),
  deltaWeek: z.number(),
  avgDaily: z.number(),
  peakDay: z.object({ date: z.string(), amount: z.number() }),
  monthTotal: z.number(),
  yearTotal: z.number(),
  budgetMonth: z.number().nullish(),
  budgetYear: z.number().nullish(),
  usdRate: z.number().nullish(),
});

export const dailyItemSchema = z.object({
  date: z.string(),
  total: z.number(),
  byService: z.record(z.number()).optional(),
});

export const topItemSchema = z.object({
  serviceName: z.string().nullish(),
  linkedAccount: z.string().nullish(),
  total: z.number(),
  sharePct: z.number(),
  delta: z.number(),
  deltaPct: z.number(),
});

export const filtersSchema = z.object({
  services: z.array(z.string()),
  accounts: z.array(z.string()),
});

export const aiInsightSchema = z.object({
  answerMarkdown: z.string(),
  highlights: z.array(z.string()),
  suggestedActions: z.array(z.string()),
});

export const analyticsInsightSchema = z.object({
  mode: z.string(),
  summary: z.string(),
  drivers: z.array(z.string()),
  risks: z.array(z.string()),
  actions: z.array(
    z.object({
      title: z.string(),
      owner: z.string(),
      priority: z.string(),
      rationale: z.string(),
    }),
  ),
  suggestedQuestions: z.array(z.string()),
  evidence: z.object({
    topServices: z.array(z.string()),
    topAccounts: z.array(z.string()),
    peakDay: z.string().nullish(),
    totalPeriod: z.number(),
    deltaPeriodPct: z.number(),
  }),
});

export const costExplorerSnapshotSchema = z.object({
  totalPeriod: z.number(),
  deltaPeriodPct: z.number(),
  top1SharePct: z.number(),
  top3SharePct: z.number(),
  peakDay: z.object({ date: z.string(), amount: z.number() }),
  largestService: z
    .object({
      label: z.string(),
      value: z.number(),
      sharePct: z.number(),
      deltaPct: z.number(),
    })
    .nullish(),
  largestAccount: z
    .object({
      label: z.string(),
      value: z.number(),
      sharePct: z.number(),
      deltaPct: z.number(),
    })
    .nullish(),
});

export const costExplorerBreakdownSchema = z.array(
  z.object({
    key: z.string(),
    label: z.string(),
    total: z.number(),
    sharePct: z.number(),
    delta: z.number(),
    deltaPct: z.number(),
    contributionPct: z.number(),
  }),
);

export const costExplorerTrendSchema = z.array(
  z.object({
    date: z.string(),
    total: z.number(),
    selected: z.number(),
    others: z.number(),
  }),
);

export const costExplorerInsightSchema = z.object({
  mode: z.string(),
  summary: z.string(),
  drivers: z.array(z.string()),
  risks: z.array(z.string()),
  actions: z.array(
    z.object({
      title: z.string(),
      owner: z.string(),
      priority: z.string(),
      rationale: z.string(),
    }),
  ),
  suggestedQuestions: z.array(z.string()),
  nextDrilldowns: z.array(
    z.object({
      dimension: z.string(),
      value: z.string(),
      reason: z.string(),
    }),
  ),
  evidence: z.object({
    groupBy: z.string(),
    selectedItem: z.string().nullish(),
    totalPeriod: z.number(),
    deltaPeriodPct: z.number(),
    peakDay: z.string().nullish(),
    topBreakdown: z.array(z.string()),
    topServices: z.array(z.string()),
    topAccounts: z.array(z.string()),
  }),
});

export const dailySchema = z.array(dailyItemSchema);
export const topServicesSchema = z.array(
  topItemSchema.transform((item) => ({
    ...item,
    serviceName: item.serviceName ?? "N/A",
  })),
);
export const topAccountsSchema = z.array(
  topItemSchema.transform((item) => ({
    ...item,
    linkedAccount: item.linkedAccount ?? "N/A",
  })),
);

export type SummaryResponse = z.infer<typeof summarySchema>;
export type DailyResponse = z.infer<typeof dailySchema>;
export type TopServicesResponse = z.infer<typeof topServicesSchema>;
export type TopAccountsResponse = z.infer<typeof topAccountsSchema>;
export type FiltersResponse = z.infer<typeof filtersSchema>;
export type AiInsightResponse = z.infer<typeof aiInsightSchema>;
export type AnalyticsInsightResponse = z.infer<typeof analyticsInsightSchema>;
export type CostExplorerSnapshotResponse = z.infer<typeof costExplorerSnapshotSchema>;
export type CostExplorerBreakdownResponse = z.infer<typeof costExplorerBreakdownSchema>;
export type CostExplorerTrendResponse = z.infer<typeof costExplorerTrendSchema>;
export type CostExplorerInsightResponse = z.infer<typeof costExplorerInsightSchema>;

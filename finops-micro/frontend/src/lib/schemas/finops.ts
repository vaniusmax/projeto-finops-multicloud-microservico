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

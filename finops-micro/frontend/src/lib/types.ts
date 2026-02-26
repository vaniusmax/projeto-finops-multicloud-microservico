export type TopItem = {
  key: string;
  name: string;
  total: number;
};

export type SummaryResponse = {
  total_current: number;
  total_previous: number;
  delta: {
    absolute: number;
    percent: number | null;
  };
  top_services: TopItem[];
  top_scopes: TopItem[];
};

export type TimeseriesResponse = {
  granularity: string;
  points: Array<{
    date: string;
    total: number;
  }>;
};

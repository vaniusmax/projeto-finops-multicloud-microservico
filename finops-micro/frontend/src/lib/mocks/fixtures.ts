import type { AiInsightResponse, DailyResponse, FiltersResponse, SummaryResponse, TopAccountsResponse, TopServicesResponse } from "@/lib/schemas/finops";

export const mockSummary: SummaryResponse = {
  totalWeek: 19290,
  deltaWeek: -3.4,
  avgDaily: 2755,
  peakDay: { date: "2026-02-21", amount: 3961 },
  monthTotal: 97690,
  yearTotal: 217130,
  budgetMonth: 138530,
  budgetYear: 1660000,
  usdRate: 5.1394,
};

export const mockDaily: DailyResponse = [
  {
    date: "2026-02-16",
    total: 2550,
    byService: {
      "Amazon Elastic Compute Cloud - Compute": 480,
      "Amazon Relational Database Service": 465,
      "Amazon Simple Storage Service": 372,
      "Amazon Virtual Private Cloud": 330,
      "EC2 - Other": 318,
      "AWS Glue": 216,
      "Amazon Redshift": 171,
      AmazonCloudWatch: 96,
      "Amazon Elastic Load Balancing": 72,
      "Amazon Cognito": 54,
      Others: 180,
    },
  },
  {
    date: "2026-02-17",
    total: 2480,
    byService: {
      "Amazon Elastic Compute Cloud - Compute": 480,
      "Amazon Relational Database Service": 465,
      "Amazon Simple Storage Service": 372,
      "Amazon Virtual Private Cloud": 330,
      "EC2 - Other": 318,
      "AWS Glue": 216,
      "Amazon Redshift": 171,
      AmazonCloudWatch: 96,
      "Amazon Elastic Load Balancing": 72,
      "Amazon Cognito": 48,
      Others: 192,
    },
  },
  {
    date: "2026-02-18",
    total: 2750,
    byService: {
      "Amazon Elastic Compute Cloud - Compute": 482,
      "Amazon Relational Database Service": 466,
      "Amazon Simple Storage Service": 372,
      "Amazon Virtual Private Cloud": 331,
      "EC2 - Other": 319,
      "AWS Glue": 219,
      "Amazon Redshift": 172,
      AmazonCloudWatch: 102,
      "Amazon Elastic Load Balancing": 78,
      "Amazon Cognito": 84,
      Others: 125,
    },
  },
  {
    date: "2026-02-19",
    total: 2910,
    byService: {
      "Amazon Elastic Compute Cloud - Compute": 483,
      "Amazon Relational Database Service": 466,
      "Amazon Simple Storage Service": 344,
      "Amazon Virtual Private Cloud": 330,
      "EC2 - Other": 318,
      "AWS Glue": 219,
      "Amazon Redshift": 172,
      AmazonCloudWatch: 144,
      "Amazon Elastic Load Balancing": 90,
      "Amazon Cognito": 90,
      Others: 254,
    },
  },
  {
    date: "2026-02-20",
    total: 2870,
    byService: {
      "Amazon Elastic Compute Cloud - Compute": 505,
      "Amazon Relational Database Service": 466,
      "Amazon Simple Storage Service": 340,
      "Amazon Virtual Private Cloud": 329,
      "EC2 - Other": 315,
      "AWS Glue": 215,
      "Amazon Redshift": 170,
      AmazonCloudWatch: 150,
      "Amazon Elastic Load Balancing": 86,
      "Amazon Cognito": 74,
      Others: 220,
    },
  },
  {
    date: "2026-02-21",
    total: 3961,
    byService: {
      "Amazon Elastic Compute Cloud - Compute": 575,
      "Amazon Relational Database Service": 466,
      "Amazon Simple Storage Service": 340,
      "Amazon Virtual Private Cloud": 235,
      "EC2 - Other": 236,
      "AWS Glue": 190,
      "Amazon Redshift": 170,
      AmazonCloudWatch: 100,
      "Amazon Elastic Load Balancing": 60,
      "Amazon Cognito": 40,
      Others: 1549,
    },
  },
  {
    date: "2026-02-22",
    total: 1769,
    byService: {
      "Amazon Elastic Compute Cloud - Compute": 575,
      "Amazon Relational Database Service": 466,
      "Amazon Simple Storage Service": 336,
      "Amazon Virtual Private Cloud": 235,
      "EC2 - Other": 236,
      "AWS Glue": 190,
      "Amazon Redshift": 205,
      AmazonCloudWatch: 72,
      "Amazon Elastic Load Balancing": 30,
      "Amazon Cognito": 20,
      Others: 140,
    },
  },
];

export const mockTopServices: TopServicesResponse = [
  { serviceName: "Amazon Elastic Compute Cloud - Compute", total: 3564.98, sharePct: 18.5, delta: 210.11, deltaPct: 6.3 },
  { serviceName: "Amazon Relational Database Service", total: 3214.94, sharePct: 16.7, delta: 132.22, deltaPct: 4.3 },
  { serviceName: "Amazon Simple Storage Service", total: 2455.88, sharePct: 12.7, delta: -40.2, deltaPct: -1.6 },
  { serviceName: "Amazon Virtual Private Cloud", total: 2263.32, sharePct: 11.7, delta: 70.1, deltaPct: 3.1 },
  { serviceName: "EC2 - Other", total: 2109.35, sharePct: 10.9, delta: 62.2, deltaPct: 3.0 },
  { serviceName: "AWS Glue", total: 1516, sharePct: 7.9, delta: 76.1, deltaPct: 5.2 },
  { serviceName: "Amazon Redshift", total: 1201, sharePct: 6.2, delta: 20.4, deltaPct: 1.7 },
  { serviceName: "AmazonCloudWatch", total: 752.02, sharePct: 3.9, delta: -9.3, deltaPct: -1.2 },
  { serviceName: "Amazon Elastic Load Balancing", total: 558.14, sharePct: 2.9, delta: -12.2, deltaPct: -2.1 },
  { serviceName: "Amazon Cognito", total: 401.56, sharePct: 2.1, delta: -8.1, deltaPct: -2.0 },
  { serviceName: "Others", total: 1234.83, sharePct: 6.4, delta: 33.0, deltaPct: 2.7 },
];

export const mockTopAccounts: TopAccountsResponse = [
  { linkedAccount: "Algar Telecom", total: 8761.99, sharePct: 45.4, delta: 510, deltaPct: 6.4 },
  { linkedAccount: "AlgarAppPRD", total: 2825.15, sharePct: 14.6, delta: -120, deltaPct: -3.2 },
  { linkedAccount: "Estacao de Experiencias Digitais", total: 2400.02, sharePct: 12.4, delta: 80, deltaPct: 2.3 },
  { linkedAccount: "poc-aiops", total: 1597.15, sharePct: 8.3, delta: 44, deltaPct: 2.9 },
  { linkedAccount: "AlgarAppHOM", total: 1327.47, sharePct: 6.9, delta: -13.5, deltaPct: -1.0 },
  { linkedAccount: "AlgarDataLakeDev", total: 860.51, sharePct: 4.5, delta: 10.1, deltaPct: 1.2 },
  { linkedAccount: "AlgarAppDEV", total: 701.01, sharePct: 3.6, delta: -9.7, deltaPct: -1.4 },
  { linkedAccount: "Gestao de Marketplace DEV", total: 675.49, sharePct: 3.5, delta: 7.2, deltaPct: 1.1 },
  { linkedAccount: "Algar Brain VM", total: 111.84, sharePct: 0.6, delta: -2.1, deltaPct: -1.9 },
  { linkedAccount: "Algar Security", total: 31.38, sharePct: 0.2, delta: -3.2, deltaPct: -9.1 },
];

export const mockFilters: FiltersResponse = {
  services: ["AWS Amplify", "AWS CloudTrail", "AWS CodeArtifact", "AWS Glue", "Amazon RDS", "Amazon S3", "Amazon EC2"],
  accounts: ["Algar Brain VM", "Algar Security", "Algar Telecom", "AlgarAPPDEV", "AlgarAppPRD", "poc-aiops"],
};

export const mockAiInsight: AiInsightResponse = {
  answerMarkdown:
    "O custo semanal está concentrado em computação e banco de dados. O pico ocorreu em 21/02/2026 e está associado ao aumento de EC2 e RDS.",
  highlights: [
    "EC2 representa a maior parcela do custo no período.",
    "RDS manteve tendência de alta em 3 dias consecutivos.",
    "A conta Algar Telecom concentra mais de 40% do custo semanal.",
  ],
  suggestedActions: [
    "Revisar instâncias EC2 com baixa utilização e aplicar rightsizing.",
    "Habilitar policies de lifecycle para dados de S3 frios.",
    "Avaliar reserva/savings plans para workloads estáveis.",
  ],
};

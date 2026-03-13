export const SEGMENTS = ['', 'signal_strata', 'consulting', 'pe', 'other'] as const;
export const ENGAGEMENT_STAGES = ['new', 'nurturing', 'active', 'client', 'churned'] as const;
export const INBOUND_CHANNELS = ['', 'linkedin', 'referral', 'conference', 'cold_outbound', 'website', 'other'] as const;

export const CURRENCIES = ['GBP', 'USD', 'EUR'] as const;

export const CURRENCY_SYMBOLS: Record<string, string> = {
  GBP: '£',
  USD: '$',
  EUR: '€',
};

export function formatCurrency(value: number | string, currency?: string): string {
  const num = Number(value || 0);
  const symbol = CURRENCY_SYMBOLS[currency || 'GBP'] || currency || '£';
  return `${symbol}${num.toLocaleString()}`;
}

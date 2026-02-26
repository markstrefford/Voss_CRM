export interface Contact {
  id: string;
  company_id: string;
  first_name: string;
  last_name: string;
  email: string;
  phone: string;
  role: string;
  linkedin_url: string;
  urls: string;
  source: string;
  referral_contact_id: string;
  tags: string;
  notes: string;
  status: string;
  segment: string;
  engagement_stage: string;
  inbound_channel: string;
  do_not_contact: string;
  campaign_id: string;
  created_at: string;
  updated_at: string;
}

export interface Company {
  id: string;
  name: string;
  industry: string;
  website: string;
  size: string;
  notes: string;
  created_at: string;
  updated_at: string;
  contacts?: Contact[];
}

export interface Deal {
  id: string;
  contact_id: string;
  company_id: string;
  title: string;
  stage: DealStage;
  value: string;
  currency: string;
  priority: string;
  expected_close: string;
  notes: string;
  created_at: string;
  updated_at: string;
}

export type DealStage = 'lead' | 'prospect' | 'qualified' | 'proposal' | 'negotiation' | 'won' | 'lost';

export const DEAL_STAGES: DealStage[] = ['lead', 'prospect', 'qualified', 'proposal', 'negotiation', 'won', 'lost'];

export interface Interaction {
  id: string;
  contact_id: string;
  deal_id: string;
  type: string;
  subject: string;
  body: string;
  url: string;
  direction: string;
  occurred_at: string;
  created_at: string;
}

export interface FollowUp {
  id: string;
  contact_id: string;
  deal_id: string;
  title: string;
  due_date: string;
  due_time: string;
  status: string;
  reminder_sent: string;
  notes: string;
  created_at: string;
  completed_at: string;
}

export interface User {
  id: string;
  username: string;
  telegram_chat_id: string;
  created_at: string;
}

export interface DashboardSummary {
  pipeline: Record<string, { count: number; value: number }>;
  overdue_count: number;
  overdue_follow_ups: FollowUp[];
  todays_follow_ups: FollowUp[];
  recent_activity_count: number;
  total_deals: number;
  total_deal_value: number;
}

export interface EmailDraft {
  subject: string;
  body: string;
}

// Action Feed (Smart Queues Dashboard)
export interface ActionFeedFollowUpItem {
  id: string;
  contact_id: string;
  contact_name: string;
  company_name: string;
  title: string;
  due_date: string;
  due_time: string;
}

export interface ActionFeedContactItem {
  id: string;
  name: string;
  company_name: string;
  role: string;
  engagement_stage: string;
  last_interaction_date: string;
  reason: string;
}

export interface ActionFeedDealItem {
  id: string;
  title: string;
  contact_name: string;
  company_name: string;
  stage: string;
  value: number;
  days_stale: number;
}

export interface ActionFeedStats {
  total_active_contacts: number;
  in_conversation: number;
  follow_ups_this_week: number;
  deals_in_pipeline: number;
  pipeline_value: number;
}

export interface ActionFeed {
  stats: ActionFeedStats;
  action_required: {
    overdue_follow_ups: ActionFeedFollowUpItem[];
    due_today: ActionFeedFollowUpItem[];
    overdue_total: number;
    due_today_total: number;
  };
  momentum: {
    inbound_recent: ActionFeedContactItem[];
    no_follow_up_scheduled: ActionFeedContactItem[];
    inbound_recent_total: number;
    no_follow_up_scheduled_total: number;
  };
  at_risk: {
    going_cold: ActionFeedContactItem[];
    stale_deals: ActionFeedDealItem[];
    going_cold_total: number;
    stale_deals_total: number;
  };
  ready_to_reach_out: {
    new_contacts: ActionFeedContactItem[];
    new_contacts_total: number;
  };
}

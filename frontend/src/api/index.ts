import api from './client';
import type { Contact, Company, Deal, DashboardSummary, EmailDraft, FollowUp, Interaction } from '@/types';

// Auth
export const login = (username: string, password: string) =>
  api.post<{ access_token: string }>('/api/auth/login', { username, password });

export const register = (username: string, password: string, invite_code: string) =>
  api.post<{ access_token: string }>('/api/auth/register', { username, password, invite_code });

export const getMe = () =>
  api.get('/api/auth/me');

// Contacts
export const getContacts = (params?: Record<string, string>) =>
  api.get<Contact[]>('/api/contacts', { params });

export const getContact = (id: string) =>
  api.get<Contact>(`/api/contacts/${id}`);

export const createContact = (data: Partial<Contact>) =>
  api.post<Contact>('/api/contacts', data);

export const updateContact = (id: string, data: Partial<Contact>) =>
  api.put<Contact>(`/api/contacts/${id}`, data);

export const deleteContact = (id: string) =>
  api.delete(`/api/contacts/${id}`);

// Companies
export const getCompanies = () =>
  api.get<Company[]>('/api/companies');

export const getCompany = (id: string) =>
  api.get<Company & { contacts: Contact[] }>(`/api/companies/${id}`);

export const createCompany = (data: Partial<Company>) =>
  api.post<Company>('/api/companies', data);

export const updateCompany = (id: string, data: Partial<Company>) =>
  api.put<Company>(`/api/companies/${id}`, data);

// Deals
export const getDeals = (params?: Record<string, string>) =>
  api.get<Deal[]>('/api/deals', { params });

export const getDeal = (id: string) =>
  api.get<Deal>(`/api/deals/${id}`);

export const createDeal = (data: Partial<Deal>) =>
  api.post<Deal>('/api/deals', data);

export const updateDeal = (id: string, data: Partial<Deal>) =>
  api.put<Deal>(`/api/deals/${id}`, data);

export const updateDealStage = (id: string, stage: string) =>
  api.patch<Deal>(`/api/deals/${id}/stage`, { stage });

// Interactions
export const getInteractions = (params?: Record<string, string>) =>
  api.get<Interaction[]>('/api/interactions', { params });

export const createInteraction = (data: Partial<Interaction>) =>
  api.post<Interaction>('/api/interactions', data);

export const updateInteraction = (id: string, data: Partial<Interaction>) =>
  api.put<Interaction>(`/api/interactions/${id}`, data);

// Follow-Ups
export const getFollowUps = (params?: Record<string, string>) =>
  api.get<FollowUp[]>('/api/follow-ups', { params });

export const createFollowUp = (data: Partial<FollowUp>) =>
  api.post<FollowUp>('/api/follow-ups', data);

export const completeFollowUp = (id: string) =>
  api.patch<FollowUp>(`/api/follow-ups/${id}/complete`);

export const snoozeFollowUp = (id: string, due_date: string, due_time?: string) =>
  api.patch<FollowUp>(`/api/follow-ups/${id}/snooze`, { due_date, due_time: due_time || '' });

// Dashboard
export const getDashboardSummary = () =>
  api.get<DashboardSummary>('/api/dashboard/summary');

export const getStalDeals = () =>
  api.get<{ stale_deals: Deal[]; count: number }>('/api/dashboard/stale-deals');

// Email
export const generateEmailDraft = (data: { contact_id: string; deal_id?: string; intent: string; tone: string }) =>
  api.post<EmailDraft>('/api/email/draft', data);

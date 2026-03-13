import { useEffect, useState } from 'react';
import { createDeal, updateDeal } from '@/api';
import type { Deal, DealStage, Contact, Company } from '@/types';
import { DEAL_STAGES } from '@/types';
import { Button } from '@/components/ui/button';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';

const CURRENCIES = ['GBP', 'USD', 'EUR'];

type DealFormData = { title: string; value: string; currency: string; stage: DealStage; priority: string; expected_close: string; notes: string; contact_id: string; company_id: string };

const emptyForm: DealFormData = { title: '', value: '', currency: 'GBP', stage: 'lead', priority: 'medium', expected_close: '', notes: '', contact_id: '', company_id: '' };

export function DealFormDialog({ open, onOpenChange, onSaved, deal, contacts, companies, defaultStage }: {
  open: boolean;
  onOpenChange: (v: boolean) => void;
  onSaved: () => void;
  deal?: Deal;
  contacts: Contact[];
  companies: Company[];
  defaultStage?: DealStage;
}) {
  const [form, setForm] = useState<DealFormData>(emptyForm);
  const [saving, setSaving] = useState(false);
  const isEdit = !!deal;

  useEffect(() => {
    if (deal) {
      setForm({
        title: deal.title || '',
        value: deal.value || '',
        currency: deal.currency || 'GBP',
        stage: deal.stage || 'lead',
        priority: deal.priority || 'medium',
        expected_close: deal.expected_close || '',
        notes: deal.notes || '',
        contact_id: deal.contact_id || '',
        company_id: deal.company_id || '',
      });
    } else {
      setForm({ ...emptyForm, stage: defaultStage || 'lead' });
    }
  }, [deal, defaultStage]);

  const handleSubmit = async () => {
    setSaving(true);
    try {
      if (isEdit) {
        await updateDeal(deal.id, form);
      } else {
        await createDeal(form);
      }
      onOpenChange(false);
      setForm(emptyForm);
      onSaved();
    } finally {
      setSaving(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader><DialogTitle>{isEdit ? 'Edit Deal' : 'New Deal'}</DialogTitle></DialogHeader>
        <div className="space-y-4">
          <div className="space-y-2"><Label>Title *</Label><Input value={form.title} onChange={e => setForm(f => ({ ...f, title: e.target.value }))} /></div>
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label>Contact</Label>
              <Select value={form.contact_id} onValueChange={v => setForm(f => ({ ...f, contact_id: v === '_none' ? '' : v }))}>
                <SelectTrigger><SelectValue placeholder="Select contact" /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="_none">None</SelectItem>
                  {contacts.map(c => <SelectItem key={c.id} value={c.id}>{c.first_name} {c.last_name}</SelectItem>)}
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-2">
              <Label>Company</Label>
              <Select value={form.company_id} onValueChange={v => setForm(f => ({ ...f, company_id: v === '_none' ? '' : v }))}>
                <SelectTrigger><SelectValue placeholder="Select company" /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="_none">None</SelectItem>
                  {companies.map(c => <SelectItem key={c.id} value={c.id}>{c.name}</SelectItem>)}
                </SelectContent>
              </Select>
            </div>
          </div>
          <div className="grid grid-cols-3 gap-4">
            <div className="space-y-2"><Label>Value</Label><Input type="number" value={form.value} onChange={e => setForm(f => ({ ...f, value: e.target.value }))} /></div>
            <div className="space-y-2">
              <Label>Currency</Label>
              <Select value={form.currency} onValueChange={v => setForm(f => ({ ...f, currency: v }))}>
                <SelectTrigger><SelectValue /></SelectTrigger>
                <SelectContent>{CURRENCIES.map(c => <SelectItem key={c} value={c}>{c}</SelectItem>)}</SelectContent>
              </Select>
            </div>
            <div className="space-y-2">
              <Label>Stage</Label>
              <Select value={form.stage} onValueChange={v => setForm(f => ({ ...f, stage: v as DealStage }))}>
                <SelectTrigger><SelectValue /></SelectTrigger>
                <SelectContent>{DEAL_STAGES.map(s => <SelectItem key={s} value={s}>{s}</SelectItem>)}</SelectContent>
              </Select>
            </div>
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label>Priority</Label>
              <Select value={form.priority} onValueChange={v => setForm(f => ({ ...f, priority: v }))}>
                <SelectTrigger><SelectValue /></SelectTrigger>
                <SelectContent>{['low', 'medium', 'high'].map(p => <SelectItem key={p} value={p}>{p}</SelectItem>)}</SelectContent>
              </Select>
            </div>
            <div className="space-y-2"><Label>Expected Close</Label><Input type="date" value={form.expected_close} onChange={e => setForm(f => ({ ...f, expected_close: e.target.value }))} /></div>
          </div>
          <div className="space-y-2"><Label>Notes</Label><Textarea value={form.notes} onChange={e => setForm(f => ({ ...f, notes: e.target.value }))} /></div>
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>Cancel</Button>
          <Button onClick={handleSubmit} disabled={saving || !form.title}>{isEdit ? 'Update' : 'Save'}</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

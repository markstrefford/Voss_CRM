import { useEffect, useState } from 'react';
import { getDeals, createDeal } from '@/api';
import type { Deal, DealStage } from '@/types';
import { DEAL_STAGES } from '@/types';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Plus, DollarSign } from 'lucide-react';

const stageBadgeColors: Record<string, string> = {
  lead: 'bg-gray-100 text-gray-800',
  prospect: 'bg-blue-100 text-blue-800',
  qualified: 'bg-indigo-100 text-indigo-800',
  proposal: 'bg-purple-100 text-purple-800',
  negotiation: 'bg-orange-100 text-orange-800',
  won: 'bg-green-100 text-green-800',
  lost: 'bg-red-100 text-red-800',
};

export function DealsPage() {
  const [deals, setDeals] = useState<Deal[]>([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);

  const load = () => {
    getDeals().then(res => setDeals(res.data)).finally(() => setLoading(false));
  };

  useEffect(() => { load(); }, []);

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Deals</h1>
        <Button onClick={() => setShowForm(true)}><Plus className="h-4 w-4 mr-1" /> Add</Button>
      </div>

      {loading ? (
        <div className="text-center py-8">Loading...</div>
      ) : deals.length === 0 ? (
        <div className="text-center py-8 text-muted-foreground">No deals yet</div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {deals.map(d => (
            <Card key={d.id}>
              <CardContent className="pt-4">
                <div className="flex justify-between items-start">
                  <div>
                    <p className="font-semibold">{d.title}</p>
                    <div className="flex items-center gap-1 mt-1 text-lg">
                      <DollarSign className="h-4 w-4" />
                      {Number(d.value || 0).toLocaleString()} {d.currency}
                    </div>
                  </div>
                  <span className={`text-xs px-2 py-1 rounded-full font-medium ${stageBadgeColors[d.stage] || ''}`}>
                    {d.stage}
                  </span>
                </div>
                <div className="flex items-center gap-2 mt-3">
                  <Badge variant={d.priority === 'high' ? 'destructive' : 'secondary'}>{d.priority}</Badge>
                  {d.expected_close && <span className="text-xs text-muted-foreground">Close: {d.expected_close}</span>}
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      <DealFormDialog open={showForm} onOpenChange={setShowForm} onSaved={load} />
    </div>
  );
}

function DealFormDialog({ open, onOpenChange, onSaved }: { open: boolean; onOpenChange: (v: boolean) => void; onSaved: () => void }) {
  const [form, setForm] = useState<{ title: string; value: string; currency: string; stage: DealStage; priority: string; expected_close: string; notes: string }>({ title: '', value: '', currency: 'USD', stage: 'lead', priority: 'medium', expected_close: '', notes: '' });
  const [saving, setSaving] = useState(false);

  const handleSubmit = async () => {
    setSaving(true);
    try {
      await createDeal(form);
      onOpenChange(false);
      setForm({ title: '', value: '', currency: 'USD', stage: 'lead', priority: 'medium', expected_close: '', notes: '' });
      onSaved();
    } finally {
      setSaving(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader><DialogTitle>New Deal</DialogTitle></DialogHeader>
        <div className="space-y-4">
          <div className="space-y-2"><Label>Title *</Label><Input value={form.title} onChange={e => setForm(f => ({ ...f, title: e.target.value }))} /></div>
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2"><Label>Value</Label><Input type="number" value={form.value} onChange={e => setForm(f => ({ ...f, value: e.target.value }))} /></div>
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
          <Button onClick={handleSubmit} disabled={saving || !form.title}>Save</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

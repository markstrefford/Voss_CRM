import { useEffect, useState } from 'react';
import { getFollowUps, createFollowUp, completeFollowUp, snoozeFollowUp } from '@/api';
import type { FollowUp } from '@/types';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Plus, Check, Clock, CalendarPlus } from 'lucide-react';

export function FollowUpsPage() {
  const [followUps, setFollowUps] = useState<FollowUp[]>([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [snoozeId, setSnoozeId] = useState<string | null>(null);
  const [snoozeDate, setSnoozeDate] = useState('');

  const load = () => {
    getFollowUps().then(res => setFollowUps(res.data)).finally(() => setLoading(false));
  };

  useEffect(() => { load(); }, []);

  const handleComplete = async (id: string) => {
    await completeFollowUp(id);
    load();
  };

  const handleSnooze = async () => {
    if (snoozeId && snoozeDate) {
      await snoozeFollowUp(snoozeId, snoozeDate);
      setSnoozeId(null);
      setSnoozeDate('');
      load();
    }
  };

  const today = new Date().toISOString().split('T')[0];
  const overdue = followUps.filter(f => f.status === 'pending' && f.due_date < today);
  const dueToday = followUps.filter(f => f.status === 'pending' && f.due_date === today);
  const upcoming = followUps.filter(f => f.status === 'pending' && f.due_date > today);
  const completed = followUps.filter(f => f.status === 'completed');

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Follow-ups</h1>
        <Button onClick={() => setShowForm(true)}><Plus className="h-4 w-4 mr-1" /> Add</Button>
      </div>

      {loading ? (
        <div className="text-center py-8">Loading...</div>
      ) : (
        <>
          <FollowUpSection title="Overdue" items={overdue} variant="destructive" onComplete={handleComplete} onSnooze={setSnoozeId} />
          <FollowUpSection title="Due Today" items={dueToday} variant="default" onComplete={handleComplete} onSnooze={setSnoozeId} />
          <FollowUpSection title="Upcoming" items={upcoming} variant="secondary" onComplete={handleComplete} onSnooze={setSnoozeId} />
          <FollowUpSection title="Completed" items={completed.slice(0, 10)} variant="outline" onComplete={handleComplete} onSnooze={setSnoozeId} />
        </>
      )}

      <FollowUpFormDialog open={showForm} onOpenChange={setShowForm} onSaved={load} />

      <Dialog open={!!snoozeId} onOpenChange={() => setSnoozeId(null)}>
        <DialogContent>
          <DialogHeader><DialogTitle>Snooze Follow-up</DialogTitle></DialogHeader>
          <div className="space-y-2">
            <Label>New Due Date</Label>
            <Input type="date" value={snoozeDate} onChange={e => setSnoozeDate(e.target.value)} />
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setSnoozeId(null)}>Cancel</Button>
            <Button onClick={handleSnooze} disabled={!snoozeDate}>Snooze</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}

function FollowUpSection({ title, items, variant, onComplete, onSnooze }: {
  title: string;
  items: FollowUp[];
  variant: 'default' | 'destructive' | 'secondary' | 'outline';
  onComplete: (id: string) => void;
  onSnooze: (id: string) => void;
}) {
  if (items.length === 0) return null;

  return (
    <div className="space-y-2">
      <h2 className="text-lg font-semibold flex items-center gap-2">
        {title} <Badge variant={variant}>{items.length}</Badge>
      </h2>
      <div className="space-y-2">
        {items.map(f => (
          <Card key={f.id}>
            <CardContent className="pt-4 flex items-center justify-between">
              <div>
                <p className="font-medium">{f.title}</p>
                <div className="flex items-center gap-2 text-sm text-muted-foreground mt-1">
                  <Clock className="h-3 w-3" />
                  {f.due_date} {f.due_time && `at ${f.due_time}`}
                </div>
                {f.notes && <p className="text-sm text-muted-foreground mt-1">{f.notes}</p>}
              </div>
              {f.status !== 'completed' && (
                <div className="flex gap-1">
                  <Button variant="ghost" size="icon" title="Complete" onClick={() => onComplete(f.id)}>
                    <Check className="h-4 w-4 text-green-600" />
                  </Button>
                  <Button variant="ghost" size="icon" title="Snooze" onClick={() => onSnooze(f.id)}>
                    <CalendarPlus className="h-4 w-4" />
                  </Button>
                </div>
              )}
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}

function FollowUpFormDialog({ open, onOpenChange, onSaved }: { open: boolean; onOpenChange: (v: boolean) => void; onSaved: () => void }) {
  const [form, setForm] = useState({ contact_id: '', title: '', due_date: '', due_time: '', notes: '' });
  const [saving, setSaving] = useState(false);

  const handleSubmit = async () => {
    setSaving(true);
    try {
      await createFollowUp(form);
      onOpenChange(false);
      setForm({ contact_id: '', title: '', due_date: '', due_time: '', notes: '' });
      onSaved();
    } finally {
      setSaving(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader><DialogTitle>New Follow-up</DialogTitle></DialogHeader>
        <div className="space-y-4">
          <div className="space-y-2"><Label>Title *</Label><Input value={form.title} onChange={e => setForm(f => ({ ...f, title: e.target.value }))} /></div>
          <div className="space-y-2"><Label>Contact ID *</Label><Input value={form.contact_id} onChange={e => setForm(f => ({ ...f, contact_id: e.target.value }))} placeholder="Contact ID" /></div>
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2"><Label>Due Date *</Label><Input type="date" value={form.due_date} onChange={e => setForm(f => ({ ...f, due_date: e.target.value }))} /></div>
            <div className="space-y-2"><Label>Due Time</Label><Input type="time" value={form.due_time} onChange={e => setForm(f => ({ ...f, due_time: e.target.value }))} /></div>
          </div>
          <div className="space-y-2"><Label>Notes</Label><Textarea value={form.notes} onChange={e => setForm(f => ({ ...f, notes: e.target.value }))} /></div>
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>Cancel</Button>
          <Button onClick={handleSubmit} disabled={saving || !form.title || !form.due_date || !form.contact_id}>Save</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
